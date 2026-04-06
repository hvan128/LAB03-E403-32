"""
[Phan Thanh Sang] Tool so sánh 2 sản phẩm theo specs.

Nhận input dạng "product1 vs product2", trả về bảng so sánh.
"""

from src.tools.product_search import PRODUCT_DB


def product_compare(query: str) -> str:
    """
    So sánh 2 sản phẩm. Input format: "product1 vs product2"

    Args:
        query: Hai tên sản phẩm cách nhau bởi "vs", ví dụ "iPhone 15 vs Samsung S24"
    Returns:
        Bảng so sánh specs của 2 sản phẩm.
    """
    # TODO [Sang]: Cải tiến nếu cần
    # - Thêm highlight sản phẩm thắng ở mỗi tiêu chí
    # - Thêm tổng điểm đánh giá

    parts = [p.strip().lower() for p in query.split("vs")]
    if len(parts) != 2:
        return "Error: Please use format 'product1 vs product2'. Example: 'iPhone 15 vs Samsung S24'"

    name1, name2 = parts[0], parts[1]

    p1 = _find_product(name1)
    p2 = _find_product(name2)

    if not p1:
        return f"Product '{name1}' not found. Available: {', '.join(p['name'] for p in PRODUCT_DB.values())}"
    if not p2:
        return f"Product '{name2}' not found. Available: {', '.join(p['name'] for p in PRODUCT_DB.values())}"

    # Build comparison
    all_keys = []
    for key in list(p1.keys()) + list(p2.keys()):
        if key not in all_keys and key != "category":
            all_keys.append(key)

    lines = [f"=== {p1['name']} vs {p2['name']} ==="]
    for key in all_keys:
        label = key.replace("_", " ").replace("vnd", "(VND)").title()
        v1 = p1.get(key, "N/A")
        v2 = p2.get(key, "N/A")
        v1_str = f"{v1:,}" if isinstance(v1, int) else str(v1)
        v2_str = f"{v2:,}" if isinstance(v2, int) else str(v2)
        lines.append(f"  {label}: {v1_str} | {v2_str}")

    return "\n".join(lines)


def _find_product(name: str):
    """Tìm sản phẩm theo tên (fuzzy)."""
    name = name.strip().lower()
    if name in PRODUCT_DB:
        return PRODUCT_DB[name]
    for key, p in PRODUCT_DB.items():
        if name in key or name in p["name"].lower():
            return p
    return None
