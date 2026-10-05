from decimal import Decimal

import pytest

from apps.pricing.money import convert_from_inr, format_inr


@pytest.mark.parametrize(
    ("amount", "expected"),
    [
        (0, "₹0"),
        (999, "₹999"),
        (1_000, "₹1,000"),
        (45_000, "₹45,000"),
        (450_000, "₹4,50,000"),
        (12_345_678, "₹1,23,45,678"),
    ],
)
def test_format_inr_uses_indian_digit_grouping(amount, expected):
    assert format_inr(amount) == expected


def test_convert_from_inr_rounds_to_the_nearest_ten():
    # 4,50,000 / 96.32 = 4671.9... -> 4670
    assert convert_from_inr(450_000, Decimal("96.32")) == 4670
    # 4,50,000 / 96.00 = 4687.5 -> 4690 (halves round up)
    assert convert_from_inr(450_000, Decimal("96.00")) == 4690
