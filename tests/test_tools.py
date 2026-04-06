"""
[Phan Thanh Sang] Unit tests cho các tools.

Chạy: python -m pytest tests/test_tools.py -v
"""

import pytest
from src.tools.product_search import product_search
from src.tools.product_compare import product_compare
from src.tools.price_calculator import price_calculator
from src.tools.calculator import calculator


# === Product Search Tests ===

class TestProductSearch:
    def test_search_exact_name(self):
        result = product_search("iPhone 15")
        assert "iPhone 15" in result
        assert "22,990,000" in result

    def test_search_by_category(self):
        result = product_search("laptop")
        assert "MacBook" in result
        assert "Dell" in result or "ASUS" in result

    def test_search_not_found(self):
        result = product_search("Nokia 3310")
        assert "No products found" in result

    def test_search_partial_name(self):
        result = product_search("samsung")
        assert "Samsung" in result


# === Product Compare Tests ===

class TestProductCompare:
    def test_compare_two_phones(self):
        result = product_compare("iPhone 15 vs Samsung S24")
        assert "iPhone 15" in result
        assert "Samsung" in result
        assert "Price" in result

    def test_compare_invalid_format(self):
        result = product_compare("iPhone 15")
        assert "Error" in result

    def test_compare_not_found(self):
        result = product_compare("iPhone 15 vs Nokia 3310")
        assert "not found" in result


# === Price Calculator Tests ===

class TestPriceCalculator:
    def test_discount(self):
        result = price_calculator("22990000 discount 15%")
        assert "After discount" in result
        assert "19,541,500" in result

    def test_currency_conversion(self):
        result = price_calculator("25000000 to usd")
        assert "USD" in result
        assert "1,000" in result

    def test_math_expression(self):
        result = price_calculator("22990000 / 8")
        assert "2,873,750" in result

    def test_unknown_currency(self):
        result = price_calculator("100000 to btc")
        assert "Unknown currency" in result


# === Calculator Tests ===

class TestCalculator:
    def test_basic_math(self):
        assert calculator("2 + 3") == "5"

    def test_complex_expression(self):
        assert calculator("sqrt(144)") == "12.0"
