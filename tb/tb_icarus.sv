// SPDX-FileCopyrightText: © 2025 Leo Moser <leo.moser@pm.me>
// SPDX-License-Identifier: Apache-2.0

`timescale 1ns/1ps
`default_nettype none

module tb;

    initial begin
        $dumpfile("tb.fst");
        $dumpvars(0, tb);
    end

    parameter FRAME_BITS_PER_ROW = 32;
    parameter MAX_FRAMES_PER_COL = 20;

    parameter FABRIC_NUM_COLUMNS = 10;
    parameter FABRIC_NUM_ROWS = 10;

    parameter FABRIC_NUM_IO = (FABRIC_NUM_COLUMNS-2)*2+(FABRIC_NUM_ROWS-2)*2;

    wire clk_i;
    wire rst_ni;
    
    // Bitstream
    wire  [31:0] bitstream_data_i;
    wire         bitstream_valid_i;
    
    // Configuration in progress
    wire  busy;
    
    // Fabric is configured
    wire configured;
    
    // To the fabric
    wire [(FRAME_BITS_PER_ROW*FABRIC_NUM_ROWS)-1:0]    frame_data;
    wire [(MAX_FRAMES_PER_COL*FABRIC_NUM_COLUMNS)-1:0] frame_strobe;
    
    // I/Os
    wire [FABRIC_NUM_IO-1:0]      iobuf_in_i;
    wire [FABRIC_NUM_IO-1:0]      iobuf_out_o;
    wire [FABRIC_NUM_IO-1:0]      iobuf_en_o;
    
    wire clk, clk2, rst, en;
    
    assign iobuf_in_i[0] = clk;
    assign iobuf_in_i[1] = clk2;
    assign iobuf_in_i[2] = rst;
    assign iobuf_in_i[3] = en;
    
    wire [FABRIC_NUM_IO-1-4:0]      iobuf_in_upper_i;
    wire [FABRIC_NUM_IO-1-4:0]      iobuf_out_upper_o;
    wire [FABRIC_NUM_IO-1-4:0]      iobuf_en_upper_o;
    
    assign iobuf_in_i[31:4] = iobuf_in_upper_i;
    assign iobuf_out_upper_o = iobuf_out_o[31:4];
    assign iobuf_en_upper_o = iobuf_en_o[31:4];
    
    fabric_config #(
      .FRAME_BITS_PER_ROW   (FRAME_BITS_PER_ROW),
      .MAX_FRAMES_PER_COL   (MAX_FRAMES_PER_COL),
      
      .FABRIC_NUM_COLUMNS   (FABRIC_NUM_COLUMNS),
      .FABRIC_NUM_ROWS      (FABRIC_NUM_ROWS)
    ) fabric_config (
        .clk_i    (clk_i),
        .rst_ni   (rst_ni),
        
        // Bitstream
        .bitstream_data_i   (bitstream_data_i),
        .bitstream_valid_i  (bitstream_valid_i),
        
        // Configuration in progress
        .busy_o           (busy),
        
        // Fabric is configured
        .configured_o     (configured),
        
        // To the fabric
        .frame_data_o     (frame_data),
        .frame_strobe_o   (frame_strobe)
    );
    
    fabric_wrapper fabric_wrapper (
        // Configuration
        .frame_data_i     (frame_data),
        .frame_strobe_i   (frame_strobe),
        
        // I/Os
        .iobuf_in_i       (iobuf_in_i),
        .iobuf_out_o      (iobuf_out_o),
        .iobuf_en_o       (iobuf_en_o)
    );

endmodule

module clk_buf(input A, output X);
assign X = A;
endmodule

module break_comb_loop(input A, output X);
assign #0.1 X = A;
endmodule
