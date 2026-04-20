# Incident Response Summary

## Local Setup

Langfuse credentials are configured locally in `.env`. Do not commit real keys.

```bash
cp .env.example .env
# Fill these from https://cloud.langfuse.com:
# LANGFUSE_PUBLIC_KEY=
# LANGFUSE_SECRET_KEY=
```

Start the app:

```bash
uvicorn app.main:app --reload
```

Generate baseline traffic:

```bash
python scripts/load_test.py --concurrency 5
```

Expected terminal evidence:

- `Completed` is at least `10`.
- `Failed` is `0` for a healthy run.
- Langfuse dashboard shows at least `10` traces.

Baseline evidence:

- Local terminal run: `python scripts/load_test.py --concurrency 5`
- Local result: `Completed=10`, `Failed=0`, `Avg latency=736.5ms`, `P95 latency=818.7ms`, `Tokens in/out=340/1336`, `Total cost_usd=0.02106`
- Langfuse tracing status during final local run: `tracing_enabled=true`
- Total traces observed: `30` via Langfuse public API
- Trace list screenshot: `docs/evidence/langfuse_trace_list.png`

## Scenario: rag_slow

Enable the incident:

```bash
python scripts/inject_incident.py --scenario rag_slow
python scripts/load_test.py --concurrency 5
python scripts/inject_incident.py --scenario rag_slow --disable
```

Incident Response Summary:

- Scenario: `rag_slow`
- Trace ID: `9929f3f51815697114ba6c9eedb671e7`
- Root Cause: RAG retrieval is the bottleneck. The `rag_slow` incident adds delay in retrieval, so request latency increased from baseline `P95=818.7ms` to `P95=5337.9ms` in the local evidence run.
- Evidence: `docs/evidence/rag_slow_trace.png`
- Local terminal evidence: `Completed=10`, `Failed=0`, `Avg latency=5328.4ms`, `P95 latency=5337.9ms`, `Tokens in/out=340/1307`, `Total cost_usd=0.020625`
- Langfuse API evidence: trace `9929f3f51815697114ba6c9eedb671e7` has `latency=2.658s`, output `latency_ms=2656`, tags `lab`, `qa`, `claude-sonnet-4-5`.
- Notes: The clean local evidence run used `python scripts/load_test.py --concurrency 2 --timeout 60` because the first `--concurrency 5` incident run produced one local connection reset while still showing the latency spike.

What to say in presentation:

"I enabled `rag_slow`, reran the load test, and opened a slow trace in Langfuse. The waterfall shows the retrieval portion dominates request latency, so the root cause is RAG latency rather than LLM token cost."

## Scenario: cost_spike

Enable the incident:

```bash
python scripts/inject_incident.py --scenario cost_spike
python scripts/load_test.py --concurrency 5
python scripts/inject_incident.py --scenario cost_spike --disable
```

Incident Response Summary:

- Scenario: `cost_spike`
- Trace ID: `aee632c36f1058aee8a53c32174256dc`
- Root Cause: Mock LLM output tokens increase during `cost_spike`, so `tokens_out` rose from baseline `1336` to `5016` and `cost_usd` rose from `0.02106` to `0.07626` while latency stayed near baseline.
- Evidence: `docs/evidence/cost_spike_trace.png`
- Local terminal evidence: `Completed=10`, `Failed=0`, `Avg latency=726.3ms`, `P95 latency=795.3ms`, `Tokens in/out=340/5016`, `Total cost_usd=0.07626`
- Langfuse API evidence: trace `aee632c36f1058aee8a53c32174256dc` has metadata `usage_details.output=704`, output `tokens_out=704`, `cost_usd=0.010662`, tags `lab`, `qa`, `claude-sonnet-4-5`.
- Notes:

What to say in presentation:

"I enabled `cost_spike`, reran the load test, and compared token/cost fields in the terminal output and Langfuse trace. The root cause is increased LLM output token usage, not RAG latency."

## Optional Scenario: tool_fail

The repo names the error incident `tool_fail`.

```bash
python scripts/inject_incident.py --scenario tool_fail
python scripts/load_test.py --concurrency 5
python scripts/inject_incident.py --scenario tool_fail --disable
```

- Scenario: `tool_fail`
- Trace ID:
- Root Cause: Vector store retrieval raises an error, causing `/chat` requests to fail with an error response.
- Evidence: `docs/evidence/tool_fail_trace.png`
