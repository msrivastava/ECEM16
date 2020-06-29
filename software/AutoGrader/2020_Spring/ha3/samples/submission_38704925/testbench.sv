// Code your testbench here
// or browse Examples
// Testbench

`timescale 1ns / 1ps

module ha3_tb();

reg clk, rst, req;
reg [15:0] a;
reg [15:0] d;
reg signed [15:0] a_sign;
reg signed [15:0] d_sign;
reg [15:0] q_sign;
reg [15:0] q_correct;
reg [15:0] r_correct;
wire ack;
wire fdbz;
wire [15:0] q, r;
integer i;
integer j;
integer ok, error;

always begin
#1 clk = !clk;
end

ha3 ha3_t(.CLK(clk), .RST(rst), .REQ(req), .A(a), .D(d), .ACK(ack), .FDBZ(fdbz), .Q(q), .R(r));

initial begin
$dumpfile("dump.vcd"); $dumpvars;
ok = 0;
error = 0;
// keep changing since reaches the max value of lines
for (i=16'b0000000000000000;i<16'b1111111111111111;i=i+1) begin #2
for (j=16'b0000000000000000;j<16'b1111111111111111;j=j+1) begin #2
clk <= 0;
#2
rst = 1;
#2
assign req = 1;
assign rst = 0;
assign a = i;
assign d = j;
#2
if (a[15] == 1'b1) begin
a_sign = -a;
end
if (d[15] == 1'b1) begin
d_sign = -d;
end

q_sign = (a_sign/d_sign);
r_correct = (a_sign%d_sign);

if (a[15] == 1'b1) begin
q_sign = -q_sign;
end
if (d[15] == 1'b1) begin
q_sign = -q_sign;
end
assign q_correct = q_sign;
#1
if (ack == 1) begin
if ((q_correct != q || r_correct != r)) begin
$display("ASSERTION ERROR: a=%b d=%b q=%b r=%b EXPECTED q_correct=%b r_correct=%b ack=%b ", a, d, q, r, q_correct, r_correct, ack);
error = error + 1;
end
else begin
$display("OK: a=%b d=%b q=%b r=%b ack=%b fdbz=%b", a, d, q, r, ack, fdbz);
ok = ok + 1;
end
assign req = 0;
end
end
end
$display(" ok=%d error=%d", ok, error);
end
endmodule


