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

- Total traces observed:
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
- Trace ID:
- Root Cause: RAG retrieval is the bottleneck. The `rag_slow` incident adds delay in retrieval, so request latency and the RAG span should increase by roughly 2.5 seconds.
- Evidence: `docs/evidence/rag_slow_trace.png`
- Notes:

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
- Trace ID:
- Root Cause: Mock LLM output tokens increase during `cost_spike`, so `tokens_out` and `cost_usd` rise while the model name stays the same.
- Evidence: `docs/evidence/cost_spike_trace.png`
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
