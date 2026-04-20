# Day 13 Observability Lab Report

> **Instruction**: Fill in all sections below. This report is designed to be parsed by an automated grading assistant. Ensure all tags (e.g., `[GROUP_NAME]`) are preserved.

## 1. Team Metadata

- [GROUP_NAME]: Lab13 Observability Team
- [REPO_URL]: https://github.com/edward1503/Lab13-Observability.git
- [MEMBERS]:
  - Member A: Nguyễn Duy Minh Hoàng - 2A202600155 | Role: Logging & PII
  - Member B: Đào Anh Quân - 2A202600028 | Role: PII Scrubbing & Log Schema
  - Member C: Nguyễn Đôn Đức - 2A202600145 | Role: SLO & Alerts
  - Member D: Nguyễn Lê Minh Luân - 2A202600398 | Role: Tracing, Load Test & Incident Debugging
  - Member E: Vu Quang Phuc | Role: Demo & Report

---

## 2. Group Performance (Auto-Verified)

- [VALIDATE_LOGS_FINAL_SCORE]: 100/100
- [TOTAL_TRACES_COUNT]: 30 traces observed in Langfuse during the final local run. Evidence: `docs/evidence/langfuse_trace_list.png`
- [PII_LEAKS_FOUND]: 0

---

## 3. Technical Evidence (Group)

### 3.1 Logging & Tracing

- [EVIDENCE_CORRELATION_ID_SCREENSHOT]: docs/evidence/correlation_id.png
- [EVIDENCE_PII_REDACTION_SCREENSHOT]: docs/evidence/pii_redaction.png
- [EVIDENCE_TRACE_WATERFALL_SCREENSHOT]: docs/evidence/rag_slow_trace.png
- [TRACE_WATERFALL_EXPLANATION]: Trong incident `rag_slow`, trace waterfall cho thấy span retrieval/RAG chiếm phần lớn tổng latency, trong khi bước LLM vẫn gần baseline. Điều đó chứng minh bottleneck nằm ở retrieval path chứ không phải model generation.

### 3.2 Dashboard & SLOs

- [DASHBOARD_6_PANELS_SCREENSHOT]: docs/evidence/dashboard_overview.png
- [SLO_TABLE]:| SLI         |     Target | Window | Current Value |
  | ----------- | ---------: | ------ | ------------: |
  | Latency P95 |   < 3000ms | 28d    | 818.7ms baseline; 5337.9ms during `rag_slow` |
  | Error Rate  |       < 2% | 28d    | 0% on healthy baseline run |
  | Cost Budget | < $2.5/day | 1d     | $0.02106 baseline; $0.07626 during `cost_spike` |

### 3.3 Alerts & Runbook

- [ALERT_RULES_SCREENSHOT]: docs/evidence/alert_rules.png
- [ALERT_RULES_EXPLANATION]: Alert rules cover latency, error rate, budget spike, and low quality score; every rule links to a concrete runbook entry in `docs/alerts.md`.

---

## 4. Incident Response (Group)

- [SCENARIO_NAME]: rag_slow
- [SYMPTOMS_OBSERVED]: Sau khi bật incident `rag_slow`, dashboard và load test cho thấy latency tăng mạnh từ baseline `P95=818.7ms` lên `P95=5337.9ms`.
- [ROOT_CAUSE_PROVED_BY]: Trace ID `9929f3f51815697114ba6c9eedb671e7` trong Langfuse và waterfall screenshot `docs/evidence/rag_slow_trace.png`, nơi retrieval span là thành phần chiếm thời gian lớn nhất.
- [FIX_ACTION]: Tắt incident `rag_slow`, chạy lại load test để xác nhận latency quay về baseline, và xác định retrieval là thành phần cần tối ưu hoặc cần fallback.
- [PREVENTIVE_MEASURE]: Giữ alert `high_latency_p95`, tiếp tục theo dõi dashboard `/dashboard`, và dùng trace waterfall làm bước debug đầu tiên để phân biệt bottleneck nằm ở RAG hay LLM.

---

## 5. Individual Contributions & Evidence

