# Evidence Collection Sheet

## Required screenshots
- Dashboard with 6 panels: `docs/evidence/dashboard_overview.png`
- JSON logs showing correlation_id: `docs/evidence/correlation_id.png`
- Log line with PII redaction: `docs/evidence/pii_redaction.png`
- Alert rules with runbook link: `docs/evidence/alert_rules.png`
- One trace-style incident waterfall: `docs/evidence/trace_waterfall.png`

## Notes for grader/demo
- Evidence pack was generated from real in-process requests against the app using `python3 scripts/generate_member_e_artifacts.py`.
- Summary metrics and incident measurements are saved in `docs/evidence/report-summary.json`.
- Local evidence run produced `13` requests, `12` local trace captures, `100/100` on log validation, and `0` detected PII leaks.
- The local sandbox cannot resolve `cloud.langfuse.com`, so the trace count recorded here is from local capture IDs during the same request flow. Team member D should still show the live Langfuse dashboard during demo if internet access is available.

## Optional screenshots
- Cost spike comparison is documented in `docs/evidence/report-summary.json`
- Incident root cause timing is documented in `docs/evidence/trace_waterfall.png`
