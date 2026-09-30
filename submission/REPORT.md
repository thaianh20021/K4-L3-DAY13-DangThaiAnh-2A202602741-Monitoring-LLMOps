# Báo cáo cá nhân — K4-L3B Day 13 Monitoring & LLMOps

> Mỗi học viên hoàn thiện một file duy nhất này. Chỉ cần 3 output text và 5 ảnh runtime; dùng đường dẫn tương đối, ví dụ `evidence/03-incident-trace.png`.

## 1. Thông tin học viên

- **Họ và tên:** Đặng Thái Anh
- **MSSV:** 2A202602741
- **Lớp:** K4-L3B
- **Repository URL:**
- **Commit SHA cuối:**
- **Challenge ID:** day13-k4-l3b-monitoring-llmops-v1
- **Tên project Langfuse cá nhân:** `day13-k4-l3b-2A202602741`

## 2. Evidence index

Giữ đúng ba output text và năm ảnh dưới đây. Không tách thêm ảnh; nếu cần giải thích, ghi bằng chữ trong các mục sau.

| Evidence | Đường dẫn |
|---|---|
| Pytest cuối | `evidence/pytest.txt` |
| Log validator | `evidence/log-validator.txt` |
| Dashboard validator | `evidence/dashboard-validator.txt` |
| Structured log + incident log (screenshot pending) | `evidence/13-incident-log.txt` |
| Trace list | `evidence/02-trace-list.png` |
| Trace waterfall + metadata + incident trace | `evidence/03-incident-trace.png` |
| Prompt versions + promote/rollback | `evidence/04-prompt-versioning.png` |
| Dashboard + incident metric | `evidence/05-dashboard-incident.png` |

**Lưu ý evidence:** Ảnh `01-incident-log.png` hiện là ảnh dựng, chưa phải
screenshot runtime; chưa dùng ảnh này để nộp. `04-prompt-versioning.png`
chỉ chụp trạng thái sau rollback, chưa đủ một ảnh hai cửa sổ theo SUBMISSION.md.
Hai dòng log gốc tương ứng trace ở `evidence/13-incident-log.txt`.
Ảnh thật cho rollback: `evidence/10a-prompt-before-rollback-live.png` và
`evidence/10b-prompt-after-rollback-live.png`. Dashboard là bản xem lại dữ
liệu log lịch sử, không phải dữ liệu thời gian thực tại lúc chụp.

## 3. Kết quả kỹ thuật

| Nội dung | Baseline | Kết quả cuối | Nhận xét |
|---|---|---|---|
| `validate_logs.py` | 30/100 | 100/100 | Đạt toàn bộ 4/4 hạng mục: JSON schema, Correlation ID, Enrichment, PII |
| `validate_dashboard.py` | 6/6 panel | 6/6 panel | Hợp lệ toàn bộ 6/6 panel theo dashboard contract |
| `pytest` | 0/22 passed | 22/22 passed | Đạt 100% unit tests và observability tests |
| Số traces hợp lệ | 0 | 10+ traces | Trace có đầy đủ root và child observations (`retrieval`, `generation`) |
| Số PII leak | 0 | 0 | Scrubber che sạch Email, SĐT VN, CCCD, Thẻ ngân hàng |
| Latency P95 / TTFT P95 | 155ms / 50ms | 152ms / 50ms | Phản hồi ổn định khi bình thường; phát hiện vọt lên 2652ms khi có incident |
| Retrieval success rate | 100% | 100% | Retrieval luôn trả về tài liệu hợp lệ trong corpus |

## 4. Logging và PII

