PYTHON ?= python3
IVERILOG ?= iverilog
VVP ?= vvp
GTKWAVE ?= gtkwave

RTL = rtl/half_adder.sv rtl/full_adder.sv rtl/baugh_wooley_multiplier.sv rtl/mul.sv
REFERENCE = rtl/mul_reference.sv

.PHONY: help test check-tools sim exhaustive crosscheck verify waveform view clean

help:
	@echo "make test        Run Python tests (including all 65536 signed 8-bit pairs)"
	@echo "make sim         Simulate 12 examples and generate build/example.vcd"
	@echo "make exhaustive  Exhaustive RTL checks at WIDTH=2, 4 and 8"
	@echo "make crosscheck  Compare RTL against all 65536 Python-generated vectors"
	@echo "make verify      Run Python, RTL, cross-language and waveform checks"
	@echo "make waveform    Regenerate docs/waveform.svg and docs/example.vcd"
	@echo "make view        Open the generated waveform in GTKWave"
	@echo "make clean       Delete temporary build products"

test:
	$(PYTHON) -m unittest discover -s tests -v

check-tools:
	@command -v $(IVERILOG) >/dev/null || { echo "Install Icarus Verilog (iverilog) first."; exit 1; }
	@command -v $(VVP) >/dev/null || { echo "Install Icarus Verilog (vvp) first."; exit 1; }

build:
	mkdir -p build

sim: check-tools | build
	$(IVERILOG) -g2012 -Wall -s tb_waveform -o build/waveform.vvp $(RTL) tb/tb_waveform.sv
	$(VVP) build/waveform.vvp

exhaustive: check-tools | build
	$(IVERILOG) -g2012 -Wall -s tb_exhaustive -Ptb_exhaustive.WIDTH=2 -o build/exhaustive_2.vvp $(RTL) $(REFERENCE) tb/tb_exhaustive.sv
	$(VVP) build/exhaustive_2.vvp
	$(IVERILOG) -g2012 -Wall -s tb_exhaustive -Ptb_exhaustive.WIDTH=4 -o build/exhaustive_4.vvp $(RTL) $(REFERENCE) tb/tb_exhaustive.sv
	$(VVP) build/exhaustive_4.vvp
	$(IVERILOG) -g2012 -Wall -s tb_exhaustive -Ptb_exhaustive.WIDTH=8 -o build/exhaustive_8.vvp $(RTL) $(REFERENCE) tb/tb_exhaustive.sv
	$(VVP) build/exhaustive_8.vvp

crosscheck: check-tools | build
	$(PYTHON) scripts/export_vectors.py
	$(IVERILOG) -g2012 -Wall -s tb_python_vectors -o build/python_vectors.vvp $(RTL) tb/tb_python_vectors.sv
	$(VVP) build/python_vectors.vvp

verify: test exhaustive crosscheck waveform

waveform: sim
	$(PYTHON) scripts/render_waveform.py --vcd build/example.vcd --output docs/waveform.svg --png docs/waveform.png --copy-vcd docs/example.vcd

view: sim
	$(GTKWAVE) build/example.vcd

clean:
	$(PYTHON) -c 'import shutil; shutil.rmtree("build", ignore_errors=True)'
