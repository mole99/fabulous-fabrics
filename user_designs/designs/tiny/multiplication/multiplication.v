// SPDX-FileCopyrightText: © 2026 FABulous Contributors
// SPDX-License-Identifier: Apache-2.0

`default_nettype none

module multiplication (
    input  wire [4:0] mult_a,
    input  wire [4:0] mult_b,
    output wire [9:0] product
);

    assign product = mult_a * mult_b;

endmodule
