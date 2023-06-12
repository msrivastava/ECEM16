// Testbench

`timescale 1ns / 1ps

module ha1_task2_tb_ref();
  reg [3:0] A, B, C;
  integer i;
  wire [3:0] MEDIAN;
  reg [3:0] MEDIAN_correct;
  ha1_task2 ha1_task2_1(.A(A),.B(B),.C(C),.MEDIAN(MEDIAN));
  
  initial begin
    //$dumpfile("dump.vcd"); $dumpvars;
    
    for (i=12'b0;i<4096;i=i+1) begin
      #2
      A = i[3:0];
      B = i[7:4];
      C = i[11:8];
      #1
      if ((A>=B && B>=C) || (A<=B && B<=C))
        MEDIAN_correct = B;
      else if ((A>=C && C>=B) || (A<=C && C<=B))
        MEDIAN_correct = C;
      else
        MEDIAN_correct = A;
      #8
      if (MEDIAN != MEDIAN_correct)
        //$display("ASSERTION ERROR: A=%b B=%b C=%b MEDIAN=%b EXPECTED MEDIAN=%b",
        //  A, B, C, MEDIAN, MEDIAN_correct);
        $display("%b\t%b\t%b\t%b\t%b\t0", A, B, C, MEDIAN_correct, MEDIAN);
      else
        //$display("OK: A=%b B=%b C=%b MEDIAN=%b", A, B, C, MEDIAN);
        $display("%b\t%b\t%b\t%b\t%b\t1", A, B, C, MEDIAN_correct, MEDIAN);
    end
  end
endmodule