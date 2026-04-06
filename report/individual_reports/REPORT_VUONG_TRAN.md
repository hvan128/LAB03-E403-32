# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Vương Trần Đình Minh
- **Student ID**: 2A202600495
- **Date**: 2026-04-06

---

## I. Technical Contribution (15 Points)

### Modules Implemented

- `src/tools/price_calculator.py`
- `scripts/analyze_logs.py`

### Code Highlights

**1. Tính trả góp (Installment)**

Format: `"22990000 installment 12 months 1.5%"`

```python
monthly_payment = price * monthly_rate * (1 + monthly_rate) ** months / ((1 + monthly_rate) ** months - 1)
total = monthly_payment * months
```

Output:
```
Price: 22,990,000đ
Term: 12 months @ 1.50%/month
Monthly payment: 2,107,723đ
Total paid: 25,292,676đ
Interest cost: 2,302,676đ
```

**2. So sánh giá/hiệu năng (Price vs Performance)**

Format: `"15990000/8 vs 22990000/16"`

```python
ratio1 = p1 / s1  # đ per unit
ratio2 = p2 / s2
better = "Product A" if ratio1 < ratio2 else "Product B"
```

Output:
```
Product A: 15,990,000đ / 8.0 = 1,998,750đ per unit
Product B: 22,990,000đ / 16.0 = 1,436,875đ per unit
Better value: Product B
```

**3. Tỷ giá realtime**

Thay thế dict cố định bằng API fetch realtime với cache 1 giờ và fallback:

```python
def get_exchange_rates() -> dict:
    url = "https://open.er-api.com/v6/latest/VND"
    # cache 1h, fallback về dict tĩnh nếu lỗi
```

**4. Metrics mở rộng trong `analyze_logs.py`**

- Cost breakdown theo provider
- Token ratio (prompt vs completion)
- Success rate theo loại câu hỏi (`question_type`)

**5. Metrics mở rộng trong `analyze_logs.py`**

- Cost breakdown theo provider
- Token ratio (prompt vs completion)
- Success rate theo loại câu hỏi (`question_type`)

### Documentation

`price_calculator` được đăng ký vào tool registry của ReAct agent. Khi agent nhận câu hỏi liên quan đến giá (trả góp, so sánh, quy đổi), nó sinh `Action: price_calculator(...)` → tool trả về kết quả → agent tổng hợp vào `Final Answer`.

---

## I.b Loop Count — Multi-step Reasoning (Steps)

`analyze_logs.py` thu thập `steps` từ các event `AGENT_V1_END` / `AGENT_V2_END` để đo số vòng Thought→Action mỗi lần chạy.

**Multi-step Reasoning**: Với câu hỏi đơn giản (discount, convert), agent thường giải quyết trong 1–2 steps. Câu hỏi phức tạp hơn (so sánh 2 sản phẩm + tính trả góp) cần 3–4 steps vì agent phải gọi `product_search` trước, rồi mới gọi `price_calculator`.

**Termination Quality**: Agent kết thúc đúng khi có đủ thông tin để trả lời (`Final Answer`). Trường hợp bị kẹt vòng lặp xảy ra khi tool trả về lỗi liên tục — agent lặp lại cùng Action mà không thay đổi query, dẫn đến `status: max_steps_exceeded`. `analyze_logs.py` track trường hợp này qua:

```python
if data.get("status") == "max_steps_exceeded":
    errors["timeout"] += 1
```

Output trong report:
```
--- Agent Steps ---
  Total agent runs: 12
  Avg steps: 2.8
  Max steps: 7
```

---

## I.c Failure Analysis (Error Codes)

`analyze_logs.py` phân loại 3 loại lỗi chính từ log events:

| Error | Event type | Nguyên nhân |
|-------|-----------|-------------|
| JSON Parser Error | `PARSE_ERROR` | LLM output `Action:` sai format, code không parse được |
| Hallucination Error | `HALLUCINATION` | LLM gọi tool không tồn tại trong registry |
| Timeout | `AGENT_V*_END` với `status: max_steps_exceeded` | Agent vượt quá `max_steps` |

**JSON Parser Error**: LLM đôi khi sinh ra `Action: search query` thay vì `Action: search("query")` → parser regex không match → log `PARSE_ERROR`.

**Hallucination Error**: LLM hallucinate tool như `Action: google_search(...)` hoặc `Action: calculator(...)` không có trong registry → agent nhận `Observation: Tool not found` → log `HALLUCINATION`.

**Timeout**: Thường xảy ra khi tool trả về kết quả rỗng hoặc lỗi liên tục, agent không thoát được vòng lặp Thought→Action.

```python
# Tracking trong analyze_logs.py
elif "PARSE_ERROR" in event_type:
    errors["parse_error"] += 1
elif "HALLUCINATION" in event_type:
    errors["hallucination"] += 1
```

Output:
```
--- Errors ---
  Parse errors: 3
  Hallucinations: 1
  Timeouts: 2
  Error rate: 50.0%
```

---

## II. Debugging Case Study (10 Points)

- **Problem Description**: Khi chạy `python streamlit_app.py` thay vì `streamlit run streamlit_app.py`, toàn bộ `st.*` calls bị gọi ngoài Streamlit context → hàng loạt warning `missing ScriptRunContext` và `session_state does not function`.
- **Log Source**: Terminal output `2026-04-06 15:11:46 WARNING ... missing ScriptRunContext`
- **Diagnosis**: Streamlit cần server riêng để quản lý session context. Chạy trực tiếp bằng Python interpreter bỏ qua bước khởi tạo này.
- **Solution**: Chạy đúng lệnh `streamlit run streamlit_app.py` hoặc `python -m streamlit run streamlit_app.py`.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

1. **Reasoning**: Block `Thought` giúp agent tự phân tích xem cần dùng tool nào trước khi hành động, thay vì trả lời ngay từ memory. Ví dụ: câu hỏi "so sánh MacBook M3 và Dell XPS về giá/hiệu năng" → agent biết cần gọi `product_search` rồi `price_calculator`, không đoán mò.

2. **Reliability**: Agent thực hiện kém hơn Chatbot khi câu hỏi đơn giản, không cần tool (ví dụ: "laptop nào phù hợp cho sinh viên?") — agent mất thêm latency cho các bước Thought/Action không cần thiết.

3. **Observation**: Observation từ tool trả về ảnh hưởng trực tiếp đến Thought tiếp theo. Nếu tool trả về lỗi hoặc kết quả rỗng, agent điều chỉnh query hoặc thử tool khác thay vì hallucinate.

---

## IV. Future Improvements (5 Points)

- **Scalability**: Dùng async tool calls để các tool độc lập (search + price) chạy song song, giảm latency.
- **Safety**: Thêm rate limit cho `get_exchange_rates()` và validate input trước khi `eval()` trong math expression fallback.
- **Performance**: Cache kết quả `product_search` theo query hash để tránh gọi API lặp lại trong cùng session.
