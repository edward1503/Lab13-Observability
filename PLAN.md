# Day 13 Observability Lab — Kế hoạch thực hiện nhóm 5 người

## Tổng quan Lab

**Mục tiêu**: Hoàn thiện một FastAPI "AI Agent" với đầy đủ observability stack: Logging → Tracing → Metrics → Dashboard → Alerts.

**Thang điểm**: 60% nhóm + 40% cá nhân (commit/PR là bằng chứng bắt buộc).

**Thời gian dự kiến**: ~4 giờ lab.

---

## Phân công 5 thành viên

### Member A — Logging & Correlation ID
**Trách nhiệm**: Đảm bảo mỗi request có unique ID xuyên suốt hệ thống, log context đúng định dạng JSON.

**Files chính**: 
- `app/middleware.py`
- `app/main.py`

**TODOs cần làm:**

1. **`app/middleware.py`** — Bỏ comment và hoàn thiện 4 TODO:
   - `clear_contextvars()` — tránh leak context giữa các request
   - Extract `x-request-id` từ header hoặc tạo mới dạng `req-<8-char-hex>`
   - `bind_contextvars(correlation_id=...)` — liên kết ID với structlog context
   - Thêm `x-request-id` và `x-response-time-ms` vào response headers

2. **`app/main.py:47`** — Uncomment và điền `bind_contextvars(...)` với:
   - `user_id_hash` (dùng `hash_user_id()` từ pii.py)
   - `session_id`
   - `feature`
   - `model` (từ agent)
   - `env` (từ os.getenv)

**Verify**: 
```bash
python scripts/validate_logs.py
```
Điểm phần correlation ID phải pass.

**Commit strategy**:
- Commit 1: "feat: implement correlation ID in middleware"
- Commit 2: "feat: enrich logs with request context in chat endpoint"

---

### Member B — PII Scrubbing & Log Schema
**Trách nhiệm**: Đảm bảo không có dữ liệu nhạy cảm (email, số CCCD, điện thoại) trong logs.

**Files chính**: 
- `app/pii.py`
- `app/logging_config.py`

**TODOs cần làm:**

1. **`app/pii.py:11`** — Thêm ít nhất 2 pattern mới vào `PII_PATTERNS`:
   - Vietnamese passport: `r"\b[A-Z]\d{7,8}\b"`
   - Vietnamese address keywords: regex bắt "đường", "phường", "quận", "tỉnh" + số/tên
   - (Optional) Social security number, medical record ID, etc.

2. **`app/logging_config.py:46`** — Uncomment `scrub_event` trong processors list

3. **Optional**: Viết thêm test case cho các pattern mới

**Verify**: 
```bash
python tests/test_pii.py
python scripts/validate_logs.py
```
- Tất cả test pass
- `validate_logs.py` không báo PII leak
- Có bằng chứng scrubbing trong logs (ví dụ `[REDACTED_EMAIL]`, `[REDACTED_CCCD]`)

**Commit strategy**:
- Commit 1: "feat: add Vietnamese passport and address PII patterns"
- Commit 2: "feat: enable PII scrubbing processor in logging config"

---

### Member C — SLO & Alert Rules
**Trách nhiệm**: Định nghĩa các mục tiêu service (SLO) và quy tắc cảnh báo có ý nghĩa.

**Files chính**: 
- `config/slo.yaml`
- `config/alert_rules.yaml`
- `docs/alerts.md`

**TODOs cần làm:**

1. **`config/slo.yaml`** — Cập nhật targets có ý nghĩa thực tế:
   - Xóa comment "Replace with your group's target"
   - Giữ hoặc adjust các giá trị để hợp lý (ví dụ: `latency_p95_ms: 3000`, `error_rate_pct: 2`)
   - Thêm comment giải thích lý do chọn mỗi target

2. **`config/alert_rules.yaml`** — Thêm ít nhất 1 alert rule thứ 4:
   - Gợi ý: `low_quality_score` (quality < 0.6 for 10m)
   - Hoặc: `token_budget_exceeded` (monthly_tokens > limit)
   - Hoặc: `rag_retrieval_timeout` (rag_latency > 5s for 5m)

3. **`docs/alerts.md`** — Viết runbook đầy đủ cho alert rule mới:
   - Severity: P1/P2
   - Impact: tác động gì đến người dùng
   - First checks: 3-4 bước debug đầu tiên
   - Mitigation: 2-3 cách sửa chữa

   Format giống 3 alerts có sẵn.

**Verify**: 
- Mỗi alert trong `alert_rules.yaml` phải có `runbook:` trỏ đến anchor có thật trong `alerts.md`
- Ví dụ: `runbook: docs/alerts.md#4-low-quality-score`

