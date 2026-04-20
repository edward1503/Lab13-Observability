from __future__ import annotations

import time

from .incidents import STATE

# Knowledge base: Observability Assistant for a production AI platform
KNOWLEDGE_BASE: dict[str, list[str]] = {
    "refund": [
        "Refunds are available within 7 days of purchase with valid proof of purchase.",
        "To request a refund, contact support with your order number and reason for return.",
        "Refunds are processed to the original payment method within 3-5 business days.",
        "Subscription plans are non-refundable after the first 48 hours of activation.",
    ],
    "monitoring": [
        "Metrics detect incidents — they alert you that something is wrong (e.g., latency spike, error rate).",
        "Traces localize incidents — they show exactly which component is slow (RAG, LLM, DB query).",
        "Logs explain root cause — they provide the detailed context needed to understand why a failure occurred.",
        "The three pillars of observability work together: metrics (what), traces (where), logs (why).",
        "Dashboards should show: latency P50/P95/P99, error rate, request volume, cost, and quality score.",
    ],
    "observability": [
        "Observability is the ability to understand a system's internal state from its external outputs.",
        "An observable AI system emits structured logs, distributed traces, and quantitative metrics.",
        "Correlation IDs link all log entries and spans that belong to the same request.",
        "SLOs (Service Level Objectives) define your reliability targets, e.g. P95 latency < 3s.",
        "Without observability, debugging production issues requires guessing — avoid this.",
    ],
    "pii": [
        "PII (Personally Identifiable Information) must never appear in application logs.",
        "PII includes: email addresses, phone numbers, CCCD/national ID, passport numbers, and home addresses.",
        "Replace PII with redaction tokens before logging, e.g., [REDACTED_EMAIL], [REDACTED_PHONE_VN].",
        "Hash user IDs with SHA-256 before logging — this preserves tracking ability without exposing identity.",
        "Credit card numbers, bank accounts, and medical record IDs are also PII and must be scrubbed.",
        "Audit logs that must store PII should be encrypted at rest and access-controlled separately.",
    ],
    "policy": [
        "The logging policy prohibits storing PII, API keys, secrets, or raw user input in application logs.",
        "All log entries must be structured JSON and include: ts, level, service, correlation_id, env.",
        "Sensitive payload fields must be summarized and scrubbed before logging.",
        "Log retention policy: application logs 30 days, audit logs 1 year.",
        "Access to production logs requires manager approval and all access is audited.",
    ],
    "latency": [
        "Tail latency (P95, P99) represents the slowest requests — critical for user experience.",
        "To debug high latency: open your trace waterfall and compare RAG span vs LLM span duration.",
        "If the RAG span is the bottleneck: optimize vector search, add caching, or reduce corpus size.",
        "If the LLM span is the bottleneck: shorten prompts, use a faster model, or apply prompt caching.",
        "Circuit breakers prevent cascading failures when a slow dependency (e.g., vector DB) affects all requests.",
        "Always check if an incident toggle (rag_slow) was accidentally left enabled.",
    ],
    "alert": [
        "Alerts should be symptom-based, not cause-based: 'latency > 5s' not 'CPU > 80%'.",
        "Every alert must link to a runbook — a step-by-step debugging guide for on-call engineers.",
        "P1 alerts require immediate response within 15 minutes; P2 alerts within 1 hour.",
        "Recommended alert thresholds: error_rate > 5% for 5m (P1), latency_p95 > 5s for 30m (P2).",
        "Reduce alert fatigue by grouping related alerts and setting appropriate evaluation windows.",
        "Cost alerts should trigger when hourly spend exceeds 2x the daily baseline.",
    ],
    "debug": [
        "Step 1: Check metrics dashboard for the anomaly — latency, error rate, or cost spike.",
        "Step 2: Open Langfuse traces for the problematic time window, filter by high latency.",
        "Step 3: Identify the slowest span in the trace waterfall — that is your bottleneck.",
        "Step 4: Grep logs by the correlation_id from the slow trace to find detailed error context.",
        "Step 5: Check if an incident toggle (rag_slow, cost_spike, tool_fail) was accidentally enabled.",
        "Step 6: Compare before/after metrics if a recent deployment may have caused regression.",
    ],
    "logging": [
        "Use structured logging (JSON) in production — never plain text log messages.",
        "Every log entry must include: timestamp (ts), level, service name, and correlation_id.",
        "Bind request context at the start of each request: user_id_hash, session_id, feature, model.",
        "Log at appropriate levels: INFO for normal flow, WARNING for degraded state, ERROR for failures.",
        "Never log raw user input without scrubbing it first for PII.",
        "Avoid logging in tight loops — aggregate and emit summaries instead.",
    ],
    "workflow": [
        "Observability workflow: Instrument code → Collect signals → Store → Visualize → Alert → Respond.",
        "Instrumentation adds hooks to your code using libraries like structlog, OpenTelemetry, or Langfuse.",
        "Signal collection aggregates data into time-series storage (Prometheus, ClickHouse, Langfuse).",
        "Dashboards visualize metrics for ongoing monitoring (Grafana, Metabase, or custom scripts).",
        "On-call engineers respond to alerts using runbooks to diagnose and restore service quickly.",
    ],
    "slo": [
        "SLI (Service Level Indicator) is the measurement: P95 latency value, error count, uptime seconds.",
        "SLO (Service Level Objective) is the target: P95 < 3s, error rate < 2%, availability > 99.9%.",
        "SLA (Service Level Agreement) is the contractual promise to customers, with penalties for breach.",
        "Error budget = 1 - SLO. If SLO is 99%, you have a 1% error budget to spend on incidents.",
        "Burn rate alerts fire when you are consuming error budget faster than the target rate.",
    ],
    "cost": [
        "Track token usage per request: tokens_in, tokens_out, and estimated cost_usd.",
        "Cost spikes usually indicate: prompt length regression, accidental model upgrade, or abuse.",
        "Use cost dashboards to monitor: daily spend trend, cost per feature, cost per user segment.",
        "To reduce cost: apply prompt caching, shorten context, or route simple requests to cheaper models.",
        "Set a cost_budget_spike alert when hourly_cost > 2x baseline for 15 consecutive minutes.",
    ],
}

