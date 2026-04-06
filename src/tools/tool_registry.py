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
        "description": "Tính giá: giảm giá ('22990000 discount 15%'), quy đổi tiền ('22990000 to usd'), hoặc biểu thức ('22990000 / 8')",
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
