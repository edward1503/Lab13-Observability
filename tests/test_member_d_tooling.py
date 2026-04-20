from scripts.load_test import RequestResult, build_parser, expand_payloads, summarize_results
from scripts.inject_incident import (
    build_incident_path,
    build_parser as build_incident_parser,
)


def test_expand_payloads_cycles_sample_queries_to_requested_count() -> None:
    payloads = [{"message": "one"}, {"message": "two"}]

    expanded = expand_payloads(payloads, 5)

    assert expanded == [
        {"message": "one"},
        {"message": "two"},
        {"message": "one"},
        {"message": "two"},
        {"message": "one"},
    ]


def test_summarize_results_counts_successes_failures_and_totals() -> None:
    results = [
        RequestResult(200, "req-a", "qa", 100.0, 10, 20, 0.001, None),
        RequestResult(500, None, "qa", 250.0, 0, 0, 0.0, "InternalServerError"),
        RequestResult(200, "req-b", "summary", 300.0, 30, 40, 0.003, None),
    ]

    summary = summarize_results(results, requested=3)

    assert summary["requested"] == 3
    assert summary["completed"] == 2
    assert summary["failed"] == 1
    assert summary["avg_latency_ms"] == 200.0
    assert summary["p95_latency_ms"] == 300.0
    assert summary["tokens_in_total"] == 40
    assert summary["tokens_out_total"] == 60
    assert summary["total_cost_usd"] == 0.004


def test_load_test_parser_defaults_to_ten_requests_and_single_concurrency() -> None:
    args = build_parser().parse_args([])

    assert args.num_requests == 10
    assert args.concurrency == 1


def test_inject_incident_builds_enable_disable_and_status_paths() -> None:
    assert build_incident_path("rag_slow", disable=False, status=False) == "/incidents/rag_slow/enable"
    assert build_incident_path("rag_slow", disable=True, status=False) == "/incidents/rag_slow/disable"
    assert build_incident_path("rag_slow", disable=False, status=True) == "/health"


def test_inject_incident_parser_accepts_status_without_scenario() -> None:
    args = build_incident_parser().parse_args(["--status"])

    assert args.status is True
    assert args.scenario is None
