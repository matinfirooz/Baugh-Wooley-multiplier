`timescale 1ns/1ps
`default_nettype none

// Compatibility interface matching the user's original mul module.
// A and B hold signed 8-bit two's-complement bit patterns.
// The output O holds the signed 16-bit two's-complement product.
module mul (
    input  wire [7:0]  A,
    input  wire [7:0]  B,
    output wire [15:0] O
);
    baugh_wooley_multiplier #(.WIDTH(8)) core (
        .a(A), .b(B), .product(O)
    );
endmodule

`default_nettype wire
