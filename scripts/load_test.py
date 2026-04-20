from __future__ import annotations

import argparse
import concurrent.futures
import json
import math
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import httpx

BASE_URL = "http://127.0.0.1:8000"
QUERIES = Path("data/sample_queries.jsonl")


@dataclass
class RequestResult:
    status_code: int
    correlation_id: str | None
    feature: str
    latency_ms: float
    tokens_in: int
    tokens_out: int
    cost_usd: float
    error: str | None = None

    @property
    def ok(self) -> bool:
        return 200 <= self.status_code < 300 and self.error is None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--concurrency", type=int, default=1, help="Number of concurrent requests")
    parser.add_argument("--num-requests", type=int, default=10, help="Total requests to send")
    parser.add_argument("--base-url", default=BASE_URL, help="FastAPI base URL")
    parser.add_argument("--timeout", type=float, default=30.0, help="Request timeout in seconds")
    return parser


def load_payloads(path: Path = QUERIES) -> list[dict]:
    lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return [json.loads(line) for line in lines]


def expand_payloads(payloads: list[dict], num_requests: int) -> list[dict]:
    if num_requests < 1:
        raise ValueError("--num-requests must be at least 1")
    if not payloads:
        raise ValueError("No payloads available")
    return [payloads[index % len(payloads)] for index in range(num_requests)]


def _percentile(values: list[float], p: int) -> float:
    if not values:
        return 0.0
    items = sorted(values)
    index = max(0, min(len(items) - 1, math.ceil((p / 100) * len(items)) - 1))
    return round(items[index], 1)


def summarize_results(results: list[RequestResult], requested: int) -> dict[str, float | int]:
    completed = [result for result in results if result.ok]
    latencies = [result.latency_ms for result in completed]
    return {
        "requested": requested,
        "completed": len(completed),
        "failed": requested - len(completed),
        "avg_latency_ms": round(sum(latencies) / len(latencies), 1) if latencies else 0.0,
        "p95_latency_ms": _percentile(latencies, 95),
        "tokens_in_total": sum(result.tokens_in for result in completed),
        "tokens_out_total": sum(result.tokens_out for result in completed),
        "total_cost_usd": round(sum(result.cost_usd for result in completed), 6),
    }


def send_request(client: httpx.Client, payload: dict, base_url: str = BASE_URL) -> RequestResult:
    start = time.perf_counter()
    try:
        r = client.post(f"{base_url}/chat", json=payload)
        latency = (time.perf_counter() - start) * 1000
        body = r.json()
        error = None if 200 <= r.status_code < 300 else str(body.get("detail", r.text))
        return RequestResult(
            status_code=r.status_code,
            correlation_id=body.get("correlation_id"),
            feature=payload.get("feature", "unknown"),
            latency_ms=latency,
            tokens_in=int(body.get("tokens_in", 0)),
            tokens_out=int(body.get("tokens_out", 0)),
            cost_usd=float(body.get("cost_usd", 0.0)),
            error=error,
        )
    except Exception as e:
        latency = (time.perf_counter() - start) * 1000
        return RequestResult(
            status_code=0,
            correlation_id=None,
            feature=payload.get("feature", "unknown"),
            latency_ms=latency,
            tokens_in=0,
            tokens_out=0,
            cost_usd=0.0,
            error=str(e),
        )


def print_result(result: RequestResult) -> None:
    if result.ok:
        print(
            f"[{result.status_code}] {result.correlation_id} | {result.feature} | "
            f"{result.latency_ms:.1f}ms | tokens={result.tokens_in}/{result.tokens_out} | "
            f"cost=${result.cost_usd:.6f}"
        )
        return
    print(
        f"[{result.status_code}] {result.correlation_id or '-'} | {result.feature} | "
        f"{result.latency_ms:.1f}ms | error={result.error}"
    )


def print_summary(summary: dict[str, float | int]) -> None:
    print("\nLoad Test Summary:")
    print(f"- Requested: {summary['requested']}")
    print(f"- Completed: {summary['completed']}")
    print(f"- Failed: {summary['failed']}")
    print(f"- Avg latency: {summary['avg_latency_ms']}ms")
    print(f"- P95 latency: {summary['p95_latency_ms']}ms")
    print(f"- Tokens in/out: {summary['tokens_in_total']}/{summary['tokens_out_total']}")
    print(f"- Total cost_usd: {summary['total_cost_usd']}")


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    payloads = expand_payloads(load_payloads(), args.num_requests)
    results: list[RequestResult] = []

    with httpx.Client(timeout=args.timeout) as client:
        if args.concurrency > 1:
            with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as executor:
                futures = [
                    executor.submit(send_request, client, payload, args.base_url)
                    for payload in payloads
                ]
                for future in concurrent.futures.as_completed(futures):
                    result = future.result()
                    results.append(result)
                    print_result(result)
        else:
            for payload in payloads:
                result = send_request(client, payload, args.base_url)
                results.append(result)
                print_result(result)

    summary = summarize_results(results, requested=len(payloads))
    print_summary(summary)
    if summary["completed"] < summary["requested"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