**Commit strategy**:
- Commit 1: "docs: update SLO targets with rationale"
- Commit 2: "feat: add low_quality_score alert rule and runbook"

---

### Member D — Tracing & Load Test & Incident Debugging
**Trách nhiệm**: Setup Langfuse, generate traffic, inject failures, debug root causes.

**Files chính**: 
- `.env`
- `app/tracing.py` (read-only)
- `app/agent.py` (read-only)
- `scripts/load_test.py`
- `scripts/inject_incident.py`

**TODOs cần làm:**

1. **Setup Langfuse**:
   - Tạo tài khoản miễn phí tại [cloud.langfuse.com](https://cloud.langfuse.com)
   - Copy `.env.example` → `.env`
   - Điền `LANGFUSE_PUBLIC_KEY` và `LANGFUSE_SECRET_KEY` từ dashboard Langfuse

2. **Run load test và xác nhận traces**:
   ```bash
   # Start app trước
   uvicorn app.main:app --reload
   
   # Terminal khác: run load test
   python scripts/load_test.py --concurrency 5
   ```
   - Chờ ≥ 10 requests hoàn thành
   - Vào Langfuse dashboard → xác nhận ≥ 10 traces xuất hiện
   - Chụp screenshot: list traces hoặc 1 trace waterfall

3. **Inject incidents và debug**:
   ```bash
   # Scenario 1: RAG latency
   python scripts/inject_incident.py --scenario rag_slow
   # → Chạy load test lại, quan sát traces
   # → Ghi chép: RAG span bao lâu? Đó là bottleneck?
   # → Lấy Trace ID cụ thể
   python scripts/inject_incident.py --scenario rag_slow --disable
   
   # Scenario 2: Cost spike
   python scripts/inject_incident.py --scenario cost_spike
   # → Quan sát: tokens_in/out tăng không? LLM model thay đổi?
   # → Ghi chép Trace ID
   python scripts/inject_incident.py --scenario cost_spike --disable
   
   # Scenario 3: (Nếu có) Error injection
   # python scripts/inject_incident.py --scenario error_simulation
   ```

4. **Tổng hợp incident response evidence**:
   - Mỗi scenario: 
     - Trace ID bằng chứng
     - Screenshot waterfall span
     - Giải thích root cause (1-2 dòng)

**Deliver**:
```
Incident Response Summary:
- Scenario: rag_slow
  Trace ID: lang_xyz123
  Root Cause: RAG latency > 3s, spans show retrieve() call taking 3.2s
  Evidence: docs/evidence/rag_slow_trace.png

- Scenario: cost_spike
  Trace ID: lang_abc456
  Root Cause: Mock LLM tokens_out increased 2x, cost_usd jumped accordingly
  Evidence: docs/evidence/cost_spike_trace.png
```

**Commit strategy**:
- Commit 1: "chore: setup Langfuse credentials"
- Commit 2: "docs: incident debugging evidence and root cause analysis"

---

### Member E — Dashboard & Report Lead
**Trách nhiệm**: Build dashboard 6 panels, điền blueprint report đầy đủ, chuẩn bị demo.

**Files chính**: 
- `docs/blueprint-template.md` (chính)
- `docs/grading-evidence.md` (hỗ trợ)
- `app/metrics.py` (read-only)

**TODOs cần làm:**

1. **Build Dashboard (6 panels)**:
   - Đọc `docs/dashboard-spec.md`
   - Dữ liệu lấy từ endpoint `/metrics` (JSON)
   - Công cụ: Grafana, Metabase, matplotlib script, hoặc thậm chí Google Sheets
   - 6 panels bắt buộc:
     1. **Latency P50/P95/P99** — line chart, có SLO threshold (3000ms)
     2. **Traffic (Request Count)** — bar/line chart, QPS
     3. **Error Rate** — line chart, có threshold (2%)
     4. **Cost over Time** — area chart, tracking daily spend
     5. **Tokens In/Out** — stacked bar, per-request breakdown
     6. **Quality Score** — gauge/line, heuristic score (0.0–1.0)
   
   - Time range default: 1 hour
   - Auto refresh: 15–30 seconds
   - Các panel phải có unit labels rõ ràng

2. **Tổng hợp Screenshots**:
   - Dashboard 6 panels: `docs/evidence/dashboard_overview.png`
   - Correlation ID trong log: `docs/evidence/correlation_id.png` (từ Member A)
   - PII redaction: `docs/evidence/pii_redaction.png` (từ Member B)
   - Alert rules: `docs/evidence/alert_rules.png` (từ Member C)
   - Trace waterfall: `docs/evidence/trace_waterfall.png` (từ Member D)

3. **Điền `docs/blueprint-template.md`** — tất cả tags `[...]` phải có giá trị, không để trống:
   ```
   [GROUP_NAME] = Tên nhóm
   [REPO_URL] = https://github.com/...
   [MEMBERS] = Danh sách 5 người + role
   [VALIDATE_LOGS_FINAL_SCORE] = kết quả từ validate_logs.py
   [TOTAL_TRACES_COUNT] = số lượng từ Langfuse
   [PII_LEAKS_FOUND] = 0 (hoặc mô tả nếu có)
   
   [EVIDENCE_*_SCREENSHOT] = đường dẫn file
   [ROOT_CAUSE_PROVED_BY] = Trace ID: lang_xyz123
   [FIX_ACTION] = tóm tắt cách fix
   [PREVENTIVE_MEASURE] = cách tránh lặp lại
   
   [MEMBER_A_NAME]: [TASKS_COMPLETED] = "Implement correlation ID middleware"
   [MEMBER_A_NAME]: [EVIDENCE_LINK] = (commit link)
   ... (tương tự cho 5 thành viên)
   ```

4. **Chuẩn bị Script Demo Live** (~5 phút):
   ```bash
   # Bước 1: Start app
   uvicorn app.main:app --reload
   
   # Bước 2: Run load test (show logs, traces appearing)
   python scripts/load_test.py --concurrency 2
   
   # Bước 3: Inject incident
   python scripts/inject_incident.py --scenario rag_slow
   python scripts/load_test.py --num-requests 5
   
   # Bước 4: Show dashboard metrics
   # (open /metrics endpoint, show Langfuse dashboard)
   
   # Bước 5: Explain root cause (dùng trace ID)
   # (trình bày findings từ incident debugging)
   ```

**Commit strategy**:
- Commit 1: "docs: add dashboard screenshots and evidence"
- Commit 2: "docs: complete blueprint template with all team evidence"

---

## Git Workflow

### Branch Strategy

```
main (protected)
├── feature/member-a-correlation-id
├── feature/member-b-pii-scrubbing
├── feature/member-c-slo-alerts
├── feature/member-d-tracing-loadtest
└── feature/member-e-dashboard-report
```

### Workflow cho mỗi thành viên

1. **Tạo branch riêng**:
   ```bash
   git checkout main
   git pull origin main
   git checkout -b feature/member-<initial>-<topic>
   ```

2. **Commit thường xuyên** (mỗi TODO = 1 commit):
   ```bash
   git add <files>
   git commit -m "feat: <description of TODO completed>"
   ```
   Ví dụ:
   ```bash
   git commit -m "feat: implement correlation ID extraction in middleware"
   git commit -m "feat: bind correlation ID to structlog contextvars"
   git commit -m "feat: add x-request-id to response headers"
   ```

3. **Push và tạo Pull Request**:
   ```bash
   git push origin feature/member-<initial>-<topic>
   ```
   - Tạo PR trên GitHub
   - Tag ≥1 thành viên khác để review
   - Dùng PR description để mô tả những gì đã làm

4. **Merge sau approval**:
   ```bash
   # Sau khi được 1 approval từ thành viên khác
   # Merge qua GitHub UI hoặc:
   git checkout main
   git pull origin main
   git merge feature/member-<initial>-<topic>
   git push origin main
   ```

### Commit Message Convention

```
<type>: <subject>

<body (optional)>

Co-Authored-By: Member Name <email@example.com>
```

Ví dụ:
```
feat: implement correlation ID extraction and propagation

- Extract x-request-id from headers with default req-<8-char-hex>
- Bind correlation_id to structlog contextvars for all logs
- Add x-request-id and x-response-time-ms to response headers

Fixes #TODO
Co-Authored-By: Anh Quan <anhquan@example.com>
```

---

## Timeline gợi ý (4 giờ lab)

| Thời gian | Công việc | Người phụ trách |
|---|---|---|
| **0:00–0:30** | Setup môi trường, clone repo, tạo branches, đọc TODO | Toàn nhóm |
| **0:30–1:30** | **Lập trình core TODO** | A, B song song |
| | - Member A: middleware + main.py binding | A |
| | - Member B: PII patterns + logging config | B |
| **1:00–2:00** | **Setup infrastructure** | C, D song song |
| | - Member C: SLO + Alert rules review | C |
| | - Member D: Langfuse setup, đầu tiên load test | D |
| **1:30–2:30** | **Verify & merge** | A, B, C |
| | - Run `validate_logs.py`, fix lỗi | A, B |
| | - Merge PR vào main | A, B, C |
| **2:00–3:00** | **Incident debugging** | D |
| | - Inject rag_slow, chụp Trace ID & screenshot | D |
| | - Inject cost_spike, ghi chép root cause | D |
| **2:30–3:30** | **Dashboard + Report** | E |
| | - Build 6 panels từ /metrics | E |
| | - Tổng hợp screenshots từ A, B, C, D | E |
| | - Điền blueprint-template.md | E |
| **3:30–4:00** | **Rehearsal + Fix** | Toàn nhóm |
| | - Rehearsal demo (~5 phút) | E (leader), all |
| | - Fix lỗi cuối cùng | Tuỳ tình hình |
| | - Final merge + push | Toàn nhóm |

---

## Checklist trước nộp

### Technical Verification
- [ ] `python scripts/validate_logs.py` → score ≥ 80/100
- [ ] ≥ 10 traces visible on Langfuse dashboard
- [ ] Dashboard có đủ 6 panels (có screenshot)
- [ ] Zero PII leaks (không còn email, CCCD, phone lọt vào logs)
- [ ] Tất cả branch được merge vào `main`

### Documentation
- [ ] `docs/blueprint-template.md` điền đầy đủ, không tag trống
- [ ] `docs/alerts.md` có runbook cho ≥3 alerts (có link anchor)
- [ ] `docs/grading-evidence.md` có screenshot cho mỗi section
- [ ] Tất cả screenshot lưu trong `docs/evidence/` folder

### Git Evidence
- [ ] Mỗi thành viên có ≥3 commits riêng trên branch của mình
- [ ] Commit messages rõ ràng, mô tả TODO cụ thể
- [ ] Mỗi commit link đưa ra file + dòng code thay đổi
- [ ] PR được review + merge, không force push

### Demo Readiness
- [ ] App chạy mượt mà trên `uvicorn app.main:app --reload`
- [ ] Load test sinh traffic thành công
- [ ] Incident injection hoạt động (show trong logs/traces)
- [ ] Dashboard auto-refresh từ `/metrics` endpoint
- [ ] Demo script (~5 phút) viết sẵn và rehearsed

---

## Useful Commands

```bash
# Setup
python -m venv .venv
source .venv/bin/activate  # hoặc .venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env
# Edit .env: điền LANGFUSE keys

# Develop
uvicorn app.main:app --reload

# Validate
python scripts/validate_logs.py
python tests/test_pii.py
python scripts/load_test.py --concurrency 5

# Debug incidents
python scripts/inject_incident.py --scenario rag_slow
python scripts/inject_incident.py --scenario rag_slow --disable

# Git
git status
git log --oneline --graph --all
git diff feature/member-a-... main
```

---

## Bonus Opportunities (+10 điểm)

1. **Cost Optimization (+3đ)**
   - Implement prompt caching hoặc token dedup
   - Show before/after cost số liệu

2. **Dashboard Excellence (+3đ)**
   - Design đẹp, chuyên nghiệp (CSS, dark mode, custom colors)
   - Thêm heatmap hoặc correlation matrix

3. **Automation (+2đ)**
   - Script auto-generate alerts từ SLO config
   - CI/CD pipeline để validate logs tự động

4. **Audit Logs (+2đ)**
   - Tách riêng audit log stream (`data/audit.jsonl`)
   - Track model changes, incident toggles

---

## Tài liệu tham khảo

- Main README: `README.md`
- Dashboard spec: `docs/dashboard-spec.md`
- Alert/Runbook template: `docs/alerts.md`
- Grading rubric: `day13-rubric-for-instructor.md`
- Langfuse docs: https://docs.langfuse.com
- structlog: https://www.structlog.org/

---

## Q&A

**Q: Nếu validate_logs.py fail?**  
A: Xem error message cụ thể, member A+B debug theo hint. Thường do missing correlation ID hoặc PII format không đúng.

**Q: Langfuse account creation bị lỗi?**  
A: Có fallback dummy mode tích hợp sẵn (`observe` decorator có try/except). Vẫn chạy được nhưng không có trace.

**Q: Làm sao để test incidents locally?**  
A: Run load test trong 1 terminal, `inject_incident.py` trong terminal khác. Metrics endpoint sẽ reflect immediately.

**Q: Commit vào branch của người khác được không?**  
A: Được, nhưng best practice là push vào branch của mình → tạo PR → request review → merge. Nhờ review giúp catch lỗi sớm.

---

Chúc nhóm thành công! 🚀
