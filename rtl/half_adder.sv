`timescale 1ns/1ps
`default_nettype none

// The PDKGENHAX1 function in the supplied RTL.
module half_adder (
    input  wire a,
    input  wire b,
    output wire sum,
    output wire carry
);
    assign sum   = a ^ b;
    assign carry = a & b;
endmodule

`default_nettype wire
