// alu_clean.v - 4-bit Clean ALU

module alu_clean (
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
end

endmodule
