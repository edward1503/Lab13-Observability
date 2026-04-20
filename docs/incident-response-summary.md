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
- Local result: `Completed=10`, `Failed=0`, `Avg latency=726.1ms`, `P95 latency=795.5ms`, `Tokens in/out=340/1411`, `Total cost_usd=0.022185`
- Langfuse tracing status during local run: `tracing_enabled=false` because `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY` were not populated.
- Total traces observed: Pending Langfuse credentials
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
- Trace ID: Pending Langfuse credentials
- Root Cause: RAG retrieval is the bottleneck. The `rag_slow` incident adds delay in retrieval, so request latency increased from baseline `P95=795.5ms` to `P95=5336.0ms` in the local evidence run.
- Evidence: `docs/evidence/rag_slow_trace.png`
- Local terminal evidence: `Completed=10`, `Failed=0`, `Avg latency=5329.2ms`, `P95 latency=5336.0ms`, `Tokens in/out=340/1256`, `Total cost_usd=0.01986`
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
- Trace ID: Pending Langfuse credentials
- Root Cause: Mock LLM output tokens increase during `cost_spike`, so `tokens_out` rose from baseline `1411` to `5556` and `cost_usd` rose from `0.022185` to `0.08436` while latency stayed near baseline.
- Evidence: `docs/evidence/cost_spike_trace.png`
- Local terminal evidence: `Completed=10`, `Failed=0`, `Avg latency=721.7ms`, `P95 latency=787.1ms`, `Tokens in/out=340/5556`, `Total cost_usd=0.08436`
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
