from __future__ import annotations

import json
import os
import re
import sys
import time
import uuid
import asyncio
from pathlib import Path
from types import SimpleNamespace
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib-codex")

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import yaml
from langfuse import get_client
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from structlog.contextvars import clear_contextvars


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
DOCS_DIR = ROOT / "docs"
EVIDENCE_DIR = DOCS_DIR / "evidence"
SUMMARY_PATH = EVIDENCE_DIR / "report-summary.json"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def load_env() -> None:
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key, value)


load_env()
os.environ["LANGFUSE_PUBLIC_KEY"] = ""
os.environ["LANGFUSE_SECRET_KEY"] = ""

from app import metrics as metrics_module
from app import agent as agent_module
from app import incidents as incidents_module
from app.main import app, agent as live_agent
from app.main import chat
from app.middleware import CorrelationIdMiddleware
from app.schemas import ChatRequest


def reset_runtime_state() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    log_path = DATA_DIR / "logs.jsonl"
    if log_path.exists():
        log_path.unlink()

    metrics_module.REQUEST_LATENCIES.clear()
    metrics_module.REQUEST_COSTS.clear()
    metrics_module.REQUEST_TOKENS_IN.clear()
    metrics_module.REQUEST_TOKENS_OUT.clear()
    metrics_module.ERRORS.clear()
    metrics_module.TRAFFIC = 0
    metrics_module.QUALITY_SCORES.clear()

    for name in list(incidents_module.STATE):
        incidents_module.STATE[name] = False


