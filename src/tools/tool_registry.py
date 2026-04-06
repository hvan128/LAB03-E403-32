"""Central registry of all available tools for the ReAct agent."""

from src.tools.calculator import calculator
from src.tools.product_search import product_search
from src.tools.product_compare import product_compare
from src.tools.price_calculator import price_calculator

TOOLS = [
    {
        "name": "product_search",
        "description": "Tìm kiếm sản phẩm theo tên hoặc loại (phone/laptop). Ví dụ: 'iPhone 15', 'laptop', 'samsung'",
        "arg_name": "query",
        "function": product_search,
    },
    {
        "name": "product_compare",
        "description": "So sánh 2 sản phẩm. Format: 'product1 vs product2'. Ví dụ: 'iPhone 15 vs Samsung S24'",
        "arg_name": "query",
        "function": product_compare,
    },
    {
        "name": "price_calculator",
        "description": (
            "Tính giá sản phẩm. Các format hỗ trợ:\n"
            "- Giảm giá: '34990000 discount 20%' → giá sau giảm\n"
            "- Trả góp: '34990000 installment 12 months 1.5%' → tiền/tháng\n"
            "- So sánh giá/hiệu năng: '15990000/8 vs 22990000/16' → cái nào rẻ hơn/đơn vị\n"
            "- Quy đổi tiền: '34990000 to usd' → đổi sang ngoại tệ\n"
            "- Biểu thức: '34990000 / 8' → tính toán tự do\n"
            "LƯU Ý: Nếu người dùng hỏi giá sản phẩm cụ thể (ví dụ 'iPhone 15 Pro Max discount 20%'), "
            "hãy dùng product_search TRƯỚC để lấy giá gốc, rồi mới gọi price_calculator với giá đó."
        ),
        "arg_name": "expression",
        "function": price_calculator,
    },
    {
        "name": "calculator",
        "description": "Tính toán biểu thức toán học. Hỗ trợ +, -, *, /, sqrt, pow, sin, cos, log.",
        "arg_name": "expression",
        "function": calculator,
    },
]
