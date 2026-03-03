// SPDX-FileCopyrightText: © 2026 FABulous Contributors
// SPDX-License-Identifier: Apache-2.0

`default_nettype none

module counter (
    input  wire       clk1,
    input  wire       rst,
    input  wire       ena,
    
    output wire [21:0] d
);

    wire clk1_buf;

    (* keep, BEL="X0Y4.A" *) GBUF clock_buf (
      .IN   (clk1),
      .OUT  (clk1_buf)
    );

    reg [21:0] ctr1;

    // Reset before enable
    always @(posedge clk1_buf) begin
        if (rst) begin
            ctr1 <= '0;
        end else begin
            if (ena) begin
                ctr1 <= ctr1 + 1'b1;
            end
        end
    end

    // Enable before reset
    /*always @(posedge clk1_buf) begin
        if (ena) begin
            if (rst) begin
                ctr1 <= '0;
            end else begin
                ctr1 <= ctr1 + 1'b1;
            end
        end
    end*/

    assign d = ctr1;

endmodule
