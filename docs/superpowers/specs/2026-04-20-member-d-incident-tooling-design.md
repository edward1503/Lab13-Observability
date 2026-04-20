# Member D Incident Tooling Design

## Goal

Make the Member D workflow easy to run and easy to explain during the lab demo:

1. Configure Langfuse credentials locally in `.env`.
2. Generate at least 10 `/chat` requests.
3. Inject `rag_slow` and `cost_spike` incidents.
4. Compare baseline versus incident behavior from terminal output and Langfuse traces.
5. Record Trace IDs, screenshots, and root cause notes in a submission-ready evidence document.

Secrets stay local. The repository should not commit real Langfuse keys.

## Scope

Change only Member D-owned files plus focused tests and docs:

- `scripts/load_test.py`
- `scripts/inject_incident.py`
- `docs/incident-response-summary.md`
- `tests/test_member_d_tooling.py`

Keep these files read-only:

- `app/tracing.py`
- `app/agent.py`

## Approach

### Load Test Script

Enhance `scripts/load_test.py` so it remains simple but produces demo-friendly evidence:

- Add `--num-requests` to repeat sample payloads when more traffic is needed.
- Keep `--concurrency` for parallel requests.
- Capture response status, correlation ID, feature, latency, token usage, and cost.
- Print one line per request for live demo visibility.
- Print a final summary with completed, failed, average latency, p95 latency, token totals, and total cost.
- Exit non-zero when successful requests are fewer than requested, so failures are visible in CI or terminal demos.

### Incident Script

Keep `scripts/inject_incident.py` focused on app incident controls:

- Support enable/disable using the existing `--disable` flag.
- Add `--status` to show active incident state without changing it.
- Keep allowed scenarios aligned with the app: `rag_slow`, `cost_spike`, and `tool_fail`.

No `error_simulation` alias in this option. The PLAN says "if any" for error injection, and this repo already names the error scenario `tool_fail`.

### Evidence Document

Add `docs/incident-response-summary.md` with:

- Exact run commands.
- A safe note that `.env` must be populated locally and not committed.
- Fill-in fields for Langfuse trace count, Trace IDs, screenshot paths, and root causes.
- A short explanation for `rag_slow` and `cost_spike` that matches the code behavior.

## Testing

Add focused unit tests that do not require a running FastAPI server:

- Summary calculations for successful and failed load-test results.
- Request payload expansion for `--num-requests`.
- Scenario validation for `inject_incident.py`.

Manual verification still requires:

- `uvicorn app.main:app --reload`
- `python scripts/load_test.py --concurrency 5`
- Langfuse dashboard screenshots after real credentials are configured.

## Presentation Narrative

The demo explanation should be:

"Member D does not change the agent or tracing implementation. I configure Langfuse locally, use the load-test script to produce at least 10 requests, then enable one incident at a time. For `rag_slow`, traces show request latency increases because retrieval sleeps. For `cost_spike`, response token usage and cost increase because the fake LLM multiplies output tokens. I record the Trace ID, screenshot, and root cause in the incident response summary."

## Acceptance Criteria

- `python scripts/load_test.py --concurrency 5` still works with the default 10 sample queries.
- `python scripts/load_test.py --concurrency 5 --num-requests 20` sends 20 requests by cycling sample payloads.
- Load-test output includes a final summary suitable for screenshots or copy/paste evidence.
- `python scripts/inject_incident.py --scenario rag_slow`, `--disable`, and `--status` work against a running app.
- Tests pass without requiring Langfuse credentials or a running server.
- No real `.env` secrets are committed.