- **Cách tạo/nhận và truyền correlation ID:** Trong `CorrelationIdMiddleware` (`app/middleware.py`), kiểm tra header `x-request-id`, nếu có thì nhận, nếu không thì sinh mới dạng `req-<8-hex>` (`f"req-{uuid.uuid4().hex[:8]}"`). Trước mỗi request gọi `clear_contextvars()` để tránh rò rỉ ID giữa các luồng, sau đó gọi `bind_contextvars(correlation_id=correlation_id)` và gán vào `request.state.correlation_id`. Cuối cùng trả về qua headers `x-request-id` và `x-response-time-ms`.
- **Các metadata được ghi vào structured log:**
  - Bắt buộc chung: `ts` (ISO-8601 UTC), `level`, `service`, `event`, `correlation_id`.
  - Ngữ cảnh request: `user_id_hash` (SHA-256 rút gọn 12 ký tự), `session_id`, `feature`, `model`, `env`.
  - Đo lường sau khi hoàn thành request: `latency_ms`, `ttft_ms`, `tokens_in`, `tokens_out`, `cost_usd`, `quality_score`, `tool_name="retrieval"`, `tool_success=True/False`, và payload preview đã scrub.
- **Cách bảo đảm PII được scrub trước khi ghi:** Processor `scrub_event` được đăng ký trong danh sách processors của `structlog.configure()` nằm ngay trước `JsonlFileProcessor()` và `JSONRenderer()`. Hàm thực hiện quét và che bằng regex cho email, số điện thoại VN (các định dạng 09x, +84), CCCD (12 số), thẻ ngân hàng (16 số) thành `[REDACTED_...]`.
- **Cách kiểm chứng kết quả:** Chạy `scripts/validate_logs.py` đạt kết quả tuyệt đối **100/100**, 0 potential PII leaks, 100% bản ghi có đầy đủ metadata và correlation ID.

## 5. Tracing và prompt versioning

- **Cách xác nhận traces do chính tôi tạo trong project cá nhân:** Traces được đẩy trực tiếp lên project cá nhân `day13-k4-l3b-2A202602741` tại `https://us.cloud.langfuse.com` thông qua `LANGFUSE_PUBLIC_KEY` và `LANGFUSE_SECRET_KEY` riêng của tôi. Metadata của mỗi trace đều mang thông tin `session_id`, `user_id_hash`, `feature` và `correlation_id` của phiên làm việc.
- **Cấu trúc root/retrieval/generation observations:**
  ```text
  day13-agent-request
  └── lab-agent-run (as_type: agent)
      ├── retrieval (as_type: retriever)
      └── generation (as_type: generation, ghi nhận model, prompt, usage_details, cost_details)
  ```
- **Cách nối trace với log:** Gán `correlation_id` vào trace metadata trong `LabAgent.run` (`propagate_attributes(metadata={"correlation_id": correlation_id})`), giúp truy vết 1-1 giữa dòng log trong `data/logs.jsonl` và trace tương ứng trên giao diện Langfuse.
- **Prompt name:** `day13-chat`
- **Version/label baseline:** Version 3 gắn nhãn `baseline` và `production`.
- **Version/label candidate:** Version 4 gắn nhãn `candidate` (yêu cầu trả lời súc tích trong tối đa 3 gạch đầu dòng).
- **Trace ID của mỗi version:**
  - Baseline v1 (`day13-chat` v3): `46bf3cbe814fcddaaf758f544bacdc9d`
  - Candidate v2 (`day13-chat` v4): `7b58d91bb6b824f793119163cf98363f`
  - Trace `bb9438a2c3f6e93974a22c7ef7a71408` **không** chứng minh rollback: metadata thực tế vẫn ghi v4 `candidate`. Rollback nhãn `production` v4 → v3 được ghi ở `evidence/10a-prompt-before-rollback-live.png` và `evidence/10b-prompt-after-rollback-live.png`; chưa có trace request `production` v3 sau rollback.
- **Cách promote và rollback `production`:**
  - **Promote**: Chuyển nhãn `production` từ Version 3 sang Version 4 bằng `client.update_prompt(name="day13-chat", version=4, new_labels=["candidate", "production"])`.
  - **Rollback**: Khi kiểm thử hoàn tất hoặc phát hiện sự cố, chuyển nhãn `production` quay về Version 3 bằng `client.update_prompt(name="day13-chat", version=3, new_labels=["baseline", "production"])`.

