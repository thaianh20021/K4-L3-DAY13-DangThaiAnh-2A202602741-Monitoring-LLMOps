# Evidence cá nhân

## Trạng thái xác thực (2026-09-30)

Ảnh chụp trực tiếp: `02-trace-list.png`, `03-incident-trace.png`,
`05-dashboard-incident.png`, `06-trace-list.png`, `07-trace-waterfall.png`,
`08-trace-metadata.png`, `09-prompt-versions.png`, `10-prompt-rollback.png`,
`04-prompt-versioning.png`, `11-dashboard-overview.png`,
`12-incident-metric.png`, `14-incident-trace.png`.
`10a-prompt-before-rollback-live.png` và `10b-prompt-after-rollback-live.png`
ghi lại nhãn `production` chuyển từ v4 về v3. Dashboard là bản xem lại
60 phút kết thúc lúc 11:49, tính trực tiếp từ `data/logs.jsonl`.

**Chưa dùng để nộp:** `01-incident-log.png`
và các ảnh chi tiết `01`–`05`, `13` không có hậu tố `-live` là ảnh
dựng bằng script, không phải screenshot runtime. Riêng
`04-prompt-versioning.png`/`10-prompt-rollback.png` chỉ chụp trạng thái
sau rollback; phải xem thêm `10a` mới đủ hai mốc. Chưa có ảnh chụp log
`req-e4c03882` cùng trace `ed6ad56a243872c82fa683b09444f748`;
`13-incident-log.txt` là trích nguyên văn hai dòng từ `data/logs.jsonl`,
chưa thay thế được ảnh log bắt buộc.
Ba file `.txt` đã chạy lại từ log hiện có. Không coi bộ năm ảnh chính thức
là hoàn chỉnh cho tới khi thay ảnh 01 và ghép bố cục hai cửa sổ cho ảnh 04.

Thư mục còn chứa ảnh dựng cũ cần thay trước khi nộp theo hai tài liệu:
- Danh sách 5 ảnh runtime chính thức & 3 file text theo [docs/SUBMISSION.md](../../docs/SUBMISSION.md) và [submission/REPORT.md](../REPORT.md).
- Danh sách 14 ảnh chi tiết theo [docs/SCREENSHOT_GUIDE.md](../../docs/SCREENSHOT_GUIDE.md).

## 1. Evidence chính thức theo SUBMISSION.md (3 file text + 5 ảnh runtime)

### Ba output text:
- `pytest.txt`: Kết quả chạy `python -m pytest -q` (22/22 passed).
- `log-validator.txt`: Kết quả chạy `python scripts/validate_logs.py` (100/100).
- `dashboard-validator.txt`: Kết quả chạy `python scripts/validate_dashboard.py` (6/6 panels).

### Đúng năm ảnh runtime:
- `01-incident-log.png`: Ảnh dựng cũ; chưa có screenshot log cùng correlation ID với trace.
- `02-trace-list.png`: Danh sách traces trong project Langfuse cá nhân `day13-k4-l3b-2A202602741` (tương ứng mục 06).
- `03-incident-trace.png`: Chi tiết trace sự cố `ed6ad56a243872c82fa683b09444f748`, waterfall và metadata (tương ứng mục 07, 08 & 14).
- `04-prompt-versioning.png`: Ảnh thật sau rollback; dùng thêm hai ảnh `10a`/`10b` để kiểm tra nhãn trước/sau.
- `05-dashboard-incident.png`: Dashboard giám sát 6 panel và metric sự cố độ trễ tăng vọt (tương ứng mục 11 & 12).

---

## 2. Evidence chi tiết theo SCREENSHOT_GUIDE.md (14 ảnh)

- `01-pytest.png`: Terminal thực thi lệnh test unit & observability.
- `02-log-validator.png`: Terminal thực thi validator kiểm tra schema, metadata, correlation ID và PII scrubbing.
- `03-dashboard-validator.png`: Terminal kiểm tra hợp lệ contract 6/6 panel dashboard.
- `04-structured-log.png`: Cấu trúc JSON log có enrichment context và correlation ID.
- `05-pii-redaction.png`: Bằng chứng che giấu thông tin nhạy cảm Email, Phone VN, Credit Card (`[REDACTED_...]`).
- `06-trace-list.png`: Giao diện danh sách traces trong Langfuse project cá nhân.
- `07-trace-waterfall.png`: Biểu đồ quan hệ cha con Root request -> Agent -> Retrieval -> Generation.
- `08-trace-metadata.png`: Bảng metadata chi tiết của trace/observation (prompt, tokens, cost, correlation ID).
- `09-prompt-versions.png`: Giao diện quản lý các version và label (`baseline`, `production`, `candidate`).
- `10-prompt-rollback.png`: Bằng chứng luồng chuyển đổi nhãn prompt an toàn và trace ID tương ứng.
- `11-dashboard-overview.png`: Tổng thể dashboard 6 panel với đầy đủ metric, time range, ngưỡng threshold/SLO.
- `12-incident-metric.png`: Biểu đồ metric P95 latency tăng vọt 2652ms khi có incident `rag_slow`.
- `13-incident-log.png`: Ảnh dựng cũ, không khớp trace; cần chụp `req-e4c03882`, `latency_ms = 2653`.
- `14-incident-trace.png`: Trace đối ứng trên Langfuse chỉ ra span `retrieval` bị nghẽn 2501ms.
