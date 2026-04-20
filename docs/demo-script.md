# Demo Script

## Goal
Show the observability flow in under 5 minutes: logs -> metrics dashboard -> incident root cause.

## Live flow
1. Start the app
   ```bash
   uvicorn app.main:app --reload
   ```
2. Generate traffic
   ```bash
   python scripts/load_test.py --concurrency 2
   ```
3. Show JSON log evidence
   - Open `data/logs.jsonl`
   - Point out shared `correlation_id`
   - Point out `[REDACTED_EMAIL]` / `[REDACTED_PHONE_VN]` / `[REDACTED_CREDIT_CARD]`
4. Show dashboard evidence
   - Open `docs/evidence/dashboard_overview.png`
   - Explain the 6 panels: latency, traffic, error rate, cost, tokens, quality
   - Mention SLO lines: `3000ms` latency and `2%` error-rate threshold
5. Show incident debugging story
   ```bash
   python scripts/inject_incident.py --scenario rag_slow
   python scripts/load_test.py --concurrency 1
   python scripts/inject_incident.py --scenario rag_slow --disable
   ```
   - Open `docs/evidence/trace_waterfall.png`
   - Explain that `retrieve()` is the bottleneck during `rag_slow`
6. Close with report/evidence
   - Open `docs/blueprint-template.md`
   - Open `docs/grading-evidence.md`
   - Mention `docs/evidence/report-summary.json` for exact numbers

## Backup path if live internet is blocked
- Use the evidence bundle already committed under `docs/evidence/`
- State that local trace IDs were captured during evidence generation and live Langfuse screenshots should be shown from member D's machine when available
