// ======================================================
// Auto-generated top wrapper connecting partitions
// ======================================================

module top_wrapper (
    input  [31:0] a, b,
    output [31:0] sum,
    output [63:0] product
);

adder_32 U_ADDER (
        .a(a),
        .b(b),
        .sum(sum)
    );

    
    multiplier_32 U_MULTIPLIER (
        .a(a),
        .b(b),
        .product(product)
    );
endmodule
