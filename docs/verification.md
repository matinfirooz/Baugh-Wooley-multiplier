# Verification record

Checked on **2026-10-02** using Python **3.12.14**, Icarus Verilog / VVP **12.0**, and Matplotlib **3.10.8** on Linux.

## Results

| Check | Coverage | Result |
|---|---|---|
| Python half adder | All 4 input combinations | PASS |
| Python full adder | All 8 input combinations | PASS |
| Python default multiplier | All 65,536 signed 8-bit operand pairs | PASS |
| Python smaller widths | All pairs at widths 2, 3, 4, and 5 | PASS |
| Python wider boundaries | Minimum, maximum, −1, 0, and 1 at widths 6, 8, 12, and 16 | PASS |
| Python input/bit helpers | Range validation, two's-complement conversion, and trace row conservation | PASS |
| SystemVerilog, width 2 | All 16 operand pairs | PASS |
| SystemVerilog, width 4 | All 256 operand pairs | PASS |
| SystemVerilog, width 8 | All 65,536 operand pairs | PASS |
| Flat RTL reference equivalence | All 65,536 8-bit pairs, against the parameterized core | PASS |
| Python ↔ SystemVerilog | All 65,536 Python-generated output bit patterns | PASS |
| Waveform simulation | 12 directed vectors including signed boundary values | PASS |
| VCD image/data checks | All 12 settled outputs and S0/S7/C7/S8 rows match the Python model | PASS |
| Python package installation | Wheel built and installed into an isolated local target; module and console CLI executed | PASS |

The final RTL compiles with `iverilog -g2012 -Wall` without warnings. Eight Python unit-test methods cover the checks listed above. The independent multiplication oracle is confined to verification code; the DUT is a structural HA/FA array.

The PNG and SVG in this folder are generated from the included **simulator-produced** `example.vcd`. The simulation uses a 1 ps timestamp resolution, applies new inputs every 10 ns, and checks each result after 1 ns. The signals represent a combinational zero-delay RTL simulation, not a physical timing characterization.

## Reproduce

From the repository root, with Icarus Verilog, GNU Make, and the plotting dependency installed:

```bash
make verify
```

The key terminal results are:

```text
Ran 8 tests
OK
PASS: WIDTH=2, 16 exhaustive operand pairs
PASS: WIDTH=4, 256 exhaustive operand pairs
PASS: WIDTH=8, 65536 exhaustive operand pairs
PASS: 65536 Python/SystemVerilog cross-checks
PASS: 12 waveform vectors; saved build/example.vcd
Verified 12 VCD intervals and internal rows; wrote docs/waveform.svg
```

The included GitHub Actions workflow has the same functional verification steps. It runs after the repository is pushed; this record reports local checks only. No synthesis or device timing results are included.
