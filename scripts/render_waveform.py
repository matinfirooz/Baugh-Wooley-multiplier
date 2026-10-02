#!/usr/bin/env python3
"""Read actual simulator VCD data and render the README timing diagram.

Matplotlib is only needed for rendering. The parser and checks use the standard
library. The image shows settled bus values; it does not estimate gate delay.
"""

import argparse
import bisect
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from baugh_wooley import from_bits, multiply_with_trace  # noqa: E402

SIGNALS = {"A": 8, "B": 8, "O": 16, "expected": 16, "mismatch": 1,
           "S0": 8, "S7": 8, "C7": 8, "S8": 8}


def parse_vcd(path):
    """Parse the selected top-level digital signals and normalize time to ns."""
    content = Path(path).read_text(encoding="ascii")
    scale = re.search(r"\$timescale\s+(\d+)\s*(fs|ps|ns|us|ms|s)\s+\$end", content)
    if not scale:
        raise ValueError("VCD has no supported timescale")
    tick_ns = int(scale.group(1)) * {"fs": 1e-6, "ps": 1e-3, "ns": 1,
                                    "us": 1e3, "ms": 1e6, "s": 1e9}[scale.group(2)]
    declarations, body = content.split("$enddefinitions $end", 1)
    codes = {}
    for line in declarations.splitlines():
        tokens = line.split()
        if tokens and tokens[0] == "$var":
            _, _, width, code, name, *_ = tokens
            if name in SIGNALS:
                if int(width) != SIGNALS[name]:
                    raise ValueError(f"Unexpected width for {name}")
                codes[code] = name
    if set(codes.values()) != set(SIGNALS):
        raise ValueError("VCD is missing one or more documented waveform signals")
    events = {name: [] for name in SIGNALS}
    time_ns = 0.0
    for line in body.splitlines():
        line = line.strip()
        if not line or line.startswith("$"):
            continue
        if line.startswith("#"):
            time_ns = int(line[1:]) * tick_ns
            continue
        if line[0] in "bB":
            value, code = line[1:].split()
        elif line[0] in "01xXzZ":
            value, code = line[0], line[1:]
        else:
            continue
        if code in codes:
            bits = None if any(c in value.lower() for c in "xz") else int(value, 2)
            events[codes[code]].append((time_ns, bits))
    return events, time_ns


def value_at(events, name, time_ns):
    entries = events[name]
    # bisect_right selects the last delta-cycle value at a timestamp.
    index = bisect.bisect_right([event[0] for event in entries], time_ns) - 1
    if index < 0 or entries[index][1] is None:
        raise ValueError(f"Unknown {name} at {time_ns} ns")
    return entries[index][1]


def waveform_samples(path):
    events, finish = parse_vcd(path)
    starts = sorted({time for name in ("A", "B") for time, _ in events[name] if time < finish})
    if not starts or finish <= 0:
        raise ValueError("No stimulus intervals in VCD")
    samples = []
    for start, end in zip(starts, starts[1:] + [finish]):
        at = start + min(1.0, (end - start) / 2)
        words = {name: value_at(events, name, at) for name in SIGNALS}
        a, b = from_bits(words["A"], 8), from_bits(words["B"], 8)
        output = from_bits(words["O"], 16)
        expected = from_bits(words["expected"], 16)
        if words["mismatch"] or output != expected or output != a * b:
            raise ValueError(f"Simulation mismatch at {at} ns")
        trace = multiply_with_trace(a, b)
        for name, modeled in (("S0", trace.sum_word(0)), ("S7", trace.sum_word(7)),
                              ("C7", trace.carry_word(7)), ("S8", trace.sum_word(8))):
            if words[name] != modeled:
                raise ValueError(f"Python/RTL internal-row mismatch: {name} at {at} ns")
        samples.append({"start_ns": start, "end_ns": end, "sample_ns": at,
                        "a_signed": a, "b_signed": b, "product_signed": output,
                        "expected_signed": expected, "bits": words})
    return samples, finish