### Nguyễn Duy Minh Hoàng - 2A202600155

- [TASKS_COMPLETED]: Đã hoàn thiện Correlation ID middleware, thêm các headers `x-request-id` và `x-response-time-ms` vào response; Làm giàu (enrich) log của endpoint `/chat` với `user_id_hash`, `session_id`, `feature`, `model`, `env`; Đã viết unit tests cho middleware và log context.
- [GAINS]: (Giá trị mang lại) Giúp hệ thống có khả năng truy vết (traceability) 100% các request nhờ Correlation ID. Biến log từ văn bản thuần túy thành dữ liệu có cấu trúc phục vụ trực tiếp cho việc tạo Dashboard thống kê. Rút ngắn thời gian debug lỗi nhờ cung cấp sẵn mã ID cho khách hàng báo cáo khi có sự cố.
- [EVIDENCE_LINK]: Commit ID: 1ecd560863dbbffaec9c875e271368ffbac4b944

### Đào Anh Quân - 2A202600028

- [TASKS_COMPLETED]: **PII Scrubbing & Log Schema**: Thêm 2 pattern PII mới cho dữ liệu cá nhân tiếng Việt: passport_vn (hộ chiếu: 1 ký tự viết hoa + 7-8 số) và address_vn (địa chỉ: các từ khóa vị trí như đường, phường, quận, huyện, tỉnh, xã). Sắp xếp lại thứ tự CCCD trước phone_vn để tránh xung đột pattern (CCCD 12 chữ số). Kích hoạt scrub_event processor trong logging config để đảm bảo PII được làm sạch ở tất cả payload. Viết 9 test case toàn diện bao gồm: email, phone_vn, CCCD, credit card, passport_vn (7 và 8 chữ số), address_vn (nhiều biến thể), và negative case. Đạt 100% coverage cho các pattern PII. **Real LLM Integration**: Loại bỏ toàn bộ mock_llm, tạo app/llm.py với class RealLLM sử dụng OpenAI API, tích hợp GPT-4o-mini với định giá đúng ($0.15/1M input tokens, $0.60/1M output tokens). Cập nhật app/agent.py để sử dụng RealLLM, hỗ trợ incident simulation (cost_spike bằng cách chuyển sang gpt-4o). Xóa luôn mock_rag.py, tạo app/rag.py với knowledge base 12 chủ đề và hỗ trợ incident (rag_slow, tool_fail).
- [EVIDENCE_LINK]: PII work: Commit 78b58ba + 4cf2496 + PR #1 (aeb68e7); Real LLM work: Commit 899bf28 (feat: use real llm instead of mock) + PR #2 (666999f)

### Nguyễn Đôn Đức - 2A202600145

- [TASKS_COMPLETED]: SLO Configuration: Cập nhật lý do (rationale) chuyên nghiệp cho các mục tiêu trong config/slo.yaml và bổ sung chỉ số P99 Latency. Alert Rules: Thiết lập hệ thống 7 quy tắc cảnh báo toàn diện trong config/alert_rules.yaml (bao gồm cả các cảnh báo về chất lượng AI và chi phí). Runbook: Viết tài liệu hướng dẫn xử lý sự cố chi tiết trong docs/alerts.md. OpenAI Integration: Chuyển đổi sang langfuse.openai để tự động hóa việc theo dõi model, token usage và cost. Nested Spans: Cấu trúc lại Trace theo dạng Waterfall (phân cấp). Hiện tại bạn có thể thấy rõ bước RAG (retrieve-docs) nằm riêng biệt với bước xử lý của LLM. Explicit Context: Tinh chỉnh để Trace chỉ gửi lên những dữ liệu cần thiết (input, output, user_id, session_id), giúp bảo mật và dễ đọc hơn.
- [EVIDENCE_LINK]: 0642f78297ba27ccbb6615acae6b6c6b6ea707a7 - Merge pull request #5 from edward1503/feat/langfuse-best-practices , 19858502399eab473a4d796344381229c6475590 - update phase 3

### Nguyễn Lê Minh Luân - 2A202600398

