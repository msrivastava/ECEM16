// Code your testbench here
// or browse Examples

`timescale 1ns / 1ps

module ha2_task2_tb_ref ();
  reg CLK, RST, DIN;
  wire DOUT_SHORT, DOUT_LONG;
  shortint i, j, k, CYCLE;
  parameter halfperiod = 10;
  integer rngseed = 10;
  
  ha2_task2 ha2_task2_1(.CLK(CLK),.DIN(DIN),.RST(RST),.DOUT_SHORT(DOUT_SHORT),.DOUT_LONG(DOUT_LONG));

  always begin
    #halfperiod CLK = ~CLK;
  end
  
  always @ (posedge CLK) begin
    $display("%b\t%b\t%b\t%b\t%b",CYCLE,RST,DIN,DOUT_SHORT,DOUT_LONG);
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
    for (i=0; i<100; i++) begin
      @ (posedge CLK);
      k = $urandom(rngseed) % (10*halfperiod);
      for (j=0; j<k; j++) begin
        # 1ns;
      end
      DIN = 1;
      k = $urandom(rngseed)  % (32*halfperiod);
      for (j=0; j<k; j++) begin 
        # 1ns; 
      end
      DIN = 0;
    end
    $finish;
  end
endmodule