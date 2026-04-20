# Day 13 Observability Lab Report

> **Instruction**: Fill in all sections below. This report is designed to be parsed by an automated grading assistant. Ensure all tags (e.g., `[GROUP_NAME]`) are preserved.

## 1. Team Metadata

- [GROUP_NAME]:
- [REPO_URL]:
- [MEMBERS]:
  - Member A: Nguyễn Duy Minh Hoàng - 2A202600155 | Role: Logging & PII
  - Member B: Đào Anh Quân - 2A202600028 | Role: PII Scrubbing & Log Schema
  - Member C: [Name] | Role: SLO & Alerts
  - Member D: Nguyễn Lê Minh Luân - 2A202600398 | Role: Tracing, Load Test & Incident Debugging
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

### Đào Anh Quân - 2A202600028

- [TASKS_COMPLETED]: **PII Scrubbing & Log Schema**: Thêm 2 pattern PII mới cho dữ liệu cá nhân tiếng Việt: passport_vn (hộ chiếu: 1 ký tự viết hoa + 7-8 số) và address_vn (địa chỉ: các từ khóa vị trí như đường, phường, quận, huyện, tỉnh, xã). Sắp xếp lại thứ tự CCCD trước phone_vn để tránh xung đột pattern (CCCD 12 chữ số). Kích hoạt scrub_event processor trong logging config để đảm bảo PII được làm sạch ở tất cả payload. Viết 9 test case toàn diện bao gồm: email, phone_vn, CCCD, credit card, passport_vn (7 và 8 chữ số), address_vn (nhiều biến thể), và negative case. Đạt 100% coverage cho các pattern PII. **Real LLM Integration**: Loại bỏ toàn bộ mock_llm, tạo app/llm.py với class RealLLM sử dụng OpenAI API, tích hợp GPT-4o-mini với định giá đúng ($0.15/1M input tokens, $0.60/1M output tokens). Cập nhật app/agent.py để sử dụng RealLLM, hỗ trợ incident simulation (cost_spike bằng cách chuyển sang gpt-4o). Xóa luôn mock_rag.py, tạo app/rag.py với knowledge base 12 chủ đề và hỗ trợ incident (rag_slow, tool_fail).
- [EVIDENCE_LINK]: PII work: Commit 78b58ba + 4cf2496 + PR #1 (aeb68e7); Real LLM work: Commit 899bf28 (feat: use real llm instead of mock) + PR #2 (666999f)

### [MEMBER_C_NAME]

- [TASKS_COMPLETED]:
- [EVIDENCE_LINK]:

### Nguyễn Lê Minh Luân - 2A202600398

- [TASKS_COMPLETED]: Hoàn thiện workflow Member D cho tracing, load test và incident debugging; cấu hình Langfuse local qua `.env` nhưng không commit secrets; nâng cấp `scripts/load_test.py` để tạo traffic có kiểm soát với `--concurrency`, `--num-requests`, `--timeout` và in summary gồm completed/failed, average latency, P95 latency, tokens in/out, total cost; nâng cấp `scripts/inject_incident.py` để bật/tắt `rag_slow`, `cost_spike`, `tool_fail` và kiểm tra `--status`; sửa `app/tracing.py` để tương thích Langfuse v3 thay vì fallback no-op; thêm regression tests cho load-test tooling, incident tooling và Langfuse tracing import; chạy baseline, `rag_slow`, `cost_spike`, xác nhận traces trên Langfuse và chụp screenshot evidence.
- [GAINS]: Giúp nhóm có quy trình incident response có thể demo lại từ terminal đến Langfuse dashboard. Load-test summary giúp so sánh rõ baseline với incident bằng số liệu định lượng: request success/failure, P95 latency, token usage và cost. Fix Langfuse v3 tracing biến tracing từ trạng thái "có decorator nhưng không gửi trace" thành trace thật trên dashboard, giúp lấy Trace ID và waterfall làm bằng chứng root cause. Với `rag_slow`, evidence cho thấy latency tăng mạnh do RAG/retrieval bottleneck; với `cost_spike`, evidence cho thấy token/cost tăng trong khi latency gần baseline.
- [EVIDENCE_LINK]: Commits: `c59c73e` (`feat: improve incident load test tooling`), `8d7cd13` (`docs: incident debugging evidence and root cause analysis`), `c9a23d3` (`docs: add local incident evidence results`), `ac3fb7e` (`fix: support Langfuse v3 tracing`), `45d7677` (`docs: add Langfuse incident evidence screenshots`). Screenshots: `docs/evidence/langfuse_trace_list.png`, `docs/evidence/rag_slow_trace.png`, `docs/evidence/cost_spike_trace.png`. Report: `docs/incident-response-summary.md`.

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
