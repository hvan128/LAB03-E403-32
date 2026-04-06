# Phân công Task — Trợ lý So sánh Sản phẩm

## Cách làm việc song song
- Mọi người pull code từ `main`, **mỗi người chỉ sửa file của mình** (đã đánh dấu tên)
- Không ai sửa file của người khác → không conflict
- Xong thì commit & push lên `main`

---

## Ngô Hải Văn — Agent v2 + Main Runner + Group Report

### Files phụ trách:
- `src/agent/agent_v2.py` — cải tiến Agent v2
- `main.py` — đã sẵn, chỉnh test cases nếu cần
- `report/group_report/` — viết group report

### Việc cần làm:
1. Chạy `python3 main.py --compare` để test
2. Xem logs, phân tích kết quả
3. Cải tiến agent_v2 nếu cần (prompt, parsing)
4. Viết Group Report theo template
5. Viết Individual Report

---

## Phan Thanh Sang — Tools (product_search + product_compare)

### Files phụ trách:
- `src/tools/product_search.py` — tìm kiếm sản phẩm ← **có TODO**
- `src/tools/product_compare.py` — so sánh sản phẩm ← **có TODO**
- `tests/test_tools.py` — thêm test cases

### Việc cần làm:
1. Mở rộng `PRODUCT_DB` — thêm sản phẩm (Xiaomi, Oppo, Lenovo...)
2. Cải tiến search: filter theo giá, RAM, fuzzy matching
3. Cải tiến compare: highlight sản phẩm thắng, thêm tổng điểm
4. Thêm test cases vào `tests/test_tools.py`
5. Viết Individual Report

### Test:
```bash
python3 -m pytest tests/test_tools.py -v
```

---

## Đỗ Minh Hiếu — Agent v1 + Chatbot + Flowchart

### Files phụ trách:
- `src/agent/agent.py` — Agent v1
- `src/chatbot/chatbot.py` — Chatbot baseline
- Flowchart diagram (đặt trong `report/group_report/`)

### Việc cần làm:
1. Chạy thử Agent v1: `python3 main.py --query "So sánh iPhone 15 và Samsung S24"`
2. Ghi nhận các lỗi v1 gặp (parse error, hallucination, loop)
3. Cải tiến chatbot system prompt cho ngữ cảnh sản phẩm
4. Vẽ Flowchart: Chatbot vs Agent v1 vs Agent v2 (dùng draw.io hoặc Mermaid)
5. Viết Individual Report

---

## Vương Trần — Telemetry + Evaluation + price_calculator

### Files phụ trách:
- `src/tools/price_calculator.py` — tính giá ← **có TODO**
- `src/telemetry/metrics.py` — cải tiến metrics
- `scripts/analyze_logs.py` — phân tích logs ← **có TODO**

### Việc cần làm:
1. Mở rộng price_calculator: thêm tính trả góp, so sánh giá/hiệu năng
2. Cập nhật tỷ giá trong `EXCHANGE_RATES`
3. Cải tiến `metrics.py`: thêm cost thực tế theo model (GPT-4o pricing)
4. Cải tiến `analyze_logs.py`: thêm metrics, xuất bảng so sánh Chatbot vs Agent
5. Chạy analysis sau khi team chạy `--compare`
6. Viết Individual Report

### Test:
```bash
python3 main.py --compare
python3 scripts/analyze_logs.py
```

---

## Thứ tự chạy
1. `pip3 install -r requirements.txt`
2. Đảm bảo `.env` có API key
3. Mỗi người sửa file của mình
4. `python3 main.py --compare` → xem kết quả
5. `python3 scripts/analyze_logs.py` → xem metrics
6. `python3 -m pytest tests/ -v` → chạy test
