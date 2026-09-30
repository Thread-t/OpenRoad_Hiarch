// Auto-extracted by split_net_v5.py
// Module: adder_8

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