# Keyword → topic mapping for multi-topic queries
_KEYWORD_MAP: dict[str, str] = {
    "refund": "refund",
    "monitoring": "monitoring", "metric": "monitoring", "trace": "monitoring", "dashboard": "monitoring",
    "observ": "observability", "correlation": "observability",
    "pii": "pii", "personal": "pii", "email": "pii", "phone": "pii",
    "cccd": "pii", "passport": "pii", "credit": "pii", "sensitive": "pii",
    "policy": "policy", "rule": "policy", "compliance": "policy",
    "latenc": "latency", "slow": "latency", "p95": "latency", "p99": "latency",
    "tail": "latency", "bottleneck": "latency",
    "alert": "alert", "alarm": "alert", "runbook": "alert",
    "debug": "debug", "troubleshoot": "debug", "diagnos": "debug",
    "log": "logging", "structlog": "logging", "json log": "logging",
    "workflow": "workflow", "pipeline": "workflow", "process": "workflow",
    "slo": "slo", "sli": "slo", "error budget": "slo", "objective": "slo",
    "cost": "cost", "token": "cost", "budget": "cost", "expensive": "cost",
}


def retrieve(message: str) -> list[str]:
    """Keyword-based retrieval from the observability knowledge base."""
    if STATE["tool_fail"]:
        raise RuntimeError("Vector store timeout")
    if STATE["rag_slow"]:
        time.sleep(2.5)

    lowered = message.lower()
    matched_topics: list[str] = []

    for keyword, topic in _KEYWORD_MAP.items():
        if keyword in lowered and topic not in matched_topics:
            matched_topics.append(topic)

    docs: list[str] = []
    seen: set[str] = set()

    for topic in matched_topics:
        for doc in KNOWLEDGE_BASE.get(topic, [])[:2]:
            if doc not in seen:
                seen.add(doc)
                docs.append(doc)

    return docs[:5] if docs else [
        "This Observability Assistant covers: metrics, traces, logs, PII scrubbing, SLOs, and alerting.",
        "No specific document matched. Answer from general observability best practices.",
    ]