def render(samples, finish, output, png=None):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon, Rectangle

    plt.rcParams.update({"font.family": "DejaVu Sans", "svg.fonttype": "none"})
    fig, ax = plt.subplots(figsize=(19, 8.7), dpi=120)
    fig.patch.set_facecolor("#F5F7FB")
    ax.set_facecolor("#F5F7FB")
    ax.set_xlim(-19, finish + 2)
    ax.set_ylim(-2.3, 11.4)
    ax.axis("off")
    ax.text(-18, 10.8, "BAUGH–WOOLEY MULTIPLIER", fontsize=23, weight="bold", color="#152744")
    ax.text(-18, 10.1, "Signed 8 × 8 → 16  |  Actual Icarus Verilog simulation", fontsize=13, color="#516178")
    ax.text(finish, 10.7, "12 VECTORS\nALL MATCH", ha="right", va="center",
            fontsize=12, weight="bold", color="#0D766E",
            bbox={"boxstyle": "round,pad=0.6", "facecolor": "#DFF5ED", "edgecolor": "none"})
    ax.text(-18, 9.2, "Signal / format", fontsize=10, color="#516178", weight="bold")
    for time in sorted({sample["start_ns"] for sample in samples} | {finish}):
        ax.plot([time, time], [-0.15, 8.8], color="#DDE3EC", lw=0.8, zorder=0)
        ax.text(time, 9.15, f"{time:g}", ha="center", fontsize=10, color="#516178")
    ax.text(0, 9.55, "Time (ns)", fontsize=10, color="#516178")

    rows = [("A", "A[7:0]", "signed decimal", "#4263AC", "#E7EDFA"),
            ("B", "B[7:0]", "signed decimal", "#4263AC", "#E7EDFA"),
            ("O", "O[15:0]", "signed / hex", "#0D766E", "#DFF5ED"),
            ("expected", "expected[15:0]", "signed decimal", "#A16A1A", "#FCF0D8"),
            ("mismatch", "mismatch", "1 = failure", "#0D766E", "#DFF5ED"),
            ("S0", "S0[7:0]", "row 0 · hex", "#748297", "#EDF0F5"),
            ("S7", "S7[7:0]", "row 7 · hex", "#748297", "#EDF0F5"),
            ("C7", "C7[7:0]", "row 7 · hex", "#748297", "#EDF0F5"),
            ("S8", "S8[7:0]", "final row · hex", "#748297", "#EDF0F5")]
    for row, (name, label, fmt, edge, fill) in enumerate(rows):
        y = 8.35 - row
        ax.text(-18, y + 0.1, label, fontsize=11, weight="bold", color="#152744", va="center")
        ax.text(-18, y - 0.23, fmt, fontsize=9, color="#64738A", va="center")
        if name == "mismatch":
            ax.plot([0, finish], [y - 0.15, y - 0.15], color=edge, lw=2)
            for sample in samples:
                center = (sample["start_ns"] + sample["end_ns"]) / 2
                ax.text(center, y + 0.15, "0", ha="center", fontsize=11, color=edge)
            continue
        # A bus changes shape only when its value changes. Merge adjacent
        # equal intervals rather than drawing fictitious transitions.
        segments = []
        for sample in samples:
            bits = sample["bits"][name]
            if segments and segments[-1]["bits"] == bits:
                segments[-1]["end_ns"] = sample["end_ns"]
            else:
                segments.append({"start_ns": sample["start_ns"],
                                 "end_ns": sample["end_ns"], "bits": bits})
        for segment in segments:
            start, end = segment["start_ns"], segment["end_ns"]
            inset = min(0.7, (end - start) / 8)
            points = [(start, y), (start + inset, y + 0.30), (end - inset, y + 0.30),
                      (end, y), (end - inset, y - 0.30), (start + inset, y - 0.30)]
            ax.add_patch(Polygon(points, closed=True, facecolor=fill, edgecolor=edge, lw=1.3))
            bits = segment["bits"]
            if name in ("A", "B"):
                text = str(from_bits(bits, 8))
            elif name == "O":
                text = f"{from_bits(bits, 16)}\n0x{bits:04X}"
            elif name == "expected":
                text = str(from_bits(bits, 16))
            else:
                text = f"{bits:02X}"
            ax.text((start + end) / 2, y, text, ha="center", va="center", fontsize=10,
                    color=edge, weight="bold" if name == "O" else "normal", linespacing=1.25)

    ax.add_patch(Rectangle((-18.5, -1.8), finish + 20.5, 1.25, facecolor="#E6ECF5", edgecolor="none"))
    ax.text(-17.5, -0.97, "First vector: −3 × 5 = −15   |   A = 0xFD, B = 0x05, O = 0xFFF1",
            fontsize=12, color="#152744", weight="bold", va="center")
    ax.text(-17.5, -1.46, "10 ns stimulus intervals. Combinational zero-delay RTL: no clock or pipeline; these intervals do not measure hardware latency.",
            fontsize=10, color="#516178", va="center")
    fig.subplots_adjust(left=0.015, right=0.995, top=0.99, bottom=0.015)
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, facecolor=fig.get_facecolor(), metadata={"Date": None})
    if png:
        Path(png).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(png, facecolor=fig.get_facecolor())
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vcd", type=Path, default=ROOT / "build" / "example.vcd")
    parser.add_argument("--output", type=Path, default=ROOT / "docs" / "waveform.svg")
    parser.add_argument("--png", type=Path, help="also save a PNG (optional)")
    parser.add_argument("--copy-vcd", type=Path, help="copy the simulator VCD alongside the figure")
    args = parser.parse_args()
    samples, finish = waveform_samples(args.vcd)
    if len(samples) != 12:
        raise ValueError(f"The example testbench should have 12 intervals, got {len(samples)}")
    render(samples, finish, args.output, args.png)
    data_path = args.output.with_name("waveform_data.json")
    data_path.write_text(json.dumps({"source": args.vcd.name, "duration_ns": finish,
                                     "checked_vectors": len(samples), "samples": samples},
                                    indent=2) + "\n", encoding="utf-8")
    if args.copy_vcd:
        args.copy_vcd.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(args.vcd, args.copy_vcd)
    print(f"Verified {len(samples)} VCD intervals and internal rows; wrote {args.output}")


if __name__ == "__main__":
    main()
