// Code your testbench here
// or browse Examples

`timescale 1ns / 1ps

module ha2_task3_tb_ref ();
  reg CLK, RST, DIN;
  wire DOUT;
  shortint i, j, k, CYCLE;
  parameter halfperiod = 10;
  integer rngseed = 10;
  
  ha2_task3 ha2_task3_1(.CLK(CLK),.DIN(DIN),.RST(RST),.DOUT(DOUT));

  always begin
    #halfperiod CLK = ~CLK;
  end
  
  always @ (posedge CLK) begin
    $display("%b\t%b\t%b\t%b",CYCLE,RST,DIN,DOUT);
    CYCLE = CYCLE + 1;
  end
  
  initial begin
    $dumpfile("dump.vcd"); $dumpvars;
    CLK = 0;
    RST = 0;
    DIN = 0;
    CYCLE = 0;
    @ (negedge CLK);
    @ (negedge CLK);
    @ (negedge CLK);
    #(halfperiod/2) RST = 1'b1;
    @ (negedge CLK);
    #(halfperiod/2) RST = 1'b0;
  end
  
  initial begin
    @ (negedge RST);
    for (i=0; i<128; i++) begin
      @ (posedge CLK);
      k = $urandom(rngseed) % (2*halfperiod);
      for (j=0; j<k; j++) begin
        # 1ns;
      end
      k = $urandom(rngseed) % 2;
      DIN = k;
    end
    $finish;
  end
endmodule