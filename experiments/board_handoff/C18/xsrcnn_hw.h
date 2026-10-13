// ==============================================================
// Vitis HLS - High-Level Synthesis from C, C++ and OpenCL v2026.1 (64-bit)
// Tool Version Limit: 2026.06
// Copyright 1986-2022 Xilinx, Inc. All Rights Reserved.
// Copyright 2022-2026 Advanced Micro Devices, Inc. All Rights Reserved.
// 
// ==============================================================
// control
// 0x00 : Control signals
//        bit 0  - ap_start (Read/Write/COH)
//        bit 1  - ap_done (Read/COR)
//        bit 2  - ap_idle (Read)
//        bit 3  - ap_ready (Read/COR)
//        bit 7  - auto_restart (Read/Write)
//        bit 9  - interrupt (Read)
//        others - reserved
// 0x04 : Global Interrupt Enable Register
//        bit 0  - Global Interrupt Enable (Read/Write)
//        others - reserved
// 0x08 : IP Interrupt Enable Register (Read/Write)
//        bit 0 - enable ap_done interrupt (Read/Write)
//        bit 1 - enable ap_ready interrupt (Read/Write)
//        others - reserved
// 0x0c : IP Interrupt Status Register (Read/TOW)
//        bit 0 - ap_done (Read/TOW)
//        bit 1 - ap_ready (Read/TOW)
//        others - reserved
// 0x10 : Data signal of in_r
//        bit 31~0 - in_r[31:0] (Read/Write)
// 0x14 : Data signal of in_r
//        bit 31~0 - in_r[63:32] (Read/Write)
// 0x18 : reserved
// 0x1c : Data signal of weights1
//        bit 31~0 - weights1[31:0] (Read/Write)
// 0x20 : Data signal of weights1
//        bit 31~0 - weights1[63:32] (Read/Write)
// 0x24 : reserved
// 0x28 : Data signal of biases1
//        bit 31~0 - biases1[31:0] (Read/Write)
// 0x2c : Data signal of biases1
//        bit 31~0 - biases1[63:32] (Read/Write)
// 0x30 : reserved
// 0x34 : Data signal of weights2
//        bit 31~0 - weights2[31:0] (Read/Write)
// 0x38 : Data signal of weights2
//        bit 31~0 - weights2[63:32] (Read/Write)
// 0x3c : reserved
// 0x40 : Data signal of biases2
//        bit 31~0 - biases2[31:0] (Read/Write)
// 0x44 : Data signal of biases2
//        bit 31~0 - biases2[63:32] (Read/Write)
// 0x48 : reserved
// 0x4c : Data signal of weights3
//        bit 31~0 - weights3[31:0] (Read/Write)
// 0x50 : Data signal of weights3
//        bit 31~0 - weights3[63:32] (Read/Write)
// 0x54 : reserved
// 0x58 : Data signal of biases3
//        bit 31~0 - biases3[31:0] (Read/Write)
// 0x5c : Data signal of biases3
//        bit 31~0 - biases3[63:32] (Read/Write)
// 0x60 : reserved
// 0x64 : Data signal of out_r
//        bit 31~0 - out_r[31:0] (Read/Write)
// 0x68 : Data signal of out_r
//        bit 31~0 - out_r[63:32] (Read/Write)
// 0x6c : reserved
// (SC = Self Clear, COR = Clear on Read, TOW = Toggle on Write, COH = Clear on Handshake)

#define XSRCNN_CONTROL_ADDR_AP_CTRL       0x00
#define XSRCNN_CONTROL_ADDR_GIE           0x04
#define XSRCNN_CONTROL_ADDR_IER           0x08
#define XSRCNN_CONTROL_ADDR_ISR           0x0c
#define XSRCNN_CONTROL_ADDR_IN_R_DATA     0x10
#define XSRCNN_CONTROL_BITS_IN_R_DATA     64
#define XSRCNN_CONTROL_ADDR_WEIGHTS1_DATA 0x1c
#define XSRCNN_CONTROL_BITS_WEIGHTS1_DATA 64
#define XSRCNN_CONTROL_ADDR_BIASES1_DATA  0x28
#define XSRCNN_CONTROL_BITS_BIASES1_DATA  64
#define XSRCNN_CONTROL_ADDR_WEIGHTS2_DATA 0x34
#define XSRCNN_CONTROL_BITS_WEIGHTS2_DATA 64
#define XSRCNN_CONTROL_ADDR_BIASES2_DATA  0x40
#define XSRCNN_CONTROL_BITS_BIASES2_DATA  64
#define XSRCNN_CONTROL_ADDR_WEIGHTS3_DATA 0x4c
#define XSRCNN_CONTROL_BITS_WEIGHTS3_DATA 64
#define XSRCNN_CONTROL_ADDR_BIASES3_DATA  0x58
#define XSRCNN_CONTROL_BITS_BIASES3_DATA  64
#define XSRCNN_CONTROL_ADDR_OUT_R_DATA    0x64
#define XSRCNN_CONTROL_BITS_OUT_R_DATA    64

