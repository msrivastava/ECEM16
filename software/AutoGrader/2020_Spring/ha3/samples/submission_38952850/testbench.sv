// Task 1 TestBench
// by James Chen 005399315
// for Spring 2020 ECE M16

`timescale 1ns / 1ps

module ha3_tb();
  reg CLK, RST, REQ, ACK, FDBZ;
  reg [15:0] A,D,Q,R;
  
  ha3 test(.CLK(CLK),.RST(RST),.REQ(REQ),.A(A),.D(D),.ACK(ACK),.FDBZ(FDBZ),.Q(Q),.R(R));
  
  initial begin
    $dumpfile("dump.vcd"); $dumpvars;
        
    RST = 1;
    REQ = 0;
    A = 0;
    D = 0;
    CLK = 1; #1
    $display("RESET: CLK = %b RST = %b REQ = %b, A = %h, D = %h, ACK = %b, FDBZ = %b, Q = %h, R = %h", CLK, RST, REQ, A, D, ACK, FDBZ, Q, R);
    
    RST = 0;
    CLK = 0; #1
    $display("RESET: CLK = %b RST = %b REQ = %b, A = %h, D = %h, ACK = %b, FDBZ = %b, Q = %h, R = %h", CLK, RST, REQ, A, D, ACK, FDBZ, Q, R);
    
    REQ = 1;
    A = 9;
    D = 2;
    CLK = 1; #1
    $display("9/2: CLK = %b RST = %b REQ = %b, A = %h, D = %h, ACK = %b, FDBZ = %b, Q = %h, R = %h", CLK, RST, REQ, A, D, ACK, FDBZ, Q, R);
    
    CLK = 0; #1
    CLK = 1; #1 //1
    CLK = 0; #1
    CLK = 1; #1 //2
    CLK = 0; #1
    CLK = 1; #1 //3
    CLK = 0; #1
    CLK = 1; #1 //4
    CLK = 0; #1
    CLK = 1; #1 //5
    CLK = 0; #1
    CLK = 1; #1 //6
    CLK = 0; #1
    CLK = 1; #1 //7
    CLK = 0; #1
    CLK = 1; #1 //8
    CLK = 0; #1
    CLK = 1; #1 //9
    CLK = 0; #1
    CLK = 1; #1 //10
    CLK = 0; #1
    CLK = 1; #1 //11
    CLK = 0; #1
    CLK = 1; #1 //12
    CLK = 0; #1
    CLK = 1; #1 //13
    CLK = 0; #1
    CLK = 1; #1 //14
    CLK = 0; #1
    CLK = 1; #1 //15
    CLK = 0; #1
    CLK = 1; #1 //16
    $display("9/2: CLK = %b RST = %b REQ = %b, A = %h, D = %h, ACK = %b, FDBZ = %b, Q = %h, R = %h", CLK, RST, REQ, A, D, ACK, FDBZ, Q, R);
    CLK = 0; #1
    CLK = 1; #1 //17
    $display("9/2: CLK = %b RST = %b REQ = %b, A = %h, D = %h, ACK = %b, FDBZ = %b, Q = %h, R = %h", CLK, RST, REQ, A, D, ACK, FDBZ, Q, R);
    
    CLK = 0; #1
    CLK = 1; #1 //keep
    $display("9/2: CLK = %b RST = %b REQ = %b, A = %h, D = %h, ACK = %b, FDBZ = %b, Q = %h, R = %h", CLK, RST, REQ, A, D, ACK, FDBZ, Q, R);
    
    REQ = 0; //end division
    CLK = 0; #1
    CLK = 1; #1
    CLK = 0; #1
    
    //-9/2
    REQ = 1;
    A = 9;
    D = -2;
    CLK = 1; #1
    $display("9/-2: CLK = %b RST = %b REQ = %b, A = %h, D = %h, ACK = %b, FDBZ = %b, Q = %h, R = %h", CLK, RST, REQ, A, D, ACK, FDBZ, Q, R);
    
    CLK = 0; #1
    CLK = 1; #1 //1
    CLK = 0; #1
    CLK = 1; #1 //2
    CLK = 0; #1
    CLK = 1; #1 //3
    CLK = 0; #1
    CLK = 1; #1 //4
    CLK = 0; #1
    CLK = 1; #1 //5
    CLK = 0; #1
    CLK = 1; #1 //6
    CLK = 0; #1
    CLK = 1; #1 //7
    CLK = 0; #1
    CLK = 1; #1 //8
    CLK = 0; #1
    CLK = 1; #1 //9
    CLK = 0; #1
    CLK = 1; #1 //10
    CLK = 0; #1
    CLK = 1; #1 //11
    CLK = 0; #1
    CLK = 1; #1 //12
    CLK = 0; #1
    CLK = 1; #1 //13
    CLK = 0; #1
    CLK = 1; #1 //14
    CLK = 0; #1
    CLK = 1; #1 //15
    CLK = 0; #1
    CLK = 1; #1 //16
    CLK = 0; #1
    CLK = 1; #1 //17
    $display("9/-2: CLK = %b RST = %b REQ = %b, A = %h, D = %h, ACK = %b, FDBZ = %b, Q = %h, R = %h", CLK, RST, REQ, A, D, ACK, FDBZ, Q, R);
    
    CLK = 0; #1
    REQ = 0; //next
    CLK = 1; #1
    CLK = 0; #1
    
    //test dbz case
    REQ = 1;
    D = 0;
    CLK = 1; #1
    CLK = 0; #1
    $display("9/0: CLK = %b RST = %b REQ = %b, A = %h, D = %h, ACK = %b, FDBZ = %b, Q = %h, R = %h", CLK, RST, REQ, A, D, ACK, FDBZ, Q, R);
    
    
    CLK = 1; #1
    CLK = 0; #1
    REQ = 0;
    CLK = 1;
  end  
endmodule