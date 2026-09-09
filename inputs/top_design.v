// verilog/top_design.v
// Contains both adder and multiplier

module top_design (
    input  [31:0] a, b,
    output [31:0] sum,
    output [63:0] product
);

    // Adder Instance
    adder_32 U_ADDER (
        .a(a),
        .b(b),
        .sum(sum)
    );

    // Multiplier Instance
    multiplier_32 U_MULTIPLIER (
        .a(a),
        .b(b),
        .product(product)
    );

endmodule

// 32-bit Adder
module adder_32 (
    input  [31:0] a, b,
    output [31:0] sum
);

    wire [31:0] carry;

    // First bit
    full_adder fa0 (.a(a[0]), .b(b[0]), .cin(1'b0), .sum(sum[0]), .cout(carry[0]));

    // Remaining bits
    genvar i;
    generate
        for (i = 1; i < 32; i = i + 1) begin : adder_loop
            full_adder fa (.a(a[i]), .b(b[i]), .cin(carry[i-1]), .sum(sum[i]), .cout(carry[i]));
        end
    endgenerate

endmodule

// 32-bit Multiplier
module multiplier_32 (
    input  [31:0] a, b,
    output [63:0] product
);

    wire [63:0] partial_products;

    // Generate partial products
    genvar i, j;
    generate
        for (i = 0; i < 32; i = i + 1) begin : mult_loop
            for (j = 0; j < 32; j = j + 1) begin : inner_loop
                assign partial_products[i+j] = a[i] & b[j];
            end
        end
    endgenerate

    // Sum partial products
    assign product = partial_products;

endmodule

// Full Adder
module full_adder (
    input  a, b, cin,
    output sum, cout
);
    assign sum  = a ^ b ^ cin;
    assign cout = (a & b) | (a & cin) | (b & cin);
endmodule