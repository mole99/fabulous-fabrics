// SPDX-FileCopyrightText: © 2026 FABulous Contributors
// SPDX-License-Identifier: Apache-2.0

`default_nettype none

module all_zeros (
    output wire [5:0] a,
    output wire [5:0] b,
    output wire [7:0] c
);

    assign a = '0;
    assign b = '0;
    assign c = '0;

endmodule
