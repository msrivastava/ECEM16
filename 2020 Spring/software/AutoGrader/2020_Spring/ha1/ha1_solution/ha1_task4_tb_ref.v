// Testbench

`timescale 1ns / 1ps

module ha1_task4_tb_ref();
  reg [4:0] P, K;
  integer i, j;
  wire [4:0] C;
  reg [4:0] C_correct;
  reg [5:0] PplusK;
  ha1_task4 ha1_task4_1(.P(P),.K(K),.C(C));
  
  initial begin
    //$dumpfile("dump.vcd"); $dumpvars;
    
    for (i=5'b0;i<26;i=i+1) begin
      for (j=5'b0;j<26;j=j+1) begin
        #2
        P = i;
        K = j;
        #1
        PplusK = P + K;
        if (PplusK > 5'd25)
          PplusK = PplusK - 5'd26;
        C_correct = PplusK[4:0];
        #8
        if (C != C_correct)
          //$display("ASSERTION ERROR: P=%b K=%b C=%b EXPECTED C=%b",
          //         P, K, C, C_correct);
          $display("%b\t%b\t%b\t%b\t0", P, K, C_correct, C);
        else
          //$display("OK: P=%b K=%b C=%b", P, K, C);
          $display("%b\t%b\t%b\t%b\t1", P, K, C_correct, C);
      end
    end
  end
endmodule