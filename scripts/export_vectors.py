#!/usr/bin/env python3
"""Export every 8-bit input pair and its Python structural-model output."""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from baugh_wooley import multiply_with_trace  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "build" / "python_vectors.txt")
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="ascii") as stream:
        for a in range(-128, 128):
            for b in range(-128, 128):
                trace = multiply_with_trace(a, b)
                stream.write(f"{trace.a_bits:02X} {trace.b_bits:02X} {trace.output_bits:04X}\n")
    print(f"Exported 65536 Python vectors to {args.output}")


if __name__ == "__main__":
    main()
