# Template Alert và Runbook

Mỗi alert phải dựa trên triệu chứng người dùng hoặc SLO, không dựa trực tiếp vào tên implementation nội bộ.

## Alert mẫu để tham khảo

Ví dụ dưới đây minh họa mức độ cụ thể cần có. Học viên không cần copy nguyên, nhưng ba alert trong bài nộp nên rõ ràng tương tự: điều kiện là gì, kéo dài bao lâu, ảnh hưởng tới user ra sao và người trực cần kiểm tra gì trước.

- Tên: `HighLatencyP95`
- Severity: `warning`
- Duration: `5m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: latency P95 của `response_sent.latency_ms`
- Điều kiện và thời gian duy trì: `p95(latency_ms) > 3000ms` trong 5 phút
- Ảnh hưởng tới người dùng: người dùng phải chờ lâu hơn trước khi nhận câu trả lời
- Ba bước kiểm tra đầu tiên:
  1. Mở dashboard latency để xác nhận P95/P99 và khoảng thời gian tăng.
  2. Lọc `data/logs.jsonl` trong khoảng đó, lấy một `correlation_id` có `latency_ms` cao.
  3. Mở trace cùng `correlation_id` trên Langfuse, so sánh các span chính để xác định bước nào bất thường.
- Mitigation tạm thời: dựa trên evidence thực tế để rollback prompt, khôi phục cấu hình liên quan, tắt practice scenario hoặc giảm tải khi demo.
- Owner: `student-<MSSV>`

## Alert 1

- Tên: `HighLatencyP95`
- Severity: `warning`
- Duration: `5m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: `primary_slo.sli` (latency P95 của `response_sent.latency_ms <= 3000ms`)
- Điều kiện và thời gian duy trì: `p95(latency_ms) > 3000ms` duy trì trong 5 phút
- Ảnh hưởng tới người dùng: Người dùng phải chờ lâu hơn để nhận câu trả lời từ AI, gây suy giảm trải nghiệm
- Ba bước kiểm tra đầu tiên:
  1. Mở dashboard panel Latency để xác định khoảng thời gian bắt đầu tăng đột biến và kiểm tra TTFT.
  2. Lọc file `data/logs.jsonl` trong khung giờ đó, tìm các log `response_sent` có `latency_ms` cao bất thường và trích xuất `correlation_id`.
  3. Mở Langfuse Cloud, tìm trace có `correlation_id` đó, kiểm tra xem span nào bị nghẽn (retrieval chậm hay generation chậm do prompt quá dài).
- Mitigation tạm thời: Nếu do prompt mới bị dài hoặc làm chậm, thực hiện rollback prompt version về v1; nếu do vector store bị quá tải/chậm, khởi động lại service hoặc chuyển chế độ cache.
- Owner: `student-2A202602741`

## Alert 2

- Tên: `HighErrorRate`
- Severity: `critical`
- Duration: `3m`
- Kênh thông báo: Slack `#k4-l3b-critical`
- SLI/SLO liên quan: Guardrail `error_rate_pct_max: 2` (tỷ lệ lỗi request tối đa 2%)
- Điều kiện và thời gian duy trì: `error_rate_pct > 2%` duy trì trong 3 phút
- Ảnh hưởng tới người dùng: Người dùng bị gián đoạn dịch vụ, nhận lỗi HTTP 500 khi gửi tin nhắn chat
- Ba bước kiểm tra đầu tiên:
  1. Mở dashboard panel Errors để xem tổng số lỗi và tỷ lệ lỗi trên tổng request.
  2. Lọc file `data/logs.jsonl` tìm các event `request_failed`, ghi nhận `error_type` (ví dụ `RuntimeError`, `TimeoutError`) và `correlation_id`.
  3. Mở trace lỗi trên Langfuse theo `correlation_id`, kiểm tra span bị đánh dấu đỏ (ERROR) để xác định lỗi xuất phát từ tool nào.
- Mitigation tạm thời: Nếu do incident được bật (`tool_fail`), tắt incident hoặc chuyển sang fallback mechanism (trả lời dự phòng không dùng context RAG); thông báo sự cố cho đội vận hành.
- Owner: `student-2A202602741`

## Alert 3

- Tên: `LowRetrievalSuccess`
- Severity: `warning`
- Duration: `5m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: Guardrail `retrieval_success_rate_pct_min: 90` (tỷ lệ retrieval thành công tối thiểu 90%)
- Điều kiện và thời gian duy trì: `retrieval_success_rate_pct < 90%` duy trì trong 5 phút
- Ảnh hưởng tới người dùng: AI trả lời không có tài liệu/ngữ cảnh chính xác, dẫn đến chất lượng câu trả lời bị giảm hoặc hallucination
- Ba bước kiểm tra đầu tiên:
  1. Mở dashboard panel Errors để xem đồ thị `retrieval_success_rate` và panel Quality để xem điểm chất lượng (`quality_score`).
  2. Lọc log `data/logs.jsonl` tìm các event `response_sent` có `tool_success == false` hoặc `quality_score < 0.5`.
  3. Mở trace trên Langfuse, kiểm tra span `retrieval` để xem danh sách `docs` trả về rỗng hay vector search trả kết quả không khớp query.
- Mitigation tạm thời: Kiểm tra trạng thái vector database/corpus, khôi phục index tài liệu hoặc reload dữ liệu tri thức vào vector store.
- Owner: `student-2A202602741`
