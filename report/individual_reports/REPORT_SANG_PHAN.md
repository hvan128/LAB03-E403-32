# Báo cáo Cá nhân: Lab 3 - Chatbot vs ReAct Agent

- **Họ và tên**: `Phan Thanh Sang`
- **Mã số sinh viên**: `2A202600280`
- **Ngày**: `2026-04-06`

---

## I. Đóng góp kỹ thuật (15 điểm)

Phần đóng góp chính của em tập trung vào **lớp tool và guardrail** cho trợ lý so sánh sản phẩm. Mục tiêu của phần này là giúp ReAct agent trả lời dựa trên dữ liệu sản phẩm có cấu trúc thay vì chỉ sinh câu trả lời chung chung từ LLM.

- **Các module đã triển khai / cải thiện**:
  - `src/tools/product_search.py`
  - `src/tools/product_compare.py`
  - `src/tools/calculator.py`
  - `src/core/scope_guard.py`
  - `tests/test_tools.py`
  - `tests/test_scope_guard.py`

- **Điểm nổi bật trong phần code**:

  1. Xây dựng một cơ sở dữ liệu
  2. Cài đặt `product_search` với tìm kiếm chính xác theo tên, theo loại và theo từ khóa
  3. Cài đặt `product_compare` để so sánh hai sản phẩm theo giá và thông số kỹ thuật
  4. Thêm `price_calculator` và `calculator` để agent có thể tính giảm giá, đổi tiền tệ và xử lý phép toán đơn giản
  5. Thêm bộ lọc phạm vi để chặn các câu hỏi không liên quan như chiến sự, tin tức, thời tiết

- **Giải thích cách phần code tương tác với ReAct loop**:
  Các tool này được đăng ký trong `src/tools/tool_registry.py` và được sử dụng bởi cả `ReActAgent` và `ReActAgentV2`. Trong quá trình chạy, agent tạo ra `Thought`, chọn `Action`, gọi một tool tương ứng, nhận `Observation` từ môi trường rồi mới đưa ra `Final Answer` có căn cứ hơn.

---

## II. Case study gỡ lỗi (10 điểm)

### Mô tả vấn đề
Một lỗi đáng chú ý mà em gặp là hệ thống vẫn có thể trả lời các câu hỏi nằm ngoài phạm vi bài toán, ví dụ:

```text
"tình hình chiến sự ở Iran hiện tại"
```

Điều này không phù hợp vì project được thiết kế như một **trợ lý mua sắm / so sánh sản phẩm**, không phải chatbot tin tức tổng quát.

### Nguồn log
Dấu hiệu của lỗi này xuất hiện trong `logs/2026-04-06.log`, nơi một số lần chạy trước đó cho thấy mô hình vẫn trả lời các câu hỏi ngoài chủ đề. Ngoài ra còn có các sự kiện `AGENT_V2_PARSE_ERROR` khi mô hình trả lời theo kiểu hội thoại thông thường thay vì đúng format `Action: tool_name(argument)`.

### Chẩn đoán
Nguyên nhân gốc rễ gồm ba phần chính:
1. **Prompt còn quá rộng** — system prompt vẫn khiến mô hình cư xử như một trợ lý tổng quát
2. **Chưa có domain gate rõ ràng** trước khi gọi LLM
3. **Hành vi hội thoại mặc định** của mô hình khi gặp lời chào hoặc câu hỏi thời sự

### Cách khắc phục
Em xử lý vấn đề theo hai lớp:
- Thêm **ràng buộc ở mức prompt** để trợ lý chỉ xử lý các câu hỏi về tìm kiếm, so sánh và tính giá sản phẩm
- Thêm **bộ lọc ở mức code** trong `src/core/scope_guard.py` để từ chối truy vấn ngoài phạm vi trước khi gọi tới mô hình

Sau khi sửa, hệ thống phản hồi theo hướng từ chối lịch sự như sau:

```text
Xin lỗi, tôi chỉ hỗ trợ các câu hỏi về tìm kiếm, so sánh sản phẩm và tính giá...
```

Ngoài ra em cũng bổ sung test hồi quy trong `tests/test_scope_guard.py` để đảm bảo lỗi này không tái diễn.

---

## III. Nhận xét cá nhân: Chatbot vs ReAct (10 điểm)

1. **Reasoning**
   Khối `Thought` giúp agent xử lý tốt hơn các bài toán nhiều bước vì nó buộc hệ thống phải chia nhỏ vấn đề trước khi hành động. Ví dụ với câu hỏi giảm giá, agent trước tiên phải tìm giá sản phẩm rồi mới gọi công cụ tính toán. Trong khi đó chatbot thường bỏ qua các bước này và trả lời một cách ước lượng hoặc mang tính suy đoán.

2. **Reliability**
   Agent vẫn có thể kém hơn chatbot trong các trường hợp prompt mơ hồ, LLM sinh ra action sai format hoặc số bước suy luận quá nhiều. Khi đó agent vừa tốn nhiều token hơn, vừa có độ trễ cao hơn so với chatbot thông thường.

3. **Observation**
   `Observation` là khác biệt quan trọng nhất giữa ReAct agent và chatbot thường. Nó giúp agent dựa vào phản hồi thực từ môi trường / tool để ra quyết định tiếp theo. Khi đã có giá sản phẩm hoặc bảng so sánh thật, agent có thể tạo ra câu trả lời cuối chính xác hơn thay vì chỉ dựa vào trí nhớ của mô hình.

---

## IV. Hướng cải tiến trong tương lai (5 điểm)

Nếu mở rộng hệ thống này lên mức production cao hơn, em sẽ cải thiện theo các hướng sau:

- **Scalability**: Thay cơ sở dữ liệu sản phẩm cục bộ bằng API hoặc database thật và thêm cache cho các truy vấn phổ biến để giảm độ trễ
- **Safety**: Tăng cường kiểm tra đối số đầu vào, thêm lớp supervisor và siết chặt allowlist cho tool call
- **Performance**: Thêm cơ chế gọi tool bất đồng bộ, streaming response và telemetry chi tiết hơn như TTFT thật và breakdown độ trễ theo từng tool

---

## V. Khai báo việc sử dụng AI hỗ trợ

Trong quá trình thực hiện bài lab, em có sử dụng **AI hỗ trợ** ở một số khâu, nhưng luôn có bước kiểm tra và chỉnh sửa thủ công trước khi đưa vào sản phẩm cuối cùng.

- **Các phần có sử dụng AI hỗ trợ**:
  - gợi ý ý tưởng tổ chức prompt và flow cho ReAct agent
  - hỗ trợ giải thích lỗi / phân tích log khi agent parse sai hoặc trả lời ngoài phạm vi
  - hỗ trợ diễn đạt lại một số đoạn mô tả trong báo cáo để rõ ràng và mạch lạc hơn

- **Các phần em trực tiếp thực hiện và kiểm chứng**:
  - thiết kế và cài đặt tool `product_search`, `product_compare`, `calculator`
  - viết test cho tool và test chặn câu hỏi ngoài phạm vi
  - chạy kiểm thử, đọc log, sửa lỗi và đối chiếu kết quả benchmark
  - rà soát lại nội dung báo cáo để phù hợp với đúng mã nguồn và kết quả thực tế

- **Cam kết học thuật**:
  AI chỉ đóng vai trò **hỗ trợ**, không thay thế cho việc hiểu bài, viết code, kiểm thử và phân tích kỹ thuật của cá nhân em.
