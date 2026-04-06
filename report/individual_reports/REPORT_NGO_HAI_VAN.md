# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Ngo Hai Van
- **Student ID**: [Your ID Here]
- **Date**: 2026-04-06

---

## I. Technical Contribution (15 Points)

*Mô tả đóng góp cụ thể vào codebase.*

### 1. Khởi tạo toàn bộ kiến trúc hệ thống (commit `f62b7ba`)

Thiết kế và triển khai toàn bộ codebase ban đầu gồm 30 files, 1414 dòng code:

- **Modules Implemented**:
  - `src/chatbot/chatbot.py` — Chatbot Baseline: gọi LLM đơn giản, không tools, không reasoning loop
  - `src/agent/agent.py` — ReAct Agent V1: vòng lặp Thought-Action-Observation với max 5 steps
  - `src/agent/agent_v2.py` — ReAct Agent V2: cải tiến với few-shot examples, hallucination guardrails (kiểm tra tool tồn tại trước khi gọi), retry logic (max 2 retries cho parse error)
  - `src/core/llm_provider.py`, `src/core/openai_provider.py`, `src/core/gemini_provider.py`, `src/core/local_provider.py` — LLM Provider abstraction layer hỗ trợ đa mô hình
  - `src/tools/calculator.py`, `src/tools/weather.py`, `src/tools/search.py` — 3 tools ban đầu
  - `src/telemetry/logger.py`, `src/telemetry/metrics.py` — Hệ thống logging và tracking metrics (tokens, latency, cost)
  - `main.py` — Runner chính với 3 modes: interactive, comparison, single query

- **Code Highlights**:

  Agent V2 hallucination guardrail (`src/agent/agent_v2.py:182-197`):
  ```python
  # Guardrail: hallucinated tool
  if tool_name not in self.tools:
      self._emit({
          "type": "error", "step": steps,
          "error_type": "hallucination",
          "content": f"Hallucinated tool: {tool_name}",
      }, on_step)
      history.append(
          f"Observation: ERROR — Tool '{tool_name}' does not exist.\n"
          f"Available tools: {', '.join(self.tools.keys())}.\n"
          f"Please choose one of the available tools."
      )
      continue
  ```

  Agent V2 parse retry logic (`src/agent/agent_v2.py:145-177`):
  ```python
  if not action_match:
      parse_retries += 1
      if parse_retries > self.max_parse_retries:
          return "I encountered repeated formatting errors..."
      history.append(
          f"Observation: FORMAT ERROR — Your response did not contain a valid Action.\n"
          f"Remember: use exactly this format:\nThought: <reasoning>\nAction: tool_name(argument)\n"
          f"Available tools: {', '.join(self.tools.keys())}"
      )
      continue
  ```

### 2. Thiết lập Product Comparison Assistant (commit `ced0f94`)

Mở rộng hệ thống với 3 tools mới cho use case so sánh sản phẩm, tổng cộng 666 dòng code mới:

- **Modules Implemented**:
  - `src/tools/product_search.py` — Tìm kiếm sản phẩm theo tên/category (phone, laptop, tablet) với database tĩnh gồm 10 sản phẩm
  - `src/tools/product_compare.py` — So sánh chi tiết 2 sản phẩm (specs, giá, rating)
  - `src/tools/price_calculator.py` — Tính giá với discount, quy đổi tiền tệ (VND/USD)
  - `src/tools/tool_registry.py` — Registry pattern để quản lý và đăng ký tools
  - `scripts/analyze_logs.py` — Script phân tích log files
  - `tests/test_tools.py` — 13 test cases cho các tools
  - `TASK_ASSIGNMENT.md` — Phân chia task cho từng thành viên

### 3. Realtime Flowchart & UI cho ReAct Visualization (commit `bf170ca`)

Cải tiến lớn nhất về UI, 516 dòng code mới/sửa đổi:

- **Modules Implemented**:
  - `streamlit_app.py` — Giao diện Streamlit với layout 2 cột: Chat (trái) + Flowchart (phải)
  - `src/agent/agent.py` & `src/agent/agent_v2.py` — Thêm `on_step` callback cho realtime trace streaming

- **Key Features**:
  - Flowchart cập nhật **realtime** khi agent xử lý từng step (không đợi kết thúc)
  - Hiển thị trực quan: Thought (xanh dương), Action (tím), Observation (xám), Error (cam), Final Answer (xanh lá)
  - Hỗ trợ light/dark mode
  - Hiển thị loop count trên Final Answer node

---

## II. Debugging Case Study (10 Points)

*Phân tích sự cố cụ thể gặp phải trong quá trình phát triển.*

### Problem: Agent V1 parse lỗi khi tool argument có dấu ngoặc kép

- **Problem Description**: Agent V1 sử dụng regex `(\w+)\((.+?)\)` để parse action. Khi LLM trả về `Action: product_search("iPhone 15")` với dấu ngoặc kép bao quanh argument, regex vẫn match nhưng argument bao gồm cả dấu `"`, dẫn đến tool không tìm thấy sản phẩm.

- **Log Source** (`logs/2026-04-06.log`, line 36):
  ```json
  {"event": "AGENT_V1_STEP", "data": {"step": 1, "llm_output": "...Action: product_search(\"iPhone 15\")"}}
  ```
  Agent V1 vẫn trả kết quả đúng ở đây vì `product_search` xử lý strip quotes bên trong, nhưng đây là điểm yếu thiết kế.

