"""
[Phan Thanh Sang] Tool tìm kiếm sản phẩm theo tên hoặc loại.

Database giả lập chứa thông tin điện thoại và laptop.
"""

# === PRODUCT DATABASE ===
# Sang: thêm/sửa sản phẩm tại đây
PRODUCT_DB = {
    "iphone 15": {
        "name": "iPhone 15",
        "category": "phone",
        "price_vnd": 22_990_000,
        "screen": "6.1 inch Super Retina XDR OLED",
        "chip": "A16 Bionic",
        "ram": "6GB",
        "storage": "128GB",
        "battery": "3349 mAh",
        "camera": "48MP + 12MP",
        "os": "iOS 17",
    },
    "iphone 15 pro max": {
        "name": "iPhone 15 Pro Max",
        "category": "phone",
        "price_vnd": 34_990_000,
        "screen": "6.7 inch Super Retina XDR OLED",
        "chip": "A17 Pro",
        "ram": "8GB",
        "storage": "256GB",
        "battery": "4441 mAh",
        "camera": "48MP + 12MP + 12MP",
        "os": "iOS 17",
    },
    "samsung s24": {
        "name": "Samsung Galaxy S24",
        "category": "phone",
        "price_vnd": 22_990_000,
        "screen": "6.2 inch Dynamic AMOLED 2X",
        "chip": "Snapdragon 8 Gen 3",
        "ram": "8GB",
        "storage": "128GB",
        "battery": "4000 mAh",
        "camera": "50MP + 12MP + 10MP",
        "os": "Android 14",
    },
    "samsung s24 ultra": {
        "name": "Samsung Galaxy S24 Ultra",
        "category": "phone",
        "price_vnd": 33_990_000,
        "screen": "6.8 inch Dynamic AMOLED 2X",
        "chip": "Snapdragon 8 Gen 3",
        "ram": "12GB",
        "storage": "256GB",
        "battery": "5000 mAh",
        "camera": "200MP + 50MP + 12MP + 10MP",
        "os": "Android 14",
    },
    "macbook air m2": {
        "name": "MacBook Air M2",
        "category": "laptop",
        "price_vnd": 27_990_000,
        "screen": "13.6 inch Liquid Retina",
        "chip": "Apple M2",
        "ram": "8GB",
        "storage": "256GB SSD",
        "battery": "18 hours",
        "os": "macOS Sonoma",
    },
    "macbook pro m3": {
        "name": "MacBook Pro M3",
        "category": "laptop",
        "price_vnd": 39_990_000,
        "screen": "14.2 inch Liquid Retina XDR",
        "chip": "Apple M3 Pro",
        "ram": "18GB",
        "storage": "512GB SSD",
        "battery": "17 hours",
        "os": "macOS Sonoma",
    },
    "dell xps 13": {
        "name": "Dell XPS 13",
        "category": "laptop",
        "price_vnd": 29_990_000,
        "screen": "13.4 inch FHD+ IPS",
        "chip": "Intel Core Ultra 7",
        "ram": "16GB",
        "storage": "512GB SSD",
        "battery": "13 hours",
        "os": "Windows 11",
    },
    "asus vivobook 15": {
        "name": "ASUS VivoBook 15",
        "category": "laptop",
        "price_vnd": 15_990_000,
        "screen": "15.6 inch FHD IPS",
        "chip": "Intel Core i5-1335U",
        "ram": "16GB",
        "storage": "512GB SSD",
        "battery": "8 hours",
        "os": "Windows 11",
    },
}


def product_search(query: str) -> str:
    """
    Tìm kiếm sản phẩm theo tên hoặc loại (phone/laptop).

    Args:
        query: Tên sản phẩm hoặc loại ("phone", "laptop"), ví dụ "iPhone 15", "laptop"
    Returns:
        Thông tin sản phẩm hoặc danh sách sản phẩm phù hợp.
    """
    query_lower = query.strip().lower()

    # TODO [Sang]: Cải tiến logic tìm kiếm nếu cần
    # - Thêm filter theo giá (dưới X triệu)
    # - Thêm filter theo RAM
    # - Fuzzy matching

    # Tìm chính xác theo tên
    if query_lower in PRODUCT_DB:
        p = PRODUCT_DB[query_lower]
        return _format_product(p)

    # Tìm theo category
    if query_lower in ("phone", "laptop"):
        matches = [p for p in PRODUCT_DB.values() if p["category"] == query_lower]
        if matches:
            return "Found products:\n" + "\n".join(
                f"- {p['name']}: {p['price_vnd']:,}đ" for p in matches
            )

    # Tìm theo từ khóa
    matches = []
    for key, p in PRODUCT_DB.items():
        if query_lower in key or query_lower in p["name"].lower():
            matches.append(p)

    if matches:
        if len(matches) == 1:
            return _format_product(matches[0])
        return "Found products:\n" + "\n".join(
            f"- {p['name']}: {p['price_vnd']:,}đ" for p in matches
        )

    return f"No products found for '{query}'. Available: {', '.join(p['name'] for p in PRODUCT_DB.values())}"


def _format_product(p: dict) -> str:
    lines = [f"{p['name']} ({p['category']})"]
    for key, val in p.items():
        if key not in ("name", "category"):
            label = key.replace("_", " ").replace("vnd", "(VND)").title()
            lines.append(f"  {label}: {val:,}" if isinstance(val, int) else f"  {label}: {val}")
    return "\n".join(lines)
