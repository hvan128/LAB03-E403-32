"""
[Vương Trần] Tool tính giá sản phẩm: giảm giá, quy đổi tiền, giá/hiệu năng.

Hỗ trợ các phép tính:
- discount: "22990000 discount 15%" → giá sau giảm
- convert: "22990000 to usd" → quy đổi sang USD
- expression: "22990000 / 8" → tính giá/GB RAM, v.v.
"""

import urllib.request
import json
import time

# Fallback nếu không fetch được
_FALLBACK_RATES = {
    "usd": 25_400,
    "eur": 27_800,
    "jpy": 165,
    "krw": 18,
    "gbp": 32_000,
    "cny": 3_500,
}

_rate_cache = {"rates": None, "ts": 0}
_CACHE_TTL = 3600  # 1 giờ


def get_exchange_rates() -> dict:
    """Lấy tỷ giá VND realtime từ exchangerate-api.com (free, no key)."""
    now = time.time()
    if _rate_cache["rates"] and now - _rate_cache["ts"] < _CACHE_TTL:
        return _rate_cache["rates"]
    try:
        url = "https://open.er-api.com/v6/latest/VND"
        with urllib.request.urlopen(url, timeout=5) as resp:
            data = json.loads(resp.read())
        if data.get("result") != "success":
            raise ValueError("API error")
        raw = data["rates"]  # raw[currency] = số đơn vị ngoại tệ / 1 VND
        # Đổi thành: 1 ngoại tệ = ? VND
        rates = {k.lower(): round(1 / v) for k, v in raw.items() if v > 0}
        _rate_cache["rates"] = rates
        _rate_cache["ts"] = now
        return rates
    except Exception:
        return {k: v for k, v in _FALLBACK_RATES.items()}


EXCHANGE_RATES = _FALLBACK_RATES  # dùng khi import tĩnh, runtime dùng get_exchange_rates()


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

    # --- Installment (trả góp) ---
    # Format: "22990000 installment 12 months 1.5%"
    if "installment" in expr:
        try:
            parts = expr.split("installment")
            price = float(parts[0].strip().replace(",", ""))
            rest = parts[1].strip()
            tokens = rest.split()
            months = int(tokens[0])
            monthly_rate = float(tokens[2].replace("%", "")) / 100 if len(tokens) >= 3 else 0.0
            if monthly_rate == 0:
                monthly_payment = price / months
                total = price
            else:
                monthly_payment = price * monthly_rate * (1 + monthly_rate) ** months / ((1 + monthly_rate) ** months - 1)
                total = monthly_payment * months
            return (
                f"Price: {price:,.0f}đ\n"
                f"Term: {months} months @ {monthly_rate*100:.2f}%/month\n"
                f"Monthly payment: {monthly_payment:,.0f}đ\n"
                f"Total paid: {total:,.0f}đ\n"
                f"Interest cost: {total - price:,.0f}đ"
            )
        except Exception as e:
            return f"Error calculating installment: {e}. Format: '22990000 installment 12 months 1.5%'"

    # --- Compare price/performance ---
    # Format: "15990000/8 vs 22990000/16"  (price/score vs price/score)
    # hoặc: "15990000 vs 22990000" (chỉ so sánh giá)
    if " vs " in expr:
        try:
            parts = expr.split(" vs ")
            def parse_ratio(s):
                s = s.strip().replace(",", "")
                if "/" in s:
                    a, b = s.split("/", 1)
                    return float(a), float(b)
                # Không có score → chỉ so sánh giá thuần
                return float(s), None
            p1, s1 = parse_ratio(parts[0])
            p2, s2 = parse_ratio(parts[1])
            if s1 is not None and s2 is not None:
                ratio1 = p1 / s1
                ratio2 = p2 / s2
                better = "Product A" if ratio1 < ratio2 else "Product B"
                return (
                    f"Product A: {p1:,.0f}đ / {s1} = {ratio1:,.0f}đ per unit\n"
                    f"Product B: {p2:,.0f}đ / {s2} = {ratio2:,.0f}đ per unit\n"
                    f"Better value: {better}"
                )
            else:
                cheaper = "Product A" if p1 < p2 else "Product B"
                diff = abs(p1 - p2)
                return (
                    f"Product A: {p1:,.0f}đ\n"
                    f"Product B: {p2:,.0f}đ\n"
                    f"Cheaper: {cheaper} (difference: {diff:,.0f}đ)\n"
                    f"Tip: Use '15990000/8 vs 22990000/16' to compare price per unit"
                )
        except Exception as e:
            return f"Error comparing: {e}. Format: '15990000/8 vs 22990000/16'"

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
            rates = get_exchange_rates()
            rate = rates.get(currency)
            if not rate:
                return f"Unknown currency '{currency}'. Available: {', '.join(sorted(rates.keys()))}"
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
