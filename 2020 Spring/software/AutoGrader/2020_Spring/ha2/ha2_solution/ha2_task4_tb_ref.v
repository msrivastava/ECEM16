// Code your testbench here
// or browse Examples

`timescale 1ns / 1ps

module ha2_task4_tb_ref ();
  reg CLK, RST, RDY;
  reg [6:0] DIN;
  wire F;
  shortint  i, j, k, CYCLE;
  parameter halfperiod = 10;
  integer rngseed = 10;
  reg [7:0] din_text[0:511];
  
  ha2_task4 ha2_task4_1(.CLK(CLK),.DIN(DIN),.RST(RST),.RDY(RDY),.F(F));

  always begin
    #halfperiod CLK = ~CLK;
  end
  
  always @ (posedge CLK) begin
    $display("%b\t%b\t%b\t%b\t%b",CYCLE,RST,RDY,DIN,F);
    CYCLE = CYCLE + 1;
  end
  
  initial begin
    $dumpfile("dump.vcd"); $dumpvars;
    $readmemh("din.txt", din_text);
    CLK = 0;
    RST = 0;
    DIN = 7'h00;
    RDY = 0;
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
    @ (posedge CLK);
    for (i=0; i<512; i++) begin
      # 1ns;
      k = $urandom(rngseed) % 5;
      //$display("t=",$time,", k=",k);
      if (k>0) begin
        for (j=0; j<k; j++) begin
          RDY = 0;
          @ (posedge CLK);
        end
        # 1ns;
      end
      RDY = 1;
      DIN = din_text[i][6:0];
      @ (posedge CLK);
    end
    # 1ns;
    RDY = 0;
    @ (posedge CLK);
    $finish;
  end
endmodule