`timescale 1ns/1ps
`default_nettype none

module tb_python_vectors;
    reg [7:0] A, B;
    reg [15:0] expected;
    wire [15:0] O;
    integer vectors_file, scanned, count;
    mul dut (.A(A), .B(B), .O(O));

    initial begin
        vectors_file = $fopen("build/python_vectors.txt", "r");
        if (vectors_file == 0) $fatal(1, "Run scripts/export_vectors.py first");
        count = 0;
        while (!$feof(vectors_file)) begin
            scanned = $fscanf(vectors_file, "%h %h %h\n", A, B, expected);
            if (scanned == 3) begin
                #1;
                if (O !== expected) $fatal(1, "Python/SV mismatch A=%h B=%h O=%h expected=%h", A, B, O, expected);
                count = count + 1;
            end else if (!$feof(vectors_file)) begin
                $fatal(1, "Malformed vector file");
            end
        end
        $fclose(vectors_file);
        if (count != 65536) $fatal(1, "Expected 65536 vectors; got %0d", count);
        $display("PASS: 65536 Python/SystemVerilog cross-checks");
        $finish;
    end
endmodule

`default_nettype wire