## 6. Dashboard, SLO và alerts

- **Dashboard và sáu panel:** Dựng đủ 6 panel: Latency (P50/P95/P99, TTFT), Traffic (request/s theo thời gian), Errors (tổng số lỗi và retrieval success rate), Cost (chi phí USD), Tokens (tokens in/out), Quality (quality score proxy từ 0.0 - 1.0).
- **SLO và lý do chọn:** SLO là `99.5%` request thành công có `latency_ms <= 3000ms` trong chu kỳ 28 ngày (`28d`). Ngưỡng này đảm bảo trải nghiệm chat thời gian thực không bị gián đoạn và người dùng nhận câu trả lời trong vòng 3 giây.
- **Cách tính error budget:** Error budget là `0.5%` ($100\% - 99.5\%$). Trong cửa sổ 28 ngày với 10,000 requests, tối đa 50 request được phép không đạt SLO (bị lỗi hoặc latency > 3000ms).
- **Ba alert và runbook tương ứng:**
  1. `HighLatencyP95` (warning, 5m): Cảnh báo khi P95 latency vượt quá 3000ms; runbook kiểm tra dashboard latency -> lọc log theo correlation ID -> mở Langfuse trace để định vị span chậm -> rollback prompt hoặc kiểm tra retriever cache.
  2. `HighErrorRate` (critical, 3m): Cảnh báo khi tỷ lệ lỗi vượt quá 2%; runbook kiểm tra panel Errors -> lọc log `request_failed` -> mở trace xem span lỗi -> tắt incident / chuyển sang fallback model.
  3. `LowRetrievalSuccess` (warning, 5m): Cảnh báo khi retrieval success rate dưới 90%; runbook kiểm tra đồ thị retrieval -> lọc log `tool_success == false` -> kiểm tra dữ liệu vector database và nạp lại corpus.

## 7. Điều tra challenge

- **Challenge ID:** `day13-k4-l3b-monitoring-llmops-v1`
- **Khoảng thời gian điều tra:** `2026-09-30T04:49:14Z – 04:49:17Z` (11:49:14 – 11:49:17)
- **Triệu chứng từ metrics:** Latency P95 tăng vọt từ ~150ms lên **2651ms - 2652ms**, vượt xa ngưỡng quy định của challenge (`latency_threshold_ms: 2000`).
- **Log line và correlation ID liên quan:** Request có `correlation_id = req-e4c03882`, event `response_sent` lúc `04:49:16Z` ghi nhận `latency_ms = 2653`, `feature = monitoring`, `user_id_hash = 189d0a182d4e`.
- **Trace ID và span gây ảnh hưởng:** Trace ID `ed6ad56a243872c82fa683b09444f748` có cùng `correlation_id = req-e4c03882`. Trong waterfall, span `retrieval` mất khoảng 2.50s, còn `generation` khoảng 0.15s; trace ghi 147 tokens và $0.001629.
- **Root cause:** Kịch bản incident `rag_slow` được kích hoạt trên feature `monitoring`, gây trễ 2.5s tại bước tìm kiếm tài liệu từ vector store/retriever.
- **Fix action:** Thực hiện tắt incident qua lệnh `python scripts/inject_incident.py --disable`, cấu hình timeout 2s cho retrieval và thêm caching cho các truy vấn lặp lại.
- **Preventive measure:** Áp dụng alert rule `HighLatencyP95` (warning sau 5m), cấu hình circuit breaker/fallback ngắt sớm retriever nếu quá 2s để trả về câu trả lời tổng quát, đồng thời tách riêng panel đo `retrieval_latency`.

## 8. Giải thích và tự đánh giá

