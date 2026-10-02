"""Run: python3 -m baugh_wooley --a -3 --b 5 --width 8 --trace."""

import argparse
import json
from dataclasses import asdict

from .model import multiply_with_trace


def main() -> None:
    parser = argparse.ArgumentParser(description="Structural signed Baugh-Wooley multiplier")
    parser.add_argument("--a", type=int, required=True, help="signed decimal operand A")
    parser.add_argument("--b", type=int, required=True, help="signed decimal operand B")
    parser.add_argument("--width", type=int, default=8, help="operand width, at least 2 (default: 8)")
    parser.add_argument("--trace", action="store_true", help="print each partial row and sum/carry row")
    parser.add_argument("--json", action="store_true", help="print the full trace as JSON")
    args = parser.parse_args()
    try:
        trace = multiply_with_trace(args.a, args.b, args.width)
    except (ValueError, TypeError) as error:
        parser.error(str(error))
    if args.json:
        print(json.dumps(asdict(trace), indent=2))
        return
    width = trace.width
    print(f"A = {trace.a:6d}  bits = {trace.a_bits:0{width}b}")
    print(f"B = {trace.b:6d}  bits = {trace.b_bits:0{width}b}")
    print(f"O = {trace.product:6d}  bits = {trace.output_bits:0{2 * width}b}  "
          f"hex = 0x{trace.output_bits:0{(2 * width + 3) // 4}X}")
    if args.trace:
        print(f"Correction bit positions: {trace.correction_positions}")
        print("Partial-product rows (MSB at left):")
        for row, bits in enumerate(trace.partial_products):
            print(f"  pp[{row}] = {''.join(str(bit) for bit in reversed(bits))}")
        print("Array rows (MSB at left; each row is logic, not a clock cycle):")
        print(f"  S[0] = {trace.sum_word(0):0{width}b}  C[0] = --")
        for row in range(1, width + 1):
            print(f"  S[{row}] = {trace.sum_word(row):0{width}b}  "
                  f"C[{row}] = {trace.carry_word(row):0{width}b}")


if __name__ == "__main__":
    main()
