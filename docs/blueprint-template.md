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

- [TASKS_COMPLETED]: Đã hoàn thiện Correlation ID middleware, thêm các headers `x-request-id` và `x-response-time-ms` vào response; Làm giàu (enrich) log của endpoint `/chat` với `user_id_hash`, `session_id`, `feature`, `model`, `env`; Đã viết unit tests cho middleware và log context.
- [GAINS]: (Giá trị mang lại) Giúp hệ thống có khả năng truy vết (traceability) 100% các request nhờ Correlation ID. Biến log từ văn bản thuần túy thành dữ liệu có cấu trúc phục vụ trực tiếp cho việc tạo Dashboard thống kê. Rút ngắn thời gian debug lỗi nhờ cung cấp sẵn mã ID cho khách hàng báo cáo khi có sự cố.
- [EVIDENCE_LINK]: Commit ID: 1ecd560863dbbffaec9c875e271368ffbac4b944

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