- **Một quyết định kỹ thuật quan trọng và lý do:** Quyết định thực hiện PII scrubbing tại tầng processor (`scrub_event`) trong chuỗi cấu hình `structlog.configure()` ngay trước khi ghi xuống file và render JSON. Cách làm này đảm bảo mọi chuỗi dữ liệu (payload, event, tóm tắt) đều được che sạch thông tin nhạy cảm trước khi thoát ra đĩa hoặc logging stream, tránh hoàn toàn nguy cơ rò rỉ PII do sơ suất ở tầng ứng dụng.
- **Một lỗi/blocker đã gặp:** Gặp lỗi `401 Unauthorized` khi kết nối Langfuse Cloud ban đầu do cấu hình host mặc định là `cloud.langfuse.com` (EU region), trong khi tài khoản được tạo tại data center US (`us.cloud.langfuse.com`). Ngoài ra, môi trường Windows PowerShell mặc định ưu tiên Python hệ thống hơn môi trường ảo `.venv`.
- **Cách tìm nguyên nhân và xử lý:** Kiểm tra chi tiết mã lỗi qua `client.auth_check()`, đối chiếu domain trên thanh địa chỉ trình duyệt, từ đó cập nhật `LANGFUSE_BASE_URL` sang `https://us.cloud.langfuse.com`. Đối với môi trường thực thi, sử dụng đường dẫn tường minh `.\.venv\Scripts\python.exe` để đảm bảo thực thi đúng packages trong môi trường ảo.
- **Cách hiểu luồng Metrics → Logs → Traces:** Metrics cung cấp cái nhìn tổng quan ở mức cao (high-level symptom) giúp phát hiện triệu chứng và khoảng thời gian xảy ra sự cố (ví dụ P95 latency tăng). Logs cung cấp ngữ cảnh chi tiết và mã `correlation_id` để khoanh vùng chính xác request nào của người dùng bị ảnh hưởng. Traces phân rã request thành các span con (`retrieval`, `generation`) giúp xác định chính xác bước nào là nguyên nhân gốc rễ (root cause) gây chậm hoặc lỗi.
- **Vai trò của prompt version, token/cost, SLO hoặc rollback trong vận hành LLM:** Prompt trực tiếp quyết định chất lượng, token tiêu thụ và độ trễ. Quản lý prompt theo version và label (`production`, `candidate`, `baseline`) cho phép thử nghiệm an toàn và thực hiện rollback tức thì về phiên bản ổn định trước đó mà không cần sửa code hay redeploy server khi phát hiện prompt mới gây suy giảm hiệu năng.
- **Điều quan trọng nhất đã học:** Nắm vững tư duy vận hành hệ thống AI production có khả năng quan sát (observability), biết cách bảo vệ dữ liệu người dùng (PII scrubbing) và quy trình điều tra sự cố chuẩn công nghiệp dựa trên chuỗi bằng chứng vững chắc Metric -> Log -> Trace.
- **Hạn chế hoặc phần chưa hoàn thành, nếu có:** Các panel dashboard hiện lấy nguồn từ file log JSONL cục bộ; trong tương lai có thể nâng cấp streaming log trực tiếp vào OpenTelemetry collector và Prometheus để hỗ trợ kiến trúc phân tán đa server.

## 9. Checklist trước khi nộp

- [ ] Kết quả và evidence thuộc commit SHA cuối.
- [ ] Tất cả ảnh/output mở được bằng đường dẫn tương đối.
- [ ] Có đúng 3 file text và 5 ảnh runtime theo hướng dẫn.
- [ ] Incident evidence nối đúng metric → log → trace.
- [ ] Trace/prompt evidence thuộc project Langfuse cá nhân và ảnh không lộ key/secret.
- [ ] Repository chạy lại được theo README.
- [ ] Không có secret, API key, PII thô hoặc evidence của người khác/lớp khác.
- [ ] URL repo và commit SHA cuối đã được nộp trên LMS/Codelabs.
