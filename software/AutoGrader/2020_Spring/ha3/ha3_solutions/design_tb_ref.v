// Code your testbench here
// or browse Examples

// CYCLE RST REQ A D Q R FDBZ ACK REQNUM
`timescale 1ns / 1ps

module design_tb_ref ();
  reg CLK, RST, REQ;
  reg signed [15:0] A, D;
  wire ACK, FDBZ;
  reg oldACK;
  wire signed [15:0] Q, R;
  shortint  ia, id, j, k, CYCLE, REQNUM, ACKNUM;
  parameter halfperiod = 10;
  integer rngseed = 10;
  reg signed [15:0] vals[16];
  
  ha3 ha3_t(.CLK(CLK), .RST(RST), .REQ(REQ), .A(A), 
            .D(D), .ACK(ACK), .FDBZ(FDBZ), .Q(Q), .R(R));

  always begin
    #halfperiod CLK = ~CLK;
  end
  
task handle_clock;
   begin
    $display("%b\t%b\t%b\t%b\t%b\t%b\t%b\t%b\t%b\t%b\t%b",
      CYCLE,RST,REQ,A,D,Q,R,FDBZ,ACK,REQNUM,ACKNUM);
    oldACK = ACK;
    CYCLE = CYCLE + 1;
    //if (CYCLE==4000) begin
    //  $finish;
    //end
   end
 endtask

  //always @ (posedge CLK) begin
 task handle_clock_edap;
   begin
    if (ACK==1 && oldACK==0) begin
      //$display("%d\t%b\t%b\t%d\t%d\t%d\t%d\t%b\t%b\t%d\t%d\t*",
      $display("%d\t%b\t%b\t%d\t%d\t%d\t%d\t%b\t%b\t%d\t%d\t*",
               CYCLE,RST,REQ,A,D,Q,R,FDBZ,ACK,REQNUM,ACKNUM);
    end
    else begin
      $display("%d\t%b\t%b\t%d\t%d\t%d\t%d\t%b\t%b\t%d\t%d",
               CYCLE,RST,REQ,A,D,Q,R,FDBZ,ACK,REQNUM,ACKNUM);
    end
    oldACK = ACK;
    CYCLE = CYCLE + 1;
    //if (CYCLE==4000) begin
    //  $finish;
    //end
   end
 endtask
  
  initial begin
    $dumpfile("dump.vcd"); $dumpvars;
    oldACK = 1'bx;
    vals[0] = 16'h8000;
    vals[1] = 16'hffff;
    vals[2] = 16'h0000;
    vals[3] = 16'h0001;
    vals[4] = 16'h7fff;
    vals[5] = 16'h0002;
    vals[6] = 16'h0003;
    vals[7] = 16'h0004;
    vals[8] = 16'h0009;
    vals[9] = 16'h0064;
    vals[10] = 16'hfffe;
    vals[11] = 16'hfffd;
    vals[12] = 16'hfffc;
    vals[13] = 16'hfff7;
    vals[14] = 16'hff9c;
    vals[15] = 16'hf0ff;
    // foreach (vals[i]) $display("%d",vals[i]);
    CLK = 0;
    RST = 0;
    A = 16'h0000;
    D = 16'h0000;
    REQ = 0;
    CYCLE = 0;
    @ (negedge CLK);
    @ (negedge CLK);
    @ (negedge CLK);
    #(halfperiod/2) RST = 1'b1;
    @ (negedge CLK);
    #(halfperiod/2) RST = 1'b0;
  end
  
  initial begin
    REQNUM = 0;
    ACKNUM = 0;
    while (RST==0) begin
      @ (posedge CLK);
      handle_clock;
    end
    while (RST==1) begin
      @ (posedge CLK);
      handle_clock;
    end
    //@ (negedge RST);
    //@ (posedge CLK);
    handle_clock;
    for (ia=0; ia<16; ia++) begin
      for (id=0; id<16; id++) begin
        # 1ns;
        k = $urandom(rngseed) % 5;
        if (k>0) begin
           REQ = 0;
          for (j=0; j<k; j++) begin
            @ (posedge CLK);
            handle_clock;
          end
          # 1ns;
        end
        REQ = 1;
        REQNUM = REQNUM + 1;
        A = vals[ia];
        D = vals[id];
        while (ACK!=1) begin
          @ (posedge CLK);
          handle_clock;
        end
        ACKNUM = ACKNUM + 1;
        //$display("*");
        # 1ns;
        A = 16'h0;
        D = 16'h0;
        k = $urandom(rngseed) % 5;
        if (k>0) begin
          for (j=0; j<k; j++) begin
            @ (posedge CLK);
            handle_clock;
          end
          # 1ns;
        end
        REQ = 0;
        while (ACK!=0) begin
          @ (posedge CLK);
          handle_clock;
        end
      end
    end
    # 1ns;
    @ (posedge CLK);
    handle_clock;
    $finish;
  end
endmodule