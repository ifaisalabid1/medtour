from decimal import ROUND_HALF_UP, Decimal


def format_inr(amount: int) -> str:
    """Format rupees with Indian digit grouping: 450000 -> "₹4,50,000"."""
    digits = str(amount)
    if len(digits) <= 3:
        return f"₹{digits}"
    head, last_three = digits[:-3], digits[-3:]
    groups = []
    while len(head) > 2:
        groups.insert(0, head[-2:])
        head = head[:-2]
    if head:
        groups.insert(0, head)
    return "₹" + ",".join([*groups, last_three])


def convert_from_inr(amount_inr: int, inr_per_unit: Decimal) -> int:
    """Convert rupees to another currency, rounded to the nearest 10.

    Rounding avoids false precision: these are indicative prices, and
    exchange rates move daily.
    """
    converted = Decimal(amount_inr) / inr_per_unit
    return int((converted / 10).quantize(Decimal("1"), rounding=ROUND_HALF_UP) * 10)
