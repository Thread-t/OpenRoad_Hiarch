// ======================================================
// Auto-generated top wrapper
// Used to reconnect separated partition blocks
// ======================================================

// Physical macro definitions are provided by the generated LEF files.
// No empty black-box module declarations are generated.

// Top wrapper connecting both partitions
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
