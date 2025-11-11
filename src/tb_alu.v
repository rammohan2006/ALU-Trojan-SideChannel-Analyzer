// tb_alu.v
`timescale 1ns/1ps

module tb_alu;
    // DUT ports
    reg  [3:0] A, B;
    reg  [1:0] op;
    wire [3:0] Y_clean, Y_trojan;

    // Instantiate both ALUs
    alu_clean  u_clean  (.A(A), .B(B), .op(op), .Y(Y_clean));
    alu_trojan u_trojan (.A(A), .B(B), .op(op), .Y(Y_trojan));

    parameter integer RUN_TYPE    = 0;          // 0=exhaustive, 1=random
    parameter integer NUM_RANDOM  = 1024;
    parameter integer RANDOM_SEED = 32'hFACEB00C;

    integer idx, total_cycles;
    integer rnd_val;
    integer rnd_count;

    // simple toggle signal to keep VCD active
    reg tb_toggle;
    initial tb_toggle = 0;
    always #1 tb_toggle = ~tb_toggle;

    initial begin
        $display("TB: Simulating both ALUs together");
        $display("TB: Simulation started at time %0t", $time);
        $dumpfile("/home/dell/D4-Hardware-Trojan/simulation/alu_both.vcd");
        $dumpvars(0, tb_alu);
    end

    initial begin
        // Initialize
        A = 4'b0000;
        B = 4'b0000;
        op = 2'b00;

        if (RUN_TYPE == 0) begin
            // Exhaustive testing: 4 (op) * 16 (B) * 16 (A) = 1024 vectors
            total_cycles = 4 * 16 * 16;
            for (idx = 0; idx < total_cycles; idx = idx + 1) begin
                A  = idx[3:0];         // low 4 bits
                B  = (idx >> 4) & 4'hF; // next 4 bits
                op = (idx >> 8) & 2'b11; // top 2 bits
                #5;
            end
        end 
        else begin
            // Random testing
            rnd_val = RANDOM_SEED;
            for (rnd_count = 0; rnd_count < NUM_RANDOM; rnd_count = rnd_count + 1) begin
                rnd_val = $random(rnd_val);
                A = rnd_val & 4'hF;
                rnd_val = $random(rnd_val);
                B = rnd_val & 4'hF;
                rnd_val = $random(rnd_val);
                op = rnd_val & 2'b11;
                #5;
            end
        end

        #20;
        $display("TB: Simulation finished at time %0t", $time);
        $finish;
    end

    // TROJAN TRIGGER MONITOR
        always @(*) begin
        if (A == 4'b1111 && B == 4'b1111 && op == 2'b00) begin
            $display("Trojan trigger condition detected at time %0t : A=%b B=%b op=%b",
                     $time, A, B, op);
        end
    end

    // -----------------------------------------------------------------
    // AUTO-CHECK TROJAN BEHAVIOR
    // -----------------------------------------------------------------
    always @(*) begin
        if (A == 4'b1111 && B == 4'b1111 && op == 2'b00) begin
            if (Y_trojan !== (Y_clean ^ 4'b0001)) begin
                $display("Trojan output incorrect at time %0t! Expected %b but got %b",
                         $time, (Y_clean ^ 4'b0001), Y_trojan);
            end else begin
                $display("Trojan flipped correctly at time %0t (Y_clean=%b, Y_trojan=%b)",
                         $time, Y_clean, Y_trojan);
            end
        end
    end

    // RESULT DISPLAY / LOGGING
    always @(*) begin
        $display("Time=%0t | A=%b B=%b op=%b | Clean=%b | Trojan=%b",
                 $time, A, B, op, Y_clean, Y_trojan);
    end

endmodule
