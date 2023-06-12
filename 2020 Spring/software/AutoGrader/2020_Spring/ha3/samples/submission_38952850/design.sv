// Task 1
// by James Chen 005399315
// for Spring 2020 ECE M16

`timescale 1ns / 1ps

module ha3(
	input CLK, RST, REQ,
	input [15:0] A, D,
	output ACK, FDBZ,
	output [15:0] Q, R
);
  wire signed [15:0] a = A;
  wire signed [15:0] d = D;
  
  //States
  wire [1:0] Sign; // +/+ is 00, +/- is 10, -/+ is 01, -/- is 11
  assign Sign = (a >= 0) ? ((d >= 0) ? 2'b00 : 2'b10) : ((d >= 0) ? 2'b01 : 2'b11);
  wire [1:0] DBZ; // 0/0 is 11, +/0 is 10, -/0 is 01, No error is 00
  assign DBZ = (d == 0) ? ((a >= 0) ? ((a == 0) ? 2'b11 : 2'b10) : 2'b01) : 2'b00;
  reg [5:0] timer;
  reg ERROR, DONE;
  
  //Datapath combinational logic
  wire [15:0] PA; //gets |A|
  assign PA = (a >= 0) ? a : -a;
  //wire [15:0] PD; //gets |D|
  //assign PD = (D >= 0) ? D : ~D + 16'b1;
  wire [15:0] ND; //gets -|D|
  assign ND = (d >= 0) ? -d : d;
  
  //Datapath
  reg [31:0] RemQuo;
  wire [31:0] LRemQuo = RemQuo << 1; //leftshifted value for simplification
  integer x; //value of LRemQuo (because can't figure out how to use signed)
  
  //Output (kind of hard to explain, but basically my division is designed to divide +/+, so signs need to be corrected and also set the correct outputs if there is DBZ error
  assign Q = DBZ[1] ? (DBZ[0] ? 16'h0 : 16'h7fff) : (DBZ[0] ? 16'h8000 : (Sign[1] ? (Sign[0] ? ((RemQuo[31:16] == 16'b0) ? RemQuo[15:0] : RemQuo[15:0] + 16'b1) : (~RemQuo[15:0] + 16'b1)) : (Sign[0] ? ((RemQuo[31:16] == 16'b0) ? (~RemQuo[15:0] + 16'b1) : (~(RemQuo[15:0] + 16'b1) + 16'b1)) : RemQuo[15:0])));
  
  assign R = (DBZ == 2'b0) ? (Sign[0] ? ((RemQuo[31:16] == 16'b0) ? 16'h0 : ~(RemQuo[31:16] + ND) + 16'b1) : RemQuo[31:16]) : 16'h0 ;
  
  assign ACK = DONE;
  assign FDBZ = ERROR;
  
  always @(posedge RST) begin
    RemQuo <= 32'b0;
    timer <= 5'b0;
    ERROR <= 0;
    DONE <= 0;
  end
  
  always @(posedge CLK) begin
    x = LRemQuo + {ND, 16'b0}; //this is just a work-around so this value is signed
    if (REQ == 1 && DONE == 0) begin
      if (!(DBZ == 2'b00)) begin //Divide by 0 error
        ERROR = 1;
        DONE = 1;
      end else if (timer == 0) begin //First clock signal
        RemQuo = {16'b0, PA};
        timer = timer + 5'b1;
      end else if (timer > 16) begin //16 cycles have passed
        timer = timer + 5'b1;
        DONE = 1;
      end else begin //Calculate the division
        if (x < 0) RemQuo = LRemQuo;
        else RemQuo = (LRemQuo + {ND, 16'b0}) + 32'b1;
        timer = timer + 5'b1;
      end
    end else if (REQ == 0 && DONE == 1) begin
      DONE = 0;
      timer = 0;
    end
    
    //$display("%b, %d, Sign = %b, DBZ = %b", RemQuo, a, Sign, DBZ);
  end
endmodule