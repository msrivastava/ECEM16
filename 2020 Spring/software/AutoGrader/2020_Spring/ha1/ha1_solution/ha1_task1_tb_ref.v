// Testbench

`timescale 1ns / 1ps

module ha1_task1_tb_ref();
  reg [6:0] A;
  integer i;
  wire [31:0] X3, X2, X1, X0;
  reg [127:0] X_correct;
  reg [31:0] X3_correct, X2_correct, X1_correct, X0_correct;
  ha1_task1 ha1_task1_1(.A(A),.X3(X3),.X2(X2),.X1(X1),.X0(X0));
  
  initial begin
    //$dumpfile("dump.vcd"); $dumpvars;
    
    for (i=7'b0;i<128;i=i+1) begin
      #2
      A = i;
      #1
      X_correct = 128'b1 << i;
      X3_correct = X_correct[127:96];
      X2_correct = X_correct[95:64];
      X1_correct = X_correct[63:32];
      X0_correct = X_correct[31:0];
      #8

      if (X0 !=X0_correct || X1 !=X1_correct || X2 !=X2_correct || X3 !=X3_correct)
        //$display("ASSERTION ERROR: A=%b X3=%b X2=%b X1=%b X0=%b EXPECTED X3=%b X2=%b X1=%b X0=%b",
        //  A, X3, X2, X1, X0, X3_correct, X2_correct, X1_correct, X0_correct);
        $display("%b\t%b\t%b\t%b\t%b\t%b\t%b\t%b\t%b\t0",
          A, X3_correct, X2_correct, X1_correct, X0_correct, X3, X2, X1, X0);
      else
        //$display("OK: A=%b X3=%b X2=%b X1=%b X0=%b", A, X3, X2, X1, X0);
        $display("%b\t%b\t%b\t%b\t%b\t%b\t%b\t%b\t%b\t1",
          A, X3_correct, X2_correct, X1_correct, X0_correct, X3, X2, X1, X0);
    end
  end
endmodule