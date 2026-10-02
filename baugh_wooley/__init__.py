"""Bit-accurate structural Baugh-Wooley multiplication."""

from .model import (
    Trace,
    baugh_wooley,
    from_bits,
    full_adder,
    half_adder,
    multiply_with_trace,
    to_bits,
    transformed_sum,
)

__all__ = [
    "Trace", "baugh_wooley", "from_bits", "full_adder", "half_adder",
    "multiply_with_trace", "to_bits", "transformed_sum",
]
