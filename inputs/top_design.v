// ============================================================
// top_design_gate.v
// Corrected structural gate-level test design using Nangate45.
//
// Fix:
//   Constant logic-0 nets are generated with LOGIC0_X1 cells
//   instead of "assign ... = 1'b0", preventing TritonRoute
//   from treating them as unroutable GROUND nets.
// ============================================================

module top_design (
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


// ------------------------------------------------------------
// Gate-level 8-bit ripple-carry adder
// ------------------------------------------------------------
module adder_8 (
    input  [7:0] a,
    input  [7:0] b,
    output [7:0] sum,
    output       carry
);

    wire [8:0] c;
    wire [7:0] axb;
    wire [7:0] carry_ab;
    wire [7:0] carry_cin;

    // Physical constant cell avoids an unroutable GROUND net.
    LOGIC0_X1 ADD_CONST_ZERO (
        .Z(c[0])
    );

    assign carry = c[8];

    XOR2_X1 ADD_XOR_AB_0 (.A(a[0]), .B(b[0]), .Z(axb[0]));
    XOR2_X1 ADD_XOR_S_0  (.A(axb[0]), .B(c[0]), .Z(sum[0]));
    AND2_X1 ADD_AND_AB_0 (.A1(a[0]), .A2(b[0]), .ZN(carry_ab[0]));
    AND2_X1 ADD_AND_C_0  (.A1(axb[0]), .A2(c[0]), .ZN(carry_cin[0]));
    OR2_X1  ADD_OR_C_0   (.A1(carry_ab[0]), .A2(carry_cin[0]), .ZN(c[1]));

    XOR2_X1 ADD_XOR_AB_1 (.A(a[1]), .B(b[1]), .Z(axb[1]));
    XOR2_X1 ADD_XOR_S_1  (.A(axb[1]), .B(c[1]), .Z(sum[1]));
    AND2_X1 ADD_AND_AB_1 (.A1(a[1]), .A2(b[1]), .ZN(carry_ab[1]));
    AND2_X1 ADD_AND_C_1  (.A1(axb[1]), .A2(c[1]), .ZN(carry_cin[1]));
    OR2_X1  ADD_OR_C_1   (.A1(carry_ab[1]), .A2(carry_cin[1]), .ZN(c[2]));

    XOR2_X1 ADD_XOR_AB_2 (.A(a[2]), .B(b[2]), .Z(axb[2]));
    XOR2_X1 ADD_XOR_S_2  (.A(axb[2]), .B(c[2]), .Z(sum[2]));
    AND2_X1 ADD_AND_AB_2 (.A1(a[2]), .A2(b[2]), .ZN(carry_ab[2]));
    AND2_X1 ADD_AND_C_2  (.A1(axb[2]), .A2(c[2]), .ZN(carry_cin[2]));
    OR2_X1  ADD_OR_C_2   (.A1(carry_ab[2]), .A2(carry_cin[2]), .ZN(c[3]));

    XOR2_X1 ADD_XOR_AB_3 (.A(a[3]), .B(b[3]), .Z(axb[3]));
    XOR2_X1 ADD_XOR_S_3  (.A(axb[3]), .B(c[3]), .Z(sum[3]));
    AND2_X1 ADD_AND_AB_3 (.A1(a[3]), .A2(b[3]), .ZN(carry_ab[3]));
    AND2_X1 ADD_AND_C_3  (.A1(axb[3]), .A2(c[3]), .ZN(carry_cin[3]));
    OR2_X1  ADD_OR_C_3   (.A1(carry_ab[3]), .A2(carry_cin[3]), .ZN(c[4]));

    XOR2_X1 ADD_XOR_AB_4 (.A(a[4]), .B(b[4]), .Z(axb[4]));
    XOR2_X1 ADD_XOR_S_4  (.A(axb[4]), .B(c[4]), .Z(sum[4]));
    AND2_X1 ADD_AND_AB_4 (.A1(a[4]), .A2(b[4]), .ZN(carry_ab[4]));
    AND2_X1 ADD_AND_C_4  (.A1(axb[4]), .A2(c[4]), .ZN(carry_cin[4]));
    OR2_X1  ADD_OR_C_4   (.A1(carry_ab[4]), .A2(carry_cin[4]), .ZN(c[5]));

    XOR2_X1 ADD_XOR_AB_5 (.A(a[5]), .B(b[5]), .Z(axb[5]));
    XOR2_X1 ADD_XOR_S_5  (.A(axb[5]), .B(c[5]), .Z(sum[5]));
    AND2_X1 ADD_AND_AB_5 (.A1(a[5]), .A2(b[5]), .ZN(carry_ab[5]));
    AND2_X1 ADD_AND_C_5  (.A1(axb[5]), .A2(c[5]), .ZN(carry_cin[5]));
    OR2_X1  ADD_OR_C_5   (.A1(carry_ab[5]), .A2(carry_cin[5]), .ZN(c[6]));

    XOR2_X1 ADD_XOR_AB_6 (.A(a[6]), .B(b[6]), .Z(axb[6]));
    XOR2_X1 ADD_XOR_S_6  (.A(axb[6]), .B(c[6]), .Z(sum[6]));
    AND2_X1 ADD_AND_AB_6 (.A1(a[6]), .A2(b[6]), .ZN(carry_ab[6]));
    AND2_X1 ADD_AND_C_6  (.A1(axb[6]), .A2(c[6]), .ZN(carry_cin[6]));
    OR2_X1  ADD_OR_C_6   (.A1(carry_ab[6]), .A2(carry_cin[6]), .ZN(c[7]));

    XOR2_X1 ADD_XOR_AB_7 (.A(a[7]), .B(b[7]), .Z(axb[7]));
    XOR2_X1 ADD_XOR_S_7  (.A(axb[7]), .B(c[7]), .Z(sum[7]));
    AND2_X1 ADD_AND_AB_7 (.A1(a[7]), .A2(b[7]), .ZN(carry_ab[7]));
    AND2_X1 ADD_AND_C_7  (.A1(axb[7]), .A2(c[7]), .ZN(carry_cin[7]));
    OR2_X1  ADD_OR_C_7   (.A1(carry_ab[7]), .A2(carry_cin[7]), .ZN(c[8]));

endmodule


// ------------------------------------------------------------
// Gate-level 8-bit ripple-borrow subtractor
//
// difference = a XOR b XOR borrow_in
// borrow_out = ((NOT a) AND b) OR
//              (borrow_in AND NOT(a XOR b))
// ------------------------------------------------------------
module subtractor_8 (
    input  [7:0] a,
    input  [7:0] b,
    output [7:0] difference,
    output       borrow
);

    wire [8:0] bin;
    wire [7:0] axb;
    wire [7:0] not_a;
    wire [7:0] not_axb;
    wire [7:0] borrow_term_1;
    wire [7:0] borrow_term_2;

    // Physical constant cell avoids an unroutable GROUND net.
    LOGIC0_X1 SUB_CONST_ZERO (
        .Z(bin[0])
    );

    assign borrow = bin[8];

    INV_X1  SUB_INV_A_0   (.A(a[0]), .ZN(not_a[0]));
    XOR2_X1 SUB_XOR_AB_0  (.A(a[0]), .B(b[0]), .Z(axb[0]));
    XOR2_X1 SUB_XOR_D_0   (.A(axb[0]), .B(bin[0]), .Z(difference[0]));
    INV_X1  SUB_INV_XOR_0 (.A(axb[0]), .ZN(not_axb[0]));
    AND2_X1 SUB_AND_1_0   (.A1(not_a[0]), .A2(b[0]), .ZN(borrow_term_1[0]));
    AND2_X1 SUB_AND_2_0   (.A1(bin[0]), .A2(not_axb[0]), .ZN(borrow_term_2[0]));
    OR2_X1  SUB_OR_B_0    (.A1(borrow_term_1[0]), .A2(borrow_term_2[0]), .ZN(bin[1]));

    INV_X1  SUB_INV_A_1   (.A(a[1]), .ZN(not_a[1]));
    XOR2_X1 SUB_XOR_AB_1  (.A(a[1]), .B(b[1]), .Z(axb[1]));
    XOR2_X1 SUB_XOR_D_1   (.A(axb[1]), .B(bin[1]), .Z(difference[1]));
    INV_X1  SUB_INV_XOR_1 (.A(axb[1]), .ZN(not_axb[1]));
    AND2_X1 SUB_AND_1_1   (.A1(not_a[1]), .A2(b[1]), .ZN(borrow_term_1[1]));
    AND2_X1 SUB_AND_2_1   (.A1(bin[1]), .A2(not_axb[1]), .ZN(borrow_term_2[1]));
    OR2_X1  SUB_OR_B_1    (.A1(borrow_term_1[1]), .A2(borrow_term_2[1]), .ZN(bin[2]));

    INV_X1  SUB_INV_A_2   (.A(a[2]), .ZN(not_a[2]));
    XOR2_X1 SUB_XOR_AB_2  (.A(a[2]), .B(b[2]), .Z(axb[2]));
    XOR2_X1 SUB_XOR_D_2   (.A(axb[2]), .B(bin[2]), .Z(difference[2]));
    INV_X1  SUB_INV_XOR_2 (.A(axb[2]), .ZN(not_axb[2]));
    AND2_X1 SUB_AND_1_2   (.A1(not_a[2]), .A2(b[2]), .ZN(borrow_term_1[2]));
    AND2_X1 SUB_AND_2_2   (.A1(bin[2]), .A2(not_axb[2]), .ZN(borrow_term_2[2]));
    OR2_X1  SUB_OR_B_2    (.A1(borrow_term_1[2]), .A2(borrow_term_2[2]), .ZN(bin[3]));

    INV_X1  SUB_INV_A_3   (.A(a[3]), .ZN(not_a[3]));
    XOR2_X1 SUB_XOR_AB_3  (.A(a[3]), .B(b[3]), .Z(axb[3]));
    XOR2_X1 SUB_XOR_D_3   (.A(axb[3]), .B(bin[3]), .Z(difference[3]));
    INV_X1  SUB_INV_XOR_3 (.A(axb[3]), .ZN(not_axb[3]));
    AND2_X1 SUB_AND_1_3   (.A1(not_a[3]), .A2(b[3]), .ZN(borrow_term_1[3]));
    AND2_X1 SUB_AND_2_3   (.A1(bin[3]), .A2(not_axb[3]), .ZN(borrow_term_2[3]));
    OR2_X1  SUB_OR_B_3    (.A1(borrow_term_1[3]), .A2(borrow_term_2[3]), .ZN(bin[4]));

    INV_X1  SUB_INV_A_4   (.A(a[4]), .ZN(not_a[4]));
    XOR2_X1 SUB_XOR_AB_4  (.A(a[4]), .B(b[4]), .Z(axb[4]));
    XOR2_X1 SUB_XOR_D_4   (.A(axb[4]), .B(bin[4]), .Z(difference[4]));
    INV_X1  SUB_INV_XOR_4 (.A(axb[4]), .ZN(not_axb[4]));
    AND2_X1 SUB_AND_1_4   (.A1(not_a[4]), .A2(b[4]), .ZN(borrow_term_1[4]));
    AND2_X1 SUB_AND_2_4   (.A1(bin[4]), .A2(not_axb[4]), .ZN(borrow_term_2[4]));
    OR2_X1  SUB_OR_B_4    (.A1(borrow_term_1[4]), .A2(borrow_term_2[4]), .ZN(bin[5]));

    INV_X1  SUB_INV_A_5   (.A(a[5]), .ZN(not_a[5]));
    XOR2_X1 SUB_XOR_AB_5  (.A(a[5]), .B(b[5]), .Z(axb[5]));
    XOR2_X1 SUB_XOR_D_5   (.A(axb[5]), .B(bin[5]), .Z(difference[5]));
    INV_X1  SUB_INV_XOR_5 (.A(axb[5]), .ZN(not_axb[5]));
    AND2_X1 SUB_AND_1_5   (.A1(not_a[5]), .A2(b[5]), .ZN(borrow_term_1[5]));
    AND2_X1 SUB_AND_2_5   (.A1(bin[5]), .A2(not_axb[5]), .ZN(borrow_term_2[5]));
    OR2_X1  SUB_OR_B_5    (.A1(borrow_term_1[5]), .A2(borrow_term_2[5]), .ZN(bin[6]));

    INV_X1  SUB_INV_A_6   (.A(a[6]), .ZN(not_a[6]));
    XOR2_X1 SUB_XOR_AB_6  (.A(a[6]), .B(b[6]), .Z(axb[6]));
    XOR2_X1 SUB_XOR_D_6   (.A(axb[6]), .B(bin[6]), .Z(difference[6]));
    INV_X1  SUB_INV_XOR_6 (.A(axb[6]), .ZN(not_axb[6]));
    AND2_X1 SUB_AND_1_6   (.A1(not_a[6]), .A2(b[6]), .ZN(borrow_term_1[6]));
    AND2_X1 SUB_AND_2_6   (.A1(bin[6]), .A2(not_axb[6]), .ZN(borrow_term_2[6]));
    OR2_X1  SUB_OR_B_6    (.A1(borrow_term_1[6]), .A2(borrow_term_2[6]), .ZN(bin[7]));

    INV_X1  SUB_INV_A_7   (.A(a[7]), .ZN(not_a[7]));
    XOR2_X1 SUB_XOR_AB_7  (.A(a[7]), .B(b[7]), .Z(axb[7]));
    XOR2_X1 SUB_XOR_D_7   (.A(axb[7]), .B(bin[7]), .Z(difference[7]));
    INV_X1  SUB_INV_XOR_7 (.A(axb[7]), .ZN(not_axb[7]));
    AND2_X1 SUB_AND_1_7   (.A1(not_a[7]), .A2(b[7]), .ZN(borrow_term_1[7]));
    AND2_X1 SUB_AND_2_7   (.A1(bin[7]), .A2(not_axb[7]), .ZN(borrow_term_2[7]));
    OR2_X1  SUB_OR_B_7    (.A1(borrow_term_1[7]), .A2(borrow_term_2[7]), .ZN(bin[8]));

endmodule


// ------------------------------------------------------------
// Gate-level 8-bit 2-to-1 multiplexer
// ------------------------------------------------------------
module mux_8 (
    input  [7:0] input_0,
    input  [7:0] input_1,
    input        select,
    output [7:0] output_y
);

    MUX2_X1 MUX_BIT_0 (.A(input_0[0]), .B(input_1[0]), .S(select), .Z(output_y[0]));
    MUX2_X1 MUX_BIT_1 (.A(input_0[1]), .B(input_1[1]), .S(select), .Z(output_y[1]));
    MUX2_X1 MUX_BIT_2 (.A(input_0[2]), .B(input_1[2]), .S(select), .Z(output_y[2]));
    MUX2_X1 MUX_BIT_3 (.A(input_0[3]), .B(input_1[3]), .S(select), .Z(output_y[3]));
    MUX2_X1 MUX_BIT_4 (.A(input_0[4]), .B(input_1[4]), .S(select), .Z(output_y[4]));
    MUX2_X1 MUX_BIT_5 (.A(input_0[5]), .B(input_1[5]), .S(select), .Z(output_y[5]));
    MUX2_X1 MUX_BIT_6 (.A(input_0[6]), .B(input_1[6]), .S(select), .Z(output_y[6]));
    MUX2_X1 MUX_BIT_7 (.A(input_0[7]), .B(input_1[7]), .S(select), .Z(output_y[7]));

endmodule
