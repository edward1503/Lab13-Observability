# Member D Incident Tooling Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Member D's load-test and incident-debugging workflow produce clear terminal evidence and a submission-ready incident summary.

**Architecture:** Keep app tracing and agent logic unchanged. Refactor `scripts/load_test.py` into small importable helpers for payload expansion, request results, and summary calculation, then add a lightweight status mode to `scripts/inject_incident.py`. Add docs that tell students where to paste Langfuse Trace IDs and screenshot paths.

**Tech Stack:** Python 3, argparse, concurrent.futures, httpx, pytest.

---

### Task 1: Load-Test Summary Helpers

**Files:**
- Modify: `scripts/load_test.py`
- Create: `tests/test_member_d_tooling.py`

- [ ] **Step 1: Write failing tests for request expansion and summary**

```python
from scripts.load_test import RequestResult, expand_payloads, summarize_results


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
```

- [ ] **Step 2: Run tests and verify they fail**

Run: `pytest tests/test_member_d_tooling.py -v`

Expected: FAIL because `RequestResult`, `expand_payloads`, and `summarize_results` do not exist.

- [ ] **Step 3: Implement minimal load-test helpers**

Add `RequestResult`, `expand_payloads`, `_percentile`, and `summarize_results` to `scripts/load_test.py`.

- [ ] **Step 4: Run tests and verify they pass**

Run: `pytest tests/test_member_d_tooling.py -v`

Expected: PASS.

### Task 2: Load-Test CLI Evidence Output

**Files:**
- Modify: `scripts/load_test.py`
- Modify: `tests/test_member_d_tooling.py`

- [ ] **Step 1: Write failing tests for CLI defaults**

```python
from scripts.load_test import build_parser


def test_load_test_parser_defaults_to_ten_requests_and_single_concurrency() -> None:
    args = build_parser().parse_args([])

    assert args.num_requests == 10
    assert args.concurrency == 1
```

- [ ] **Step 2: Run test and verify it fails**

Run: `pytest tests/test_member_d_tooling.py -v`

Expected: FAIL because `build_parser` does not exist.

- [ ] **Step 3: Implement parser, result printing, summary printing, and exit code**

Update `main()` to use `build_parser()`, call `expand_payloads()`, collect returned `RequestResult` objects, print one line per request, print the summary, and raise `SystemExit(1)` if completed requests are fewer than requested.

- [ ] **Step 4: Run tests and verify they pass**

Run: `pytest tests/test_member_d_tooling.py -v`

Expected: PASS.

### Task 3: Incident Status Mode

**Files:**
- Modify: `scripts/inject_incident.py`
- Modify: `tests/test_member_d_tooling.py`

- [ ] **Step 1: Write failing tests for scenario validation and status path**

```python
from scripts.inject_incident import build_incident_path, build_parser


def test_inject_incident_builds_enable_disable_and_status_paths() -> None:
    assert build_incident_path("rag_slow", disable=False, status=False) == "/incidents/rag_slow/enable"
    assert build_incident_path("rag_slow", disable=True, status=False) == "/incidents/rag_slow/disable"
    assert build_incident_path("rag_slow", disable=False, status=True) == "/health"


def test_inject_incident_parser_accepts_status_without_scenario() -> None:
    args = build_parser().parse_args(["--status"])

    assert args.status is True
    assert args.scenario is None
```

- [ ] **Step 2: Run test and verify it fails**

Run: `pytest tests/test_member_d_tooling.py -v`

Expected: FAIL because helper functions do not exist.

- [ ] **Step 3: Implement incident parser and path helper**

Add `SCENARIOS`, `build_parser()`, and `build_incident_path()` to `scripts/inject_incident.py`. Make `--scenario` required unless `--status` is used.

- [ ] **Step 4: Run tests and verify they pass**

Run: `pytest tests/test_member_d_tooling.py -v`

Expected: PASS.

### Task 4: Incident Evidence Document

**Files:**
- Create: `docs/incident-response-summary.md`

- [ ] **Step 1: Add evidence document**

Create `docs/incident-response-summary.md` with setup commands, run commands, and fill-in sections for `rag_slow` and `cost_spike`.

- [ ] **Step 2: Verify docs mention all required deliverables**

Run: `rg -n "Trace ID|Root Cause|Evidence|rag_slow|cost_spike" docs/incident-response-summary.md`

Expected: Each required deliverable appears.

### Task 5: Final Verification

**Files:**
- Verify all changed files.

- [ ] **Step 1: Run targeted tests**

Run: `pytest tests/test_member_d_tooling.py -v`

Expected: PASS.

- [ ] **Step 2: Run full test suite**

Run: `pytest -v`

Expected: PASS.

- [ ] **Step 3: Check git diff**

Run: `git diff -- scripts/load_test.py scripts/inject_incident.py tests/test_member_d_tooling.py docs/incident-response-summary.md`

Expected: Diff only includes Member D tooling, tests, and docs.
