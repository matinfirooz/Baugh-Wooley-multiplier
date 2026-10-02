`timescale 1ns/1ps
`default_nettype none

// Combinational, structural, signed WIDTH x WIDTH Baugh-Wooley multiplier.
// Supported WIDTH >= 2. No multiplication operator is used in this module.
module baugh_wooley_multiplier #(
    parameter integer WIDTH = 8
) (
    input  wire signed [WIDTH-1:0]     a,
    input  wire signed [WIDTH-1:0]     b,
    output wire signed [2*WIDTH-1:0]   product
);
    // pp[r][j] is the transformed partial product of a[r] and b[j].
    // s[r][j] has weight 2^(r+j); c[r][j] has weight 2^(r+j+1).
    wire [WIDTH-1:0] pp [0:WIDTH-1];
    wire [WIDTH-1:0] s  [0:WIDTH];
    wire [WIDTH-1:0] c  [1:WIDTH];

    generate
        for (genvar r = 0; r < WIDTH; r = r + 1) begin : gen_pp_row
            for (genvar j = 0; j < WIDTH; j = j + 1) begin : gen_pp_bit
                // Invert a sign-cross term, but retain the sign x sign term.
                if ((r == WIDTH-1) != (j == WIDTH-1)) begin : gen_invert
                    assign pp[r][j] = ~(a[r] & b[j]);
                end else begin : gen_and
                    assign pp[r][j] = a[r] & b[j];
                end
            end
        end
    endgenerate

    assign s[0] = pp[0];

    // Row 1: the previous row is shifted relative to the new partial row.
    generate
        for (genvar j = 0; j < WIDTH-1; j = j + 1) begin : gen_first_row
            half_adder ha (
                .a(s[0][j+1]), .b(pp[1][j]),
                .sum(s[1][j]), .carry(c[1][j])
            );
        end
    endgenerate

    // This cell is in product column WIDTH: correction bit 2^WIDTH.
    half_adder first_correction (
        .a(1'b1), .b(pp[1][WIDTH-1]),
        .sum(s[1][WIDTH-1]), .carry(c[1][WIDTH-1])
    );

    // Reduction rows 2 through WIDTH-1.
    generate
        for (genvar r = 2; r < WIDTH; r = r + 1) begin : gen_reduction_row
            for (genvar j = 0; j < WIDTH-1; j = j + 1) begin : gen_column
                full_adder fa (
                    .a(s[r-1][j+1]), .b(c[r-1][j]), .cin(pp[r][j]),
                    .sum(s[r][j]), .carry(c[r][j])
                );
            end
            half_adder edge_ha (
                .a(c[r-1][WIDTH-1]), .b(pp[r][WIDTH-1]),
                .sum(s[r][WIDTH-1]), .carry(c[r][WIDTH-1])
            );
        end
    endgenerate

    // Final ripple-carry row. Its sums become the upper WIDTH output bits.
    half_adder final_first (
        .a(s[WIDTH-1][1]), .b(c[WIDTH-1][0]),
        .sum(s[WIDTH][0]), .carry(c[WIDTH][0])
    );
    generate
        for (genvar j = 1; j < WIDTH-1; j = j + 1) begin : gen_final_row
            full_adder fa (
                .a(s[WIDTH-1][j+1]), .b(c[WIDTH][j-1]),
                .cin(c[WIDTH-1][j]),
                .sum(s[WIDTH][j]), .carry(c[WIDTH][j])
            );
        end
    endgenerate

    // Product column 2*WIDTH-1: correction bit 2^(2*WIDTH-1).
    full_adder final_correction (
        .a(1'b1), .b(c[WIDTH][WIDTH-2]), .cin(c[WIDTH-1][WIDTH-1]),
        .sum(s[WIDTH][WIDTH-1]), .carry(c[WIDTH][WIDTH-1])
    );
    // c[WIDTH][WIDTH-1] is column 2*WIDTH and is intentionally discarded.

    generate
        for (genvar bit_index = 0; bit_index < WIDTH; bit_index = bit_index + 1) begin : gen_low_output
            assign product[bit_index] = s[bit_index][0];
        end
    endgenerate
    assign product[2*WIDTH-1:WIDTH] = s[WIDTH];
endmodule

`default_nettype wire