- **Diagnosis**: LLM (GPT-4o) không nhất quán trong format output — đôi khi có quotes, đôi khi không. V1 chỉ dùng `strip("\"'")` sau khi match, nhưng regex không xử lý whitespace trước/sau quotes.

- **Solution trong V2** (`src/agent/agent_v2.py:141-143`):
  ```python
  # V2: regex cải tiến xử lý quotes + whitespace
  action_match = re.search(
      r"Action:\s*(\w+)\(\s*[\"']?(.*?)[\"']?\s*\)", content, re.DOTALL,
  )
  ```
  V2 dùng regex mạnh hơn với `[\"']?` optional quotes và `\s*` whitespace, cùng flag `re.DOTALL` cho multi-line content. Kết hợp với few-shot example trong system prompt giúp LLM output đúng format hơn.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

### 1. Reasoning: Thought block giúp Agent như thế nào?

Từ log so sánh query "So sánh iPhone 15 và Samsung Galaxy S24":

- **Chatbot** (line 65-67): Trả lời ngay lập tức (4622ms) dựa trên kiến thức training data — thông tin có thể không chính xác hoặc outdated. Không có cách verify.
- **Agent V1** (line 68-74): Thought block "I need to use the product_compare tool" → gọi `product_compare(iPhone 15 vs Samsung Galaxy S24)` → trả lời dựa trên data thực. 2 steps, 4877ms.
- **Agent V2** (line 75-80): Tương tự V1 nhưng nhanh hơn (3515ms) nhờ few-shot examples giúp LLM output đúng format ngay từ step 1.

**Kết luận**: Thought block cho phép agent **phân tách bài toán** thành sub-tasks và **quyết định tool nào cần gọi**, thay vì "đoán" câu trả lời. Điều này đặc biệt quan trọng khi cần data chính xác (giá, specs).

### 2. Reliability: Khi nào Agent hoạt động tệ hơn Chatbot?

- **Câu hỏi đơn giản/chung chung**: Chatbot nhanh hơn và tiết kiệm token hơn. Ví dụ với query "iPhone 15 có những thông số gì?" — Chatbot dùng 252 tokens (2713ms), Agent V2 dùng 1243 tokens (2445ms). Agent dùng gấp ~5x tokens cho kết quả tương đương.
- **Câu hỏi nằm ngoài scope tools**: Nếu hỏi "Tại sao iPhone 15 tốt hơn cho chụp ảnh?" — Agent vẫn cố gọi tool nhưng tool chỉ trả specs, không đưa ra opinion. Chatbot có thể reasoning tốt hơn cho câu hỏi chủ quan.
- **Cost**: Agent V2 luôn tốn nhiều tokens hơn do system prompt dài (có few-shot examples) + nhiều LLM calls.

### 3. Observation: Feedback từ môi trường ảnh hưởng như thế nào?

Observation (kết quả tool call) đóng vai trò **grounding** cho agent:

- Khi `product_search(laptop)` trả về danh sách 4 laptop với giá cụ thể, agent dùng chính xác data đó thay vì hallucinate thông tin.
- Khi `product_compare(iPhone 15 vs Samsung Galaxy S24)` trả về bảng so sánh, agent tổng hợp và format lại thông tin — không thêm specs sai.
- Error observations (parse error, tool not found) giúp agent tự điều chỉnh — đặc biệt hiệu quả ở V2 với guided re-prompt kèm danh sách tools khả dụng.

---

## IV. Future Improvements (5 Points)

### Scalability
- **Async tool execution**: Hiện tại agent gọi tool tuần tự. Với nhiều tools independent (ví dụ: search iPhone 15 + search Galaxy S24 cùng lúc), có thể dùng `asyncio` để gọi song song, giảm latency.
- **Tool retrieval with vector DB**: Khi số lượng tools lớn (50+), thay vì liệt kê tất cả trong system prompt (tốn tokens), dùng semantic search trên tool descriptions để chọn top-k tools relevant nhất cho query.

### Safety
- **Supervisor LLM**: Thêm một LLM layer kiểm tra output trước khi trả cho user — phát hiện thông tin sai, nội dung không phù hợp.
- **Tool call validation**: Thêm schema validation cho tool arguments (hiện tại chỉ là string). Ví dụ `price_calculator` nên validate input là số hợp lệ trước khi tính toán.
- **Rate limiting**: Giới hạn số tool calls per session để tránh abuse hoặc infinite loop tốn cost.

### Performance
- **Caching layer**: Cache kết quả tool calls cho các query giống nhau (ví dụ `product_search(iPhone 15)` không thay đổi trong session). Giảm latency và API cost.
- **Streaming response**: Thay vì đợi agent hoàn thành tất cả steps, stream partial results cho user (đã implement phần nào với realtime flowchart, nhưng chưa stream text response).
- **Model routing**: Dùng model nhỏ/rẻ (GPT-4o-mini) cho các step đơn giản (parse action), model lớn (GPT-4o) cho reasoning phức tạp và final answer.

---

> [!NOTE]
> Report by Ngo Hai Van — Lab 3: Chatbot vs ReAct Agent
