# Day 13 Observability Lab Report

> **Instruction**: Fill in all sections below. This report is designed to be parsed by an automated grading assistant. Ensure all tags (e.g., `[GROUP_NAME]`) are preserved.

## 1. Team Metadata

- [GROUP_NAME]:
- [REPO_URL]:
- [MEMBERS]:
  - Member A: Nguyễn Duy Minh Hoàng - 2A202600155 | Role: Logging & PII
  - Member B: [Name] | Role: Tracing & Enrichment
  - Member C: [Name] | Role: SLO & Alerts
  - Member D: [Name] | Role: Load Test & Dashboard
  - Member E: [Name] | Role: Demo & Report

---

## 2. Group Performance (Auto-Verified)

- 
- [TOTAL_TRACES_COUNT]:
- 

---

## 3. Technical Evidence (Group)

### 3.1 Logging & Tracing

- [EVIDENCE_CORRELATION_ID_SCREENSHOT]: [Path to image]
- [EVIDENCE_PII_REDACTION_SCREENSHOT]: [Path to image]
- [EVIDENCE_TRACE_WATERFALL_SCREENSHOT]: [Path to image]
- [TRACE_WATERFALL_EXPLANATION]: (Briefly explain one interesting span in your trace)

### 3.2 Dashboard & SLOs

- [DASHBOARD_6_PANELS_SCREENSHOT]: [Path to image]
- [SLO_TABLE]:| SLI         |     Target | Window | Current Value |
  | ----------- | ---------: | ------ | ------------: |
  | Latency P95 |   < 3000ms | 28d    |               |
  | Error Rate  |       < 2% | 28d    |               |
  | Cost Budget | < $2.5/day | 1d     |               |

### 3.3 Alerts & Runbook

- [ALERT_RULES_SCREENSHOT]: [Path to image]
- 

---

## 4. Incident Response (Group)

- [SCENARIO_NAME]: (e.g., rag_slow)
- [SYMPTOMS_OBSERVED]:
- [ROOT_CAUSE_PROVED_BY]: (List specific Trace ID or Log Line)
- [FIX_ACTION]:
- [PREVENTIVE_MEASURE]:

---

## 5. Individual Contributions & Evidence

### Nguyễn Duy Minh Hoàng - 2A202600155

- [TASKS_COMPLETED]: Implemented correlation ID middleware, added `x-request-id` and `x-response-time-ms` response headers, enriched `/chat` logs with `user_id_hash`/`session_id`/`feature`/`model`/`env`, and added unit tests for middleware plus log context.
- [EVIDENCE_LINK]: Branch `feat/logging-pii` (commit/PR link pending)

### [MEMBER_B_NAME]

- [TASKS_COMPLETED]:
- [EVIDENCE_LINK]:

### [MEMBER_C_NAME]

- [TASKS_COMPLETED]:
- [EVIDENCE_LINK]:

### [MEMBER_D_NAME]

- [TASKS_COMPLETED]:
- [EVIDENCE_LINK]:

### [MEMBER_E_NAME]

- [TASKS_COMPLETED]:
- [EVIDENCE_LINK]:

---

## 6. Bonus Items (Optional)

- [BONUS_COST_OPTIMIZATION]: (Description + Evidence)
- [BONUS_AUDIT_LOGS]: (Description + Evidence)
- [BONUS_CUSTOM_METRIC]: (Description + Evidence)

[VALIDATE_LOGS_FINAL_SCORE]: 100/100
[PII_LEAKS_FOUND]: 0
[SAMPLE_RUNBOOK_LINK]: [docs/alerts.md#L...]
