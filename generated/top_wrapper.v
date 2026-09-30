// ======================================================
// Auto-generated top wrapper connecting partitions
// ======================================================

module top_wrapper (
    input  [7:0] a,
    input  [7:0] b,
    input        select_subtract,
    output [7:0] result,
    output       add_carry,
    output       subtract_borrow
);

wire [7:0] sum_internal;
    wire [7:0] difference_internal;

    adder_8 U_ADDER (
        .a     (a),
        .b     (b),
        .sum   (sum_internal),
        .carry (add_carry)
    );

    subtractor_8 U_SUBTRACTOR (
        .a          (a),
        .b          (b),
        .difference (difference_internal),
        .borrow     (subtract_borrow)
    );

    mux_8 U_MUX (
        .input_0 (sum_internal),
        .input_1 (difference_internal),
        .select  (select_subtract),
        .output_y(result)
    );
endmodule
