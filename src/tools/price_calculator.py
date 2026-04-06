"""
[Vương Trần] Tool tính giá sản phẩm: giảm giá, quy đổi tiền, giá/hiệu năng.

Hỗ trợ các phép tính:
- discount: "22990000 discount 15%" → giá sau giảm
- convert: "22990000 to usd" → quy đổi sang USD
- expression: "22990000 / 8" → tính giá/GB RAM, v.v.
"""

# TODO [Vương Trần]: Cập nhật tỷ giá nếu cần
EXCHANGE_RATES = {
    "usd": 25_000,
    "eur": 27_000,
    "jpy": 170,
    "krw": 19,
}


def price_calculator(expression: str) -> str:
    """
    Tính giá sản phẩm: giảm giá, quy đổi tiền, hoặc biểu thức toán.

    Args:
        expression: Một trong các format:
            - "22990000 discount 15%" → tính giá sau giảm
            - "22990000 to usd" → quy đổi tiền tệ
            - "22990000 / 8" → biểu thức toán (giá/RAM, v.v.)
    Returns:
        Kết quả tính toán.
    """
    expr = expression.strip().lower()

    # TODO [Vương Trần]: Thêm các phép tính khác nếu cần
    # - So sánh giá/hiệu năng 2 sản phẩm
    # - Tính trả góp

    # --- Discount ---
    if "discount" in expr:
        try:
            parts = expr.split("discount")
            price = float(parts[0].strip().replace(",", ""))
            percent = float(parts[1].strip().replace("%", ""))
            discounted = price * (1 - percent / 100)
            saved = price - discounted
            return (
                f"Original: {price:,.0f}đ\n"
                f"Discount: {percent}%\n"
                f"After discount: {discounted:,.0f}đ\n"
                f"You save: {saved:,.0f}đ"
            )
        except Exception as e:
            return f"Error calculating discount: {e}"

    # --- Currency conversion ---
    if " to " in expr:
        try:
            parts = expr.split(" to ")
            price = float(parts[0].strip().replace(",", ""))
            currency = parts[1].strip()
            rate = EXCHANGE_RATES.get(currency)
            if not rate:
                return f"Unknown currency '{currency}'. Available: {', '.join(EXCHANGE_RATES.keys())}"
            converted = price / rate
            return f"{price:,.0f} VND = {converted:,.2f} {currency.upper()} (rate: 1 {currency.upper()} = {rate:,} VND)"
        except Exception as e:
            return f"Error converting currency: {e}"

    # --- Math expression fallback ---
    try:
        result = eval(expression, {"__builtins__": {}}, {})
        if isinstance(result, float):
            return f"{result:,.2f}"
        return str(result)
    except Exception as e:
        return f"Error: {e}. Use format: '22990000 discount 15%' or '22990000 to usd' or '22990000 / 8'"
