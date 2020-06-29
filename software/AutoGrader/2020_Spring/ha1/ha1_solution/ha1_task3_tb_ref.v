// Testbench

`timescale 1ns / 1ps

module ha1_task3_tb_ref();
  reg [5:0] CODON;
  integer i;
  wire [4:0] AA;
  reg [4:0] AA_correct;
  ha1_task3 ha1_task3_1(.CODON(CODON),.AA(AA));
  
  parameter
  Phenyl_Alanine = 5'b00000, Leucine = 5'b00001, Serine = 5'b00010, 
  Tyrosine = 5'b00011, Stop = 5'b00100, Cysteine = 5'b00101, 
  Tryptophan = 5'b00110, Proline = 5'b00111, Histidine = 5'b01000, 
  Glutamine = 5'b01001, Arginine = 5'b01010, Isoleucine = 5'b01011,
  Methionine = 5'b01100, Threonine = 5'b01101,
  Asparagine = 5'b01110, Lysine = 5'b01111, Valine = 5'b10000,
  Alanine = 5'b10001, Aspartic_Acid = 5'b10010, 
  Glutamic_Acid = 5'b10011, Glycine = 5'b10100,
  G = 2'b00, C = 2'b11, A = 2'b10, U = 2'b01;
  
  initial begin
    //$dumpfile("dump.vcd"); $dumpvars;
    
    for (i=6'b0;i<64;i=i+1) begin
      #2
      CODON = i;
      #1
      case (CODON)
        {G,G,G}, {G,G,A}, {G,G,C}, {G,G,U}: AA_correct = Glycine;
        {G,A,G}, {G,A,A}: AA_correct = Glutamic_Acid;
        {G,A,C}, {G,A,U}: AA_correct = Aspartic_Acid;
        {G,C,G}, {G,C,A}, {G,C,C}, {G,C,U}: AA_correct = Alanine;
        {G,U,G}, {G,U,A}, {G,U,C}, {G,U,U}: AA_correct = Valine;
        {A,G,G}, {A,G,A}: AA_correct = Arginine;
        {A,G,C}, {A,G,U}: AA_correct = Serine;
        {A,A,G}, {A,A,A}: AA_correct = Lysine;
        {A,A,C}, {A,A,U}: AA_correct = Asparagine;
        {A,C,G}, {A,C,A}, {A,C,C}, {A,C,U}: AA_correct = Threonine;
        {A,U,G}: AA_correct = Methionine;
        {A,U,A}, {A,U,C}, {A,U,U}: AA_correct = Isoleucine;
        {C,G,G}, {C,G,A}, {C,G,C}, {C,G,U}: AA_correct = Arginine;
        {C,A,G}, {C,A,A}: AA_correct = Glutamine;
        {C,A,C}, {C,A,U}: AA_correct = Histidine;
        {C,C,G}, {C,C,A}, {C,C,C}, {C,C,U}: AA_correct = Proline;
        {C,U,G}, {C,U,A}, {C,U,C}, {C,U,U}: AA_correct = Leucine;
        {U,G,G}: AA_correct = Tryptophan;
        {U,G,A}: AA_correct = Stop;
        {U,G,C}, {U,G,U}: AA_correct = Cysteine;
        {U,A,G}, {U,A,A}: AA_correct = Stop;
        {U,A,C}, {U,A,U}: AA_correct = Tyrosine;
        {U,C,G}, {U,C,A}, {U,C,C}, {U,C,U}: AA_correct = Serine;
        {U,U,G}, {U,U,A}: AA_correct = Leucine;
        {U,U,C}, {U,U,U}: AA_correct = Phenyl_Alanine;
      endcase;
      #8
      if (AA != AA_correct)
        //$display("ASSERTION ERROR: CODON=%b AA=%b EXPECTED AA=%b", CODON, AA, AA_correct);
        $display("%b\t%b\t%b\t0", CODON, AA_correct, AA);
      else
        //$display("OK: CODON=%b AA=%b", CODON, AA);
        $display("%b\t%b\t%b\t1", CODON, AA_correct, AA);
    end
  end
endmodule