`timescale 1ns/1ps
`default_nettype none

module tb_exhaustive;
    parameter integer WIDTH = 8;
    localparam integer CASES = 1 << WIDTH;
    reg signed [WIDTH-1:0] a, b;
    wire signed [2*WIDTH-1:0] product;
    wire signed [2*WIDTH-1:0] expected;
    wire [15:0] reference_product;
    integer av, bv, count;

    baugh_wooley_multiplier #(.WIDTH(WIDTH)) dut (
        .a(a), .b(b), .product(product)
    );
    // A multiplication operator is used only as the test oracle.
    assign expected = $signed(a) * $signed(b);
    generate
        if (WIDTH == 8) begin : gen_reference
            mul_reference reference_dut (.A(a), .B(b), .O(reference_product));
        end else begin : gen_no_reference
            assign reference_product = 16'b0;
        end
    endgenerate

    initial begin
        count = 0;
        for (av = 0; av < CASES; av = av + 1) begin
            for (bv = 0; bv < CASES; bv = bv + 1) begin
                a = av;
                b = bv;
                #1;  // Testbench settling interval, not an RTL register.
                if (product !== expected) begin
                    $fatal(1, "WIDTH=%0d A=%0d B=%0d got=%0d expected=%0d",
                           WIDTH, a, b, product, expected);
                end
                if (WIDTH == 8 && product !== reference_product) begin
                    $fatal(1, "Flat reference differs for A=%0d B=%0d", a, b);
                end
                count = count + 1;
            end
        end
        $display("PASS: WIDTH=%0d, %0d exhaustive operand pairs", WIDTH, count);
        $finish;
    end
endmodule

`default_nettype wire
