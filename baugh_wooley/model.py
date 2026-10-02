"""Signed multiplication using the same HA/FA array as the supplied RTL.

Only the verification code multiplies the two operands using Python's `*`.
The structural datapath below uses one-bit logic, shifts, and bit assembly.
"""

from dataclasses import dataclass
from typing import Tuple


def _width(width: int) -> None:
    if isinstance(width, bool) or not isinstance(width, int) or width < 2:
        raise ValueError("width must be an integer of at least 2")


def to_bits(value: int, width: int) -> int:
    """Encode a signed integer as a width-bit two's-complement pattern.

    Out-of-range integers are rejected rather than silently truncated.
    """
    _width(width)
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("operand must be an integer")
    if not -(1 << (width - 1)) <= value < (1 << (width - 1)):
        raise ValueError(f"{value} does not fit a signed {width}-bit operand")
    return value & ((1 << width) - 1)


def from_bits(bits: int, width: int) -> int:
    """Interpret a width-bit nonnegative bit pattern as a signed integer."""
    _width(width)
    if isinstance(bits, bool) or not isinstance(bits, int):
        raise TypeError("bits must be an integer")
    if not 0 <= bits < (1 << width):
        raise ValueError(f"bits must be between 0 and {(1 << width) - 1}")
    return bits - (1 << width) if bits & (1 << (width - 1)) else bits


def half_adder(a: int, b: int) -> Tuple[int, int]:
    """Return (sum, carry) for two one-bit inputs."""
    return a ^ b, a & b


def full_adder(a: int, b: int, cin: int) -> Tuple[int, int]:
    """Return (sum, carry) for three one-bit inputs."""
    return a ^ b ^ cin, (a & b) | (a & cin) | (b & cin)


def _assemble(bits: Tuple[int, ...]) -> int:
    # Array column zero is the least significant bit.
    result = 0
    for column, bit in enumerate(bits):
        result |= bit << column
    return result


def _partial_products(a_bits: int, b_bits: int, width: int):
    return tuple(
        tuple(
            (((a_bits >> row) & 1) & ((b_bits >> column) & 1))
            ^ int((row == width - 1) != (column == width - 1))
            for column in range(width)
        )
        for row in range(width)
    )


@dataclass(frozen=True)
class Trace:
    """Array signals, in increasing row/column order (LSB at column zero)."""

    width: int
    a: int
    b: int
    a_bits: int
    b_bits: int
    partial_products: Tuple[Tuple[int, ...], ...]
    sums: Tuple[Tuple[int, ...], ...]
    # carries[0] is a placeholder only; the hardware has no C_0 row.
    carries: Tuple[Tuple[int, ...], ...]
    output_bits: int
    product: int

    @property
    def correction_positions(self) -> Tuple[int, int]:
        return self.width, 2 * self.width - 1

    def sum_word(self, row: int) -> int:
        return _assemble(self.sums[row])

    def carry_word(self, row: int) -> int:
        if not 1 <= row <= self.width:
            raise ValueError("carry row must be between 1 and width")
        return _assemble(self.carries[row])


def multiply_with_trace(a: int, b: int, width: int = 8) -> Trace:
    """Evaluate every half/full adder in the structural signed multiplier."""
    a_bits, b_bits = to_bits(a, width), to_bits(b, width)
    pp = _partial_products(a_bits, b_bits, width)
    s = [[0] * width for _ in range(width + 1)]
    c = [[0] * width for _ in range(width + 1)]
    s[0] = list(pp[0])

    for column in range(width - 1):
        s[1][column], c[1][column] = half_adder(s[0][column + 1], pp[1][column])
    s[1][-1], c[1][-1] = half_adder(1, pp[1][-1])

    for row in range(2, width):
        for column in range(width - 1):
            s[row][column], c[row][column] = full_adder(
                s[row - 1][column + 1], c[row - 1][column], pp[row][column]
            )
        s[row][-1], c[row][-1] = half_adder(c[row - 1][-1], pp[row][-1])

    s[width][0], c[width][0] = half_adder(s[width - 1][1], c[width - 1][0])
    for column in range(1, width - 1):
        s[width][column], c[width][column] = full_adder(
            s[width - 1][column + 1], c[width][column - 1], c[width - 1][column]
        )
    s[width][-1], c[width][-1] = full_adder(1, c[width][-2], c[width - 1][-1])

    low = _assemble(tuple(s[row][0] for row in range(width)))
    output_bits = (_assemble(tuple(s[width])) << width) | low
    return Trace(
        width, a, b, a_bits, b_bits, pp,
        tuple(tuple(row) for row in s), tuple(tuple(row) for row in c),
        output_bits, from_bits(output_bits, 2 * width),
    )


def baugh_wooley(a: int, b: int, width: int = 8) -> int:
    """Return the exact signed product of two width-bit signed integers."""
    return multiply_with_trace(a, b, width).product


def transformed_sum(a: int, b: int, width: int = 8) -> int:
    """Independent arithmetic model: weighted transformed rows + corrections.

    Returns the raw 2*width-bit output pattern. This model does not use the
    reduction array and provides an independent way to check its wiring.
    """
    pp = _partial_products(to_bits(a, width), to_bits(b, width), width)
    total = (1 << width) + (1 << (2 * width - 1))
    for row, bits in enumerate(pp):
        total += _assemble(bits) << row
    return total & ((1 << (2 * width)) - 1)
