`timescale 1ns/1ps
`default_nettype none

// The PDKGENFAX1 function in the supplied RTL.
module full_adder (
    input  wire a,
    input  wire b,
    input  wire cin,
    output wire sum,
    output wire carry
);
    assign sum   = a ^ b ^ cin;
    assign carry = (a & b) | (a & cin) | (b & cin);
endmodule

`default_nettype wire
