// Auto-extracted by split_net_v5.py
// Module: mux_8

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