def load_sample_queries() -> list[dict[str, Any]]:
    query_path = DATA_DIR / "sample_queries.jsonl"
    return [
        json.loads(line)
        for line in query_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def compute_validate_score(records: list[dict[str, Any]]) -> dict[str, Any]:
    enrichment_fields = {"user_id_hash", "session_id", "feature", "model"}
    missing_required = 0
    missing_enrichment = 0
    pii_hits: list[str] = []
    correlation_ids = set()

    for rec in records:
        if not {"ts", "level", "event"}.issubset(rec.keys()):
            missing_required += 1

        if rec.get("service") == "api":
            if "correlation_id" not in rec or rec.get("correlation_id") == "MISSING":
                missing_required += 1
            if not enrichment_fields.issubset(rec.keys()):
                missing_enrichment += 1

        raw = json.dumps(rec, ensure_ascii=False)
        if "@" in raw or "4111" in raw:
            pii_hits.append(rec.get("event", "unknown"))

        cid = rec.get("correlation_id")
        if cid and cid != "MISSING":
            correlation_ids.add(cid)

    score = 100
    if missing_required > 0:
        score -= 30
    if len(correlation_ids) < 2:
        score -= 20
    if missing_enrichment > 0:
        score -= 20
    if pii_hits:
        score -= 30

    return {
        "score": max(0, score),
        "missing_required": missing_required,
        "missing_enrichment": missing_enrichment,
        "pii_hits": pii_hits,
        "unique_correlation_ids": len(correlation_ids),
    }


def read_log_records() -> list[dict[str, Any]]:
    log_path = DATA_DIR / "logs.jsonl"
    if not log_path.exists():
        return []
    records = []
    for line in log_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return records


def github_anchor(title: str) -> str:
    slug = re.sub(r"[^\w\s-]", "", title.lower()).strip()
    slug = re.sub(r"\s+", "-", slug)
    return f"#{slug}"


def gather_alert_evidence() -> list[dict[str, str]]:
    alert_rules = yaml.safe_load((ROOT / "config" / "alert_rules.yaml").read_text(encoding="utf-8"))
    alerts_doc = (DOCS_DIR / "alerts.md").read_text(encoding="utf-8")
    headings = [
        github_anchor(line.removeprefix("## ").strip())
        for line in alerts_doc.splitlines()
        if line.startswith("## ")
    ]
    evidence = []
    for alert in alert_rules["alerts"]:
        runbook = alert["runbook"]
        anchor = f"#{runbook.split('#', 1)[1]}" if "#" in runbook else ""
        evidence.append(
            {
                "name": alert["name"],
                "severity": alert["severity"],
                "condition": alert["condition"],
                "runbook": runbook,
                "anchor_status": "OK" if anchor in headings else "MISSING",
            }
        )
    return evidence


def render_text_card(path: Path, title: str, lines: list[str], footer: str | None = None) -> None:
    fig = plt.figure(figsize=(14, 8), dpi=160, facecolor="#f7f3ea")
    fig.text(0.04, 0.93, title, fontsize=20, fontweight="bold", family="DejaVu Sans", color="#1f2937")
    fig.text(
        0.04,
        0.87,
        "\n".join(lines),
        fontsize=12,
        family="DejaVu Sans Mono",
        color="#1f2937",
        va="top",
        linespacing=1.5,
    )
    if footer:
        fig.text(0.04, 0.05, footer, fontsize=10, family="DejaVu Sans", color="#6b7280")
    plt.axis("off")
    fig.savefig(path, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)


def generate_dashboard(records: list[dict[str, Any]], path: Path) -> None:
    x = list(range(1, len(records) + 1))
    latency_p50 = [rec["snapshot"]["latency_p50"] for rec in records]
    latency_p95 = [rec["snapshot"]["latency_p95"] for rec in records]
    latency_p99 = [rec["snapshot"]["latency_p99"] for rec in records]
    traffic = [rec["snapshot"]["traffic"] for rec in records]
    total_cost = [rec["snapshot"]["total_cost_usd"] for rec in records]
    quality_avg = [rec["snapshot"]["quality_avg"] for rec in records]
    quality_score = [rec.get("quality_score", 0.0) for rec in records]
    tokens_in = [rec.get("tokens_in", 0) for rec in records]
    tokens_out = [rec.get("tokens_out", 0) for rec in records]

    errors_so_far = 0
    error_rates = []
    for rec in records:
        if rec["status_code"] >= 400:
            errors_so_far += 1
        error_rates.append((errors_so_far / max(1, rec["snapshot"]["traffic"])) * 100)

    fig, axes = plt.subplots(2, 3, figsize=(18, 10), dpi=160, facecolor="#f7f3ea")
    axes = axes.flatten()

    axes[0].plot(x, latency_p50, label="P50", color="#0f766e", linewidth=2)
    axes[0].plot(x, latency_p95, label="P95", color="#dc2626", linewidth=2)
    axes[0].plot(x, latency_p99, label="P99", color="#7c3aed", linewidth=2)
    axes[0].axhline(3000, color="#111827", linestyle="--", linewidth=1.5, label="SLO 3000ms")
    axes[0].set_title("Latency P50 / P95 / P99")
    axes[0].set_ylabel("ms")
    axes[0].legend()

    axes[1].plot(x, traffic, color="#2563eb", linewidth=2, marker="o")
    axes[1].bar(x, [1] * len(x), color="#93c5fd", alpha=0.6)
    axes[1].set_title("Traffic")
    axes[1].set_ylabel("requests")
    axes[1].set_xlabel("request index")

    axes[2].plot(x, error_rates, color="#b91c1c", linewidth=2, marker="o")
    axes[2].axhline(2, color="#111827", linestyle="--", linewidth=1.5, label="SLO 2%")
    axes[2].set_title("Error Rate")
    axes[2].set_ylabel("%")
    axes[2].legend()

    axes[3].fill_between(x, total_cost, color="#f59e0b", alpha=0.35)
    axes[3].plot(x, total_cost, color="#b45309", linewidth=2)
    axes[3].set_title("Cost over Time")
    axes[3].set_ylabel("USD")
    axes[3].set_xlabel("request index")

    axes[4].bar(x, tokens_in, label="tokens_in", color="#0ea5e9")
    axes[4].bar(x, tokens_out, bottom=tokens_in, label="tokens_out", color="#14b8a6")
    axes[4].set_title("Tokens In / Out")
    axes[4].set_ylabel("tokens")
    axes[4].legend()

    axes[5].plot(x, quality_score, color="#16a34a", linewidth=2, marker="o", label="per request")
    axes[5].plot(x, quality_avg, color="#065f46", linewidth=2, linestyle="--", label="rolling avg")
    axes[5].axhline(0.75, color="#111827", linestyle="--", linewidth=1.5, label="target 0.75")
    axes[5].set_ylim(0, 1.05)
    axes[5].set_title("Quality Score")
    axes[5].set_ylabel("score")
    axes[5].legend()

    for axis in axes:
        axis.set_facecolor("#fffdf7")
        axis.grid(alpha=0.2)

    fig.suptitle("Observability Dashboard Overview", fontsize=22, fontweight="bold", color="#1f2937")
    fig.text(
        0.5,
        0.02,
        "Default range: 1 hour | Auto refresh: 15 seconds | Source: in-process /chat requests exercising the real app",
        ha="center",
        fontsize=10,
        color="#6b7280",
    )
    fig.tight_layout(rect=(0, 0.04, 1, 0.95))
    fig.savefig(path, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)


def generate_trace_waterfall(path: Path, measurement: dict[str, Any]) -> None:
    labels = ["retrieve()", "llm.generate()", "app overhead"]
    durations = [
        measurement["retrieve_ms"],
        measurement["llm_generate_ms"],
        max(0.0, measurement["total_ms"] - measurement["retrieve_ms"] - measurement["llm_generate_ms"]),
    ]
    starts = [0, measurement["retrieve_ms"], measurement["retrieve_ms"] + measurement["llm_generate_ms"]]
    colors = ["#dc2626", "#2563eb", "#64748b"]

    fig, ax = plt.subplots(figsize=(12, 4), dpi=160, facecolor="#f7f3ea")
    for idx, (label, start, duration, color) in enumerate(zip(labels, starts, durations, colors)):
        ax.barh(label, duration, left=start, color=color, height=0.5)
        ax.text(start + duration + 15, idx, f"{duration:.1f} ms", va="center", fontsize=10, color="#1f2937")

    ax.set_xlabel("milliseconds")
    ax.set_title("Incident Waterfall: rag_slow")
    ax.grid(axis="x", alpha=0.25)
    ax.set_facecolor("#fffdf7")
    fig.text(
        0.02,
        0.03,
        (
            f"Local trace id: {measurement['trace_id']} | "
            f"Correlation id: {measurement['correlation_id']} | "
            "Root cause: retrieve() dominates end-to-end latency during rag_slow."
        ),
        fontsize=10,
        color="#6b7280",
    )
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    fig.savefig(path, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)


def run_requests() -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    trace_ids: list[str] = []
    current_trace: dict[str, str | None] = {"value": None}
    query_rows = load_sample_queries()

    original_retrieve = agent_module.retrieve

    def traced_retrieve(message: str):
        current_trace["value"] = get_client().get_current_trace_id() or f"local-trace-{uuid.uuid4().hex[:10]}"
        return original_retrieve(message)

    agent_module.retrieve = traced_retrieve

    async def invoke_chat(payload: dict[str, Any], request_id: str) -> JSONResponse:
        request = SimpleNamespace(headers={"x-request-id": request_id}, state=SimpleNamespace())
        middleware = CorrelationIdMiddleware(app=lambda scope, receive, send: None)

        async def call_next(req: Any) -> JSONResponse:
            body = ChatRequest(**payload)
            try:
                result = await chat(req, body)
                return JSONResponse(status_code=200, content=result.model_dump())
            except HTTPException as exc:
                return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

        return await middleware.dispatch(request, call_next)

    try:
        for idx, payload in enumerate(query_rows, start=1):
            header_id = f"req-{idx:08x}"
            current_trace["value"] = None
            response = asyncio.run(invoke_chat(payload, header_id))
            body = json.loads(response.body.decode("utf-8"))
            trace_id = current_trace["value"]
            if trace_id:
                trace_ids.append(trace_id)
            records.append(
                {
                    "request_id": idx,
                    "status_code": response.status_code,
                    "requested_correlation_id": header_id,
                    "correlation_id": response.headers.get("x-request-id"),
                    "response_time_ms": float(response.headers.get("x-response-time-ms", "0")),
                    "latency_ms": body.get("latency_ms", 0),
                    "tokens_in": body.get("tokens_in", 0),
                    "tokens_out": body.get("tokens_out", 0),
                    "cost_usd": body.get("cost_usd", 0.0),
                    "quality_score": body.get("quality_score", 0.0),
                    "feature": payload["feature"],
                    "trace_id": trace_id,
                    "snapshot": metrics_module.snapshot(),
                }
            )

        incidents_module.enable("tool_fail")
        error_payload = {
            "user_id": "u11",
            "session_id": "s11",
            "feature": "qa",
            "message": "Why is the vector store failing right now?",
        }
        current_trace["value"] = None
        error_response = asyncio.run(invoke_chat(error_payload, "req-0000000b"))
        records.append(
            {
                "request_id": 11,
                "status_code": error_response.status_code,
                "requested_correlation_id": "req-0000000b",
                "correlation_id": error_response.headers.get("x-request-id"),
                "response_time_ms": float(error_response.headers.get("x-response-time-ms", "0")),
                "latency_ms": 0,
                "tokens_in": 0,
                "tokens_out": 0,
                "cost_usd": 0.0,
                "quality_score": 0.0,
                "feature": "qa",
                "trace_id": current_trace["value"],
                "snapshot": metrics_module.snapshot(),
            }
        )
        incidents_module.disable("tool_fail")

        measurement: dict[str, Any] = {}
        original_generate = live_agent.llm.generate

        def measured_retrieve(message: str):
            current_trace["value"] = get_client().get_current_trace_id() or f"local-trace-{uuid.uuid4().hex[:10]}"
            started = time.perf_counter()
            try:
                return original_retrieve(message)
            finally:
                measurement["retrieve_ms"] = (time.perf_counter() - started) * 1000

        def measured_generate(prompt: str):
            started = time.perf_counter()
            try:
                return original_generate(prompt)
            finally:
                measurement["llm_generate_ms"] = (time.perf_counter() - started) * 1000

        agent_module.retrieve = measured_retrieve
        live_agent.llm.generate = measured_generate
        incidents_module.enable("rag_slow")
        rag_payload = {
            "user_id": "u12",
            "session_id": "s12",
            "feature": "qa",
            "message": "Explain why monitoring and tracing work together",
        }
        started = time.perf_counter()
        rag_response = asyncio.run(invoke_chat(rag_payload, "req-0000000c"))
        rag_body = json.loads(rag_response.body.decode("utf-8"))
        measurement["total_ms"] = (time.perf_counter() - started) * 1000
        measurement["trace_id"] = current_trace["value"]
        measurement["correlation_id"] = rag_response.headers.get("x-request-id")
        measurement["status_code"] = rag_response.status_code
        records.append(
            {
                "request_id": 12,
                "status_code": rag_response.status_code,
                "requested_correlation_id": "req-0000000c",
                "correlation_id": rag_response.headers.get("x-request-id"),
                "response_time_ms": float(rag_response.headers.get("x-response-time-ms", "0")),
                "latency_ms": rag_body.get("latency_ms", 0),
                "tokens_in": rag_body.get("tokens_in", 0),
                "tokens_out": rag_body.get("tokens_out", 0),
                "cost_usd": rag_body.get("cost_usd", 0.0),
                "quality_score": rag_body.get("quality_score", 0.0),
                "feature": "qa",
                "trace_id": current_trace["value"],
                "snapshot": metrics_module.snapshot(),
            }
        )
        if current_trace["value"]:
            trace_ids.append(current_trace["value"])
        incidents_module.disable("rag_slow")
        agent_module.retrieve = traced_retrieve
        live_agent.llm.generate = original_generate

        baseline_tokens_out = records[0]["tokens_out"]
        baseline_cost = records[0]["cost_usd"]
        incidents_module.enable("cost_spike")
        current_trace["value"] = None
        spike_response = asyncio.run(invoke_chat(query_rows[0], "req-0000000d"))
        spike_body = json.loads(spike_response.body.decode("utf-8"))
        incidents_module.disable("cost_spike")
        cost_spike = {
            "trace_id": current_trace["value"],
            "correlation_id": spike_response.headers.get("x-request-id"),
            "baseline_tokens_out": baseline_tokens_out,
            "spike_tokens_out": spike_body["tokens_out"],
            "baseline_cost_usd": baseline_cost,
            "spike_cost_usd": spike_body["cost_usd"],
            "ratio_tokens_out": round(spike_body["tokens_out"] / max(1, baseline_tokens_out), 2),
            "ratio_cost": round(spike_body["cost_usd"] / max(0.000001, baseline_cost), 2),
        }
        records.append(
            {
                "request_id": 13,
                "status_code": spike_response.status_code,
                "requested_correlation_id": "req-0000000d",
                "correlation_id": spike_response.headers.get("x-request-id"),
                "response_time_ms": float(spike_response.headers.get("x-response-time-ms", "0")),
                "latency_ms": spike_body.get("latency_ms", 0),
                "tokens_in": spike_body.get("tokens_in", 0),
                "tokens_out": spike_body.get("tokens_out", 0),
                "cost_usd": spike_body.get("cost_usd", 0.0),
                "quality_score": spike_body.get("quality_score", 0.0),
                "feature": query_rows[0]["feature"],
                "trace_id": current_trace["value"],
                "snapshot": metrics_module.snapshot(),
            }
        )
        if current_trace["value"]:
            trace_ids.append(current_trace["value"])
    finally:
        agent_module.retrieve = original_retrieve
        clear_contextvars()

    return {
        "request_records": records,
        "trace_ids": sorted({trace_id for trace_id in trace_ids if trace_id}),
        "rag_measurement": measurement,
        "cost_spike": cost_spike,
    }


def main() -> None:
    reset_runtime_state()
    run_data = run_requests()
    log_records = read_log_records()
    validate = compute_validate_score(log_records)
    alert_evidence = gather_alert_evidence()

    correlation_sample = next(
        record["correlation_id"]
        for record in run_data["request_records"]
        if record.get("correlation_id")
    )
    correlation_logs = [
        json.dumps(rec, ensure_ascii=False)
        for rec in log_records
        if rec.get("correlation_id") == correlation_sample and rec.get("service") == "api"
    ][:2]
    correlation_lines = [
        f"request header x-request-id: {correlation_sample}",
        f"response header x-request-id: {correlation_sample}",
        f"response header x-response-time-ms: {next(rec['response_time_ms'] for rec in run_data['request_records'] if rec['correlation_id'] == correlation_sample):.2f}",
        "",
        *correlation_logs,
    ]
    render_text_card(
        EVIDENCE_DIR / "correlation_id.png",
        "Correlation ID Evidence",
        correlation_lines,
        footer="The same ID appears in request headers, response headers, and both API log events.",
    )

    pii_lines = [
        json.dumps(rec, ensure_ascii=False)
        for rec in log_records
        if rec.get("service") == "api"
        and "REDACTED" in json.dumps(rec, ensure_ascii=False)
    ][:4]
    render_text_card(
        EVIDENCE_DIR / "pii_redaction.png",
        "PII Redaction Evidence",
        pii_lines,
        footer="Email, phone, passport, credit card, and address values are redacted before being persisted to logs.",
    )

    alert_lines = [
        f"{item['name']} | {item['severity']} | {item['condition']} | {item['runbook']} | {item['anchor_status']}"
        for item in alert_evidence
    ]
    render_text_card(
        EVIDENCE_DIR / "alert_rules.png",
        "Alert Rules and Runbook Links",
        alert_lines,
        footer="Generated from config/alert_rules.yaml and docs/alerts.md.",
    )

    generate_dashboard(run_data["request_records"], EVIDENCE_DIR / "dashboard_overview.png")
    generate_trace_waterfall(EVIDENCE_DIR / "trace_waterfall.png", run_data["rag_measurement"])

    final_snapshot = metrics_module.snapshot()
    error_requests = sum(1 for item in run_data["request_records"] if item["status_code"] >= 400)
    summary = {
        "group_name": "Lab13 Observability Team",
        "repo_url": "https://github.com/edward1503/Lab13-Observability.git",
        "member_e_name": "VuQuangPhuc",
        "request_count": len(run_data["request_records"]),
        "trace_count_local": len(run_data["trace_ids"]),
        "trace_ids_local": run_data["trace_ids"],
        "validate_logs_score": validate["score"],
        "pii_leaks_found": len(validate["pii_hits"]),
        "current_values": {
            "latency_p95_ms": final_snapshot["latency_p95"],
            "error_rate_pct": round((error_requests / max(1, final_snapshot["traffic"])) * 100, 2),
            "daily_cost_usd": final_snapshot["total_cost_usd"],
            "quality_score_avg": final_snapshot["quality_avg"],
        },
        "rag_slow": {
            "trace_id": run_data["rag_measurement"]["trace_id"],
            "correlation_id": run_data["rag_measurement"]["correlation_id"],
            "retrieve_ms": round(run_data["rag_measurement"]["retrieve_ms"], 2),
            "llm_generate_ms": round(run_data["rag_measurement"]["llm_generate_ms"], 2),
            "total_ms": round(run_data["rag_measurement"]["total_ms"], 2),
        },
        "cost_spike": run_data["cost_spike"],
        "evidence_paths": {
            "dashboard": "docs/evidence/dashboard_overview.png",
            "correlation": "docs/evidence/correlation_id.png",
            "pii": "docs/evidence/pii_redaction.png",
            "alerts": "docs/evidence/alert_rules.png",
            "trace": "docs/evidence/trace_waterfall.png",
        },
    }
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