- [TASKS_COMPLETED]: Hoàn thiện workflow Member D cho tracing, load test và incident debugging; cấu hình Langfuse local qua `.env` nhưng không commit secrets; nâng cấp `scripts/load_test.py` để tạo traffic có kiểm soát với `--concurrency`, `--num-requests`, `--timeout` và in summary gồm completed/failed, average latency, P95 latency, tokens in/out, total cost; nâng cấp `scripts/inject_incident.py` để bật/tắt `rag_slow`, `cost_spike`, `tool_fail` và kiểm tra `--status`; sửa `app/tracing.py` để tương thích Langfuse v3 thay vì fallback no-op; thêm regression tests cho load-test tooling, incident tooling và Langfuse tracing import; chạy baseline, `rag_slow`, `cost_spike`, xác nhận traces trên Langfuse và chụp screenshot evidence.
- [GAINS]: Giúp nhóm có quy trình incident response có thể demo lại từ terminal đến Langfuse dashboard. Load-test summary giúp so sánh rõ baseline với incident bằng số liệu định lượng: request success/failure, P95 latency, token usage và cost. Fix Langfuse v3 tracing biến tracing từ trạng thái "có decorator nhưng không gửi trace" thành trace thật trên dashboard, giúp lấy Trace ID và waterfall làm bằng chứng root cause. Với `rag_slow`, evidence cho thấy latency tăng mạnh do RAG/retrieval bottleneck; với `cost_spike`, evidence cho thấy token/cost tăng trong khi latency gần baseline.
- [EVIDENCE_LINK]: Commits: `c59c73e` (`feat: improve incident load test tooling`), `8d7cd13` (`docs: incident debugging evidence and root cause analysis`), `c9a23d3` (`docs: add local incident evidence results`), `ac3fb7e` (`fix: support Langfuse v3 tracing`), `45d7677` (`docs: add Langfuse incident evidence screenshots`). Screenshots: `docs/evidence/langfuse_trace_list.png`, `docs/evidence/rag_slow_trace.png`, `docs/evidence/cost_spike_trace.png`. Report: `docs/incident-response-summary.md`.

### Vu Quang Phuc

- [TASKS_COMPLETED]: Hoàn thiện phần việc Member E bằng cách xây dựng dashboard 6 panels cho endpoint `/dashboard`, thêm các công cụ hỗ trợ dashboard (`scripts/dashboard.html`, `scripts/dashboard.py`, `scripts/serve_dashboard.py`), tổng hợp evidence cho correlation ID, PII redaction, alert rules, dashboard overview, và hoàn thiện blueprint report theo đúng flow demo mà instructor yêu cầu trong `message.txt`. Phần trình bày của Member E tập trung vào ACT 1 và ACT 5, tức là dẫn demo tổng thể và giải thích dashboard/SLO cho giảng viên.
- [EVIDENCE_LINK]: Commit `493c1142841f1c0e7046a800f4eb8379fd501df6` (`Conplete the task dashboard`); evidence files: `docs/evidence/dashboard_overview.png`, `docs/evidence/correlation_id.png`, `docs/evidence/pii_redaction.png`, `docs/evidence/alert_rules.png`

---

## 6. Bonus Items (Optional)

- [BONUS_COST_OPTIMIZATION]: Có evidence so sánh cost trước và sau incident `cost_spike`: baseline `Total cost_usd=0.02106` tăng lên `0.07626` khi token output tăng mạnh. Evidence: `docs/evidence/cost_spike_trace.png`, `docs/incident-response-summary.md`.
- [BONUS_AUDIT_LOGS]: Chưa triển khai audit log tách riêng trong trạng thái repo hiện tại.
- [BONUS_CUSTOM_METRIC]: Dashboard có custom metric `quality score` và time-series metrics history qua `/metrics/history`, dùng để hiển thị panel chất lượng và xu hướng theo thời gian.

[VALIDATE_LOGS_FINAL_SCORE]: 100/100
[PII_LEAKS_FOUND]: 0
[SAMPLE_RUNBOOK_LINK]: docs/alerts.md#4-low-quality-score
