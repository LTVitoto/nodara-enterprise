from __future__ import annotations

from decimal import Decimal


def estimate_tokens(text: str | None) -> int:
    if not text:
        return 0
    return max(1, len(text) // 4)


def estimate_cost_usd(provider: str, input_text: str, output_text: str) -> Decimal:
    input_tokens = Decimal(estimate_tokens(input_text))
    output_tokens = Decimal(estimate_tokens(output_text))
    rates = {
        "openai": (Decimal("0.000005"), Decimal("0.000015")),
        "anthropic": (Decimal("0.000003"), Decimal("0.000015")),
        "gemini": (Decimal("0.000001"), Decimal("0.000004")),
        "mock": (Decimal("0.000000"), Decimal("0.000000")),
    }
    in_rate, out_rate = rates.get(provider, rates["mock"])
    return (input_tokens * in_rate + output_tokens * out_rate).quantize(Decimal("0.000001"))
