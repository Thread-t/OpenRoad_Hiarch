// Auto-extracted by split_net_v2_arya.py
// Module: multiplier_32

module multiplier_32 (
    a, b, product
);

input [31:0] a;
  wire [31:0] a;
  input [31:0] b;
  wire [31:0] b;
  output [63:0] product;
  wire [63:0] product;
  AND2_X1 _00_ (
    .A1(a[0]),
    .A2(b[0]),
    .ZN(product[0])
  );
  AND2_X1 _01_ (
    .A1(b[0]),
    .A2(a[1]),
    .ZN(product[1])
  );
  AND2_X1 _02_ (
    .A1(b[0]),
    .A2(a[2]),
    .ZN(product[2])
  );
  AND2_X1 _03_ (
    .A1(b[0]),
    .A2(a[3]),
    .ZN(product[3])
  );
  AND2_X1 _04_ (
    .A1(b[0]),
    .A2(a[4]),
    .ZN(product[4])
  );
  AND2_X1 _05_ (
    .A1(b[0]),
    .A2(a[5]),
    .ZN(product[5])
  );
  AND2_X1 _06_ (
    .A1(b[0]),
    .A2(a[6]),
    .ZN(product[6])
  );
  AND2_X1 _07_ (
    .A1(b[0]),
    .A2(a[7]),
    .ZN(product[7])
  );
  AND2_X1 _08_ (
    .A1(b[0]),
    .A2(a[8]),
    .ZN(product[8])
  );
  AND2_X1 _09_ (
    .A1(b[0]),
    .A2(a[9]),
    .ZN(product[9])
  );
  AND2_X1 _10_ (
    .A1(b[0]),
    .A2(a[10]),
    .ZN(product[10])
  );
  AND2_X1 _11_ (
    .A1(b[0]),
    .A2(a[11]),
    .ZN(product[11])
  );
  AND2_X1 _12_ (
    .A1(b[0]),
    .A2(a[12]),
    .ZN(product[12])
  );
  AND2_X1 _13_ (
    .A1(b[0]),
    .A2(a[13]),
    .ZN(product[13])
  );
  AND2_X1 _14_ (
    .A1(b[0]),
    .A2(a[14]),
    .ZN(product[14])
  );
  AND2_X1 _15_ (
    .A1(b[0]),
    .A2(a[15]),
    .ZN(product[15])
  );
  AND2_X1 _16_ (
    .A1(b[0]),
    .A2(a[16]),
    .ZN(product[16])
  );
  AND2_X1 _17_ (
    .A1(b[0]),
    .A2(a[17]),
    .ZN(product[17])
  );
  AND2_X1 _18_ (
    .A1(b[0]),
    .A2(a[18]),
    .ZN(product[18])
  );
  AND2_X1 _19_ (
    .A1(b[0]),
    .A2(a[19]),
    .ZN(product[19])
  );
  AND2_X1 _20_ (
    .A1(b[0]),
    .A2(a[20]),
    .ZN(product[20])
  );
  AND2_X1 _21_ (
    .A1(b[0]),
    .A2(a[21]),
    .ZN(product[21])
  );
  AND2_X1 _22_ (
    .A1(b[0]),
    .A2(a[22]),
    .ZN(product[22])
  );
  AND2_X1 _23_ (
    .A1(b[0]),
    .A2(a[23]),
    .ZN(product[23])
  );
  AND2_X1 _24_ (
    .A1(b[0]),
    .A2(a[24]),
    .ZN(product[24])
  );
  AND2_X1 _25_ (
    .A1(b[0]),
    .A2(a[25]),
    .ZN(product[25])
  );
  AND2_X1 _26_ (
    .A1(b[0]),
    .A2(a[26]),
    .ZN(product[26])
  );
  AND2_X1 _27_ (
    .A1(b[0]),
    .A2(a[27]),
    .ZN(product[27])
  );
  AND2_X1 _28_ (
    .A1(b[0]),
    .A2(a[28]),
    .ZN(product[28])
  );
  AND2_X1 _29_ (
    .A1(b[0]),
    .A2(a[29]),
    .ZN(product[29])
  );
  AND2_X1 _30_ (
    .A1(b[0]),
    .A2(a[30]),
    .ZN(product[30])
  );
  AND2_X1 _31_ (
    .A1(b[0]),
    .A2(a[31]),
    .ZN(product[31])
  );
  AND2_X1 _32_ (
    .A1(b[1]),
    .A2(a[31]),
    .ZN(product[32])
  );
  AND2_X1 _33_ (
    .A1(b[2]),
    .A2(a[31]),
    .ZN(product[33])
  );
  AND2_X1 _34_ (
    .A1(b[3]),
    .A2(a[31]),
    .ZN(product[34])
  );
  AND2_X1 _35_ (
    .A1(b[4]),
    .A2(a[31]),
    .ZN(product[35])
  );
  AND2_X1 _36_ (
    .A1(b[5]),
    .A2(a[31]),
    .ZN(product[36])
  );
  AND2_X1 _37_ (
    .A1(b[6]),
    .A2(a[31]),
    .ZN(product[37])
  );
  AND2_X1 _38_ (
    .A1(b[7]),
    .A2(a[31]),
    .ZN(product[38])
  );
  AND2_X1 _39_ (
    .A1(b[8]),
    .A2(a[31]),
    .ZN(product[39])
  );
  AND2_X1 _40_ (
    .A1(b[9]),
    .A2(a[31]),
    .ZN(product[40])
  );
  AND2_X1 _41_ (
    .A1(b[10]),
    .A2(a[31]),
    .ZN(product[41])
  );
  AND2_X1 _42_ (
    .A1(b[11]),
    .A2(a[31]),
    .ZN(product[42])
  );
  AND2_X1 _43_ (
    .A1(b[12]),
    .A2(a[31]),
    .ZN(product[43])
  );
  AND2_X1 _44_ (
    .A1(b[13]),
    .A2(a[31]),
    .ZN(product[44])
  );
  AND2_X1 _45_ (
    .A1(b[14]),
    .A2(a[31]),
    .ZN(product[45])
  );
  AND2_X1 _46_ (
    .A1(b[15]),
    .A2(a[31]),
    .ZN(product[46])
  );
  AND2_X1 _47_ (
    .A1(b[16]),
    .A2(a[31]),
    .ZN(product[47])
  );
  AND2_X1 _48_ (
    .A1(b[17]),
    .A2(a[31]),
    .ZN(product[48])
  );
  AND2_X1 _49_ (
    .A1(b[18]),
    .A2(a[31]),
    .ZN(product[49])
  );
  AND2_X1 _50_ (
    .A1(b[19]),
    .A2(a[31]),
    .ZN(product[50])
  );
  AND2_X1 _51_ (
    .A1(b[20]),
    .A2(a[31]),
    .ZN(product[51])
  );
  AND2_X1 _52_ (
    .A1(b[21]),
    .A2(a[31]),
    .ZN(product[52])
  );
  AND2_X1 _53_ (
    .A1(b[22]),
    .A2(a[31]),
    .ZN(product[53])
  );
  AND2_X1 _54_ (
    .A1(b[23]),
    .A2(a[31]),
    .ZN(product[54])
  );
  AND2_X1 _55_ (
    .A1(b[24]),
    .A2(a[31]),
    .ZN(product[55])
  );
  AND2_X1 _56_ (
    .A1(b[25]),
    .A2(a[31]),
    .ZN(product[56])
  );
  AND2_X1 _57_ (
    .A1(b[26]),
    .A2(a[31]),
    .ZN(product[57])
  );
  AND2_X1 _58_ (
    .A1(b[27]),
    .A2(a[31]),
    .ZN(product[58])
  );
  AND2_X1 _59_ (
    .A1(b[28]),
    .A2(a[31]),
    .ZN(product[59])
  );
  AND2_X1 _60_ (
    .A1(b[29]),
    .A2(a[31]),
    .ZN(product[60])
  );
  AND2_X1 _61_ (
    .A1(b[30]),
    .A2(a[31]),
    .ZN(product[61])
  );
  AND2_X1 _62_ (
    .A1(b[31]),
    .A2(a[31]),
    .ZN(product[62])
  );
endmodule
