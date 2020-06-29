// Testbench

`timescale 1ns / 1ps

module ha1_task5_tb_ref();
  reg [3:0] D1, D0;
  integer i, j;
  wire [6:0] Z;
  reg [6:0] Z_correct;
  ha1_task5 ha1_task5_1(.D1(D1),.D0(D0),.Z(Z));
  
  initial begin
    //$dumpfile("dump.vcd"); $dumpvars;
    
    for (i=4'b0;i<10;i=i+1) begin
      for (j=4'b0;j<10;j=j+1) begin
        #2
        D1 = i;
        D0 = j;
        #1
        Z_correct = 10*D1 + D0;
      	#8
        if (Z != Z_correct)
          //$display("ASSERTION ERROR: D1=%b D0=%b Z=%b EXPECTED Z=%b",
          //         D1, D0, Z, Z_correct);
          $display("%b\t%b\t%b\t%b\t0", D1, D0, Z_correct, Z);
        else
          //$display("OK: D1=%b D0=%b Z=%b", D1, D0, Z);
          $display("%b\t%b\t%b\t%b\t1", D1, D0, Z_correct, Z);
      end
    end
  end
endmodule