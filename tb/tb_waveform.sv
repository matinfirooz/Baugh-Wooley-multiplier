`timescale 1ns/1ps
`default_nettype none

// Functional waveform: no clock, no reset, and no delays inside the DUT.
module tb_waveform;
    reg signed [7:0] A, B;
    wire signed [15:0] O;
    wire signed [15:0] expected;
    wire mismatch;
    wire [7:0] S0, S7, C7, S8;
    integer sample_file;

    mul dut (.A(A), .B(B), .O(O));
    assign expected = $signed(A) * $signed(B);
    assign mismatch = (O !== expected);
    // Expose selected array rows under convenient waveform names.
    assign S0 = dut.core.s[0];
    assign S7 = dut.core.s[7];
    assign C7 = dut.core.c[7];
    assign S8 = dut.core.s[8];

    task automatic check(input integer av, input integer bv);
        begin
            A = av;
            B = bv;
            #1;
            if (O !== expected) $fatal(1, "A=%0d B=%0d O=%0d expected=%0d", A, B, O, expected);
            $fdisplay(sample_file, "%0t,%0d,%0d,%0d,%0d,%0d,%02h,%02h,%02h,%02h",
                      $time, A, B, O, expected, !mismatch, S0, S7, C7, S8);
            #9;
        end
    endtask

    initial begin
        $dumpfile("build/example.vcd");
        // Selected buses; exhaustive simulation intentionally does not dump.
        $dumpvars(0, A, B, O, expected, mismatch, S0, S7, C7, S8);
        sample_file = $fopen("build/waveform_samples.csv", "w");
        if (sample_file == 0) $fatal(1, "Could not open waveform_samples.csv");
        $fdisplay(sample_file, "time_ps,A,B,O,expected,match,S0,S7,C7,S8");
        check(-3, 5);
        check(3, 2);
        check(-5, 3);
        check(7, -4);
        check(-8, -8);
        check(0, -128);
        check(127, 127);
        check(-128, 127);
        check(-128, -128);
        check(-1, -1);
        check(85, 3);
        check(-1, 1);
        $fclose(sample_file);
        $display("PASS: 12 waveform vectors; saved build/example.vcd");
        $finish;
    end
endmodule

`default_nettype wire
