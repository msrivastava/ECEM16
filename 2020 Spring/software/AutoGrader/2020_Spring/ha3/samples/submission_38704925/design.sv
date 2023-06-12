// Code your design here
// Task 1
`timescale 1ns / 1ps

module ha3(
input CLK, RST, REQ,
input [15:0] A, D,
output ACK, FDBZ,
output [15:0] Q, R
);

reg signed [15:0] r;
reg signed [15:0] q;
reg signed [15:0] a_neg;
reg signed [15:0] d_neg;
reg signed [15:0] q_neg;
reg signed [15:0] r_neg;
reg ack;
reg fdbz;
integer i;
integer x;

always @ (posedge CLK) begin
if (RST || ~REQ) begin // reset
r = 16'b0;
q = 16'b0;
ack = 1'b0;
fdbz = 1'b0;
a_neg = 16'b0;
d_neg = 16'b0;
q_neg = 16'b0;
r_neg = 16'b0;
end

else if (REQ && D == 16'b0 ) begin
q = A <= 16'b1000000000000000 ? 16'b0111111111111111 : 16'b1000000000000000;
r = 16'b0;
fdbz = 1'b1;
ack = 1'b1;
end
else if (REQ && D == 16'b1000000000000000) begin
q = 16'b0;
if (A[15] == 1'b1) begin
r = -A;
end
else begin
r = A;
end
end
else if (REQ) begin // division
if (A[15] == 1'b1 && D[15] == 1'b1) begin
a_neg = -A;
d_neg = -D;
//$display(" a_neg=%d d_neg=%d", a_neg, d_neg);
for (i =5'b10000; i > 5'b00000; i=i-1) begin
// x since the for loop doesnt work when use range 15 to =0
x = (i - 5'b00001);
r = r << 1;
r[0] = a_neg[x];
if (r >= d_neg) begin
r = r - d_neg;
q[x] = 1'b1;
end
end
//$display(" q=%d q_neg=%d", q, q_neg);
end
if (A[15] == 1'b1 && D[15] == 1'b0) begin
a_neg = -A;
for (i =5'b10000; i > 5'b00000; i=i-1) begin
// x since the for loop doesnt work when use range 15 to =0
x = (i - 5'b00001);
r = r << 1;
r[0] = a_neg[x];
if (r >= D) begin
r = r - D;
q_neg[x] = 1'b1;
end
end
q = -q_neg;
end
if (A[15] == 1'b0 && D[15] == 1'b1) begin
d_neg = -D;
for (i =5'b10000; i > 5'b00000; i=i-1) begin
// x since the for loop doesnt work when use range 15 to =0
x = (i - 5'b00001);
r = r << 1;
r[0] = A[x];
if (r >= d_neg) begin
r = r - d_neg;
q_neg[x] = 1'b1;
end
end
q = -q_neg;
end
if (A[15] == 1'b0 && D[15] == 1'b0) begin
for (i =5'b10000; i > 5'b00000; i=i-1) begin
// x since the for loop doesnt work when use range 15 to =0
x = (i - 5'b00001);
r = r << 1;
r[0] = A[x];
if (r >= D) begin
r = r - D;
q[x] = 1'b1;
end
end
end

ack = 1'b1;
fdbz = 1'b0;
end
end

assign R = r;
assign Q = q;
assign ACK = ack;
assign FDBZ = fdbz;
endmodule
