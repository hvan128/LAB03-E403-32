import re
import unicodedata
from typing import Optional

from src.tools.product_search import PRODUCT_DB


def _normalize_text(text: str) -> str:
    lowered = (text or "").strip().lower()
    without_accents = "".join(
        ch for ch in unicodedata.normalize("NFD", lowered) if unicodedata.category(ch) != "Mn"
    )
    return re.sub(r"\s+", " ", without_accents)


SUPPORTED_PRODUCT_NAMES = {
    _normalize_text(name) for name in PRODUCT_DB.keys()
} | {
    _normalize_text(product["name"]) for product in PRODUCT_DB.values()
}

SUPPORTED_KEYWORDS = {
    "san pham",
    "product",
    "compare",
    "comparison",
    "so sanh",
    "tim",
    "tim kiem",
    "search",
    "gia",
    "gia bao nhieu",
    "bao nhieu tien",
    "discount",
    "giam gia",
    "khuyen mai",
    "price",
    "usd",
    "vnd",
    "dien thoai",
    "phone",
    "laptop",
    "may tinh",
    "iphone",
    "samsung",
    "macbook",
    "dell",
    "asus",
    "camera",
    "pin",
    "ram",
    "storage",
    "chip",
    "cau hinh",
    "thong so",
    "nen mua",
    "dang tien",
}

BLOCKED_TOPICS = {
    "chien su",
    "iran",
    "ukraine",
    "israel",
    "chinh tri",
    "thoi su",
    "tin tuc",
    "news",
    "war",
    "xung dot",
    "bong da",
    "the thao",
    "giai tri",
    "chung khoan",
    "gia vang",
    "thoi tiet",
    "weather",
}


def is_in_scope_query(query: str) -> bool:
    normalized = _normalize_text(query)
    if not normalized:
        return False

    if any(name in normalized for name in SUPPORTED_PRODUCT_NAMES):
        return True

    if any(keyword in normalized for keyword in SUPPORTED_KEYWORDS):
        return True

    if _looks_like_calculation(normalized):
        return True

    if any(topic in normalized for topic in BLOCKED_TOPICS):
        return False

    return False


def _looks_like_calculation(normalized_query: str) -> bool:
    has_digit = any(ch.isdigit() for ch in normalized_query)
    has_math = any(op in normalized_query for op in ["+", "-", "*", "/", "%", "sqrt", "pow", "log"])
    finance_terms = any(term in normalized_query for term in ["discount", "giam", "usd", "vnd"])
    return has_digit and (has_math or finance_terms)


def build_out_of_scope_response() -> str:
    return (
        "Xin lỗi, tôi chỉ hỗ trợ các câu hỏi về tìm kiếm, so sánh sản phẩm và tính giá "
        "cho điện thoại/laptop trong hệ thống. Bạn có thể hỏi như: "
        "'So sánh iPhone 15 và Samsung S24' hoặc 'MacBook Air M2 giảm 10% còn bao nhiêu?'."
    )
