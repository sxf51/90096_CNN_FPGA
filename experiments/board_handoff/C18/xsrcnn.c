// ==============================================================
// Vitis HLS - High-Level Synthesis from C, C++ and OpenCL v2026.1 (64-bit)
// Tool Version Limit: 2026.06
// Copyright 1986-2022 Xilinx, Inc. All Rights Reserved.
// Copyright 2022-2026 Advanced Micro Devices, Inc. All Rights Reserved.
// 
// ==============================================================
/***************************** Include Files *********************************/
#include "xsrcnn.h"

/************************** Function Implementation *************************/
#ifndef __linux__
int XSrcnn_CfgInitialize(XSrcnn *InstancePtr, XSrcnn_Config *ConfigPtr) {
    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(ConfigPtr != NULL);

    InstancePtr->Control_BaseAddress = ConfigPtr->Control_BaseAddress;
    InstancePtr->IsReady = XIL_COMPONENT_IS_READY;

    return XST_SUCCESS;
}
#endif

void XSrcnn_Start(XSrcnn *InstancePtr) {
    u32 Data;

    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XSrcnn_ReadReg(InstancePtr->Control_BaseAddress, XSRCNN_CONTROL_ADDR_AP_CTRL) & 0x80;
    XSrcnn_WriteReg(InstancePtr->Control_BaseAddress, XSRCNN_CONTROL_ADDR_AP_CTRL, Data | 0x01);
}

u32 XSrcnn_IsDone(XSrcnn *InstancePtr) {
    u32 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XSrcnn_ReadReg(InstancePtr->Control_BaseAddress, XSRCNN_CONTROL_ADDR_AP_CTRL);
    return (Data >> 1) & 0x1;
}

u32 XSrcnn_IsIdle(XSrcnn *InstancePtr) {
    u32 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XSrcnn_ReadReg(InstancePtr->Control_BaseAddress, XSRCNN_CONTROL_ADDR_AP_CTRL);
    return (Data >> 2) & 0x1;
}

u32 XSrcnn_IsReady(XSrcnn *InstancePtr) {
    u32 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XSrcnn_ReadReg(InstancePtr->Control_BaseAddress, XSRCNN_CONTROL_ADDR_AP_CTRL);
    // check ap_start to see if the pcore is ready for next input
    return !(Data & 0x1);
}

void XSrcnn_EnableAutoRestart(XSrcnn *InstancePtr) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XSrcnn_WriteReg(InstancePtr->Control_BaseAddress, XSRCNN_CONTROL_ADDR_AP_CTRL, 0x80);
}

void XSrcnn_DisableAutoRestart(XSrcnn *InstancePtr) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XSrcnn_WriteReg(InstancePtr->Control_BaseAddress, XSRCNN_CONTROL_ADDR_AP_CTRL, 0);
}

void XSrcnn_Set_in_r(XSrcnn *InstancePtr, u64 Data) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XSrcnn_WriteReg(InstancePtr->Control_BaseAddress, XSRCNN_CONTROL_ADDR_IN_R_DATA, (u32)(Data));
    XSrcnn_WriteReg(InstancePtr->Control_BaseAddress, XSRCNN_CONTROL_ADDR_IN_R_DATA + 4, (u32)(Data >> 32));
}

u64 XSrcnn_Get_in_r(XSrcnn *InstancePtr) {
    u64 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XSrcnn_ReadReg(InstancePtr->Control_BaseAddress, XSRCNN_CONTROL_ADDR_IN_R_DATA);
    Data += (u64)XSrcnn_ReadReg(InstancePtr->Control_BaseAddress, XSRCNN_CONTROL_ADDR_IN_R_DATA + 4) << 32;
    return Data;
}

void XSrcnn_Set_weights1(XSrcnn *InstancePtr, u64 Data) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XSrcnn_WriteReg(InstancePtr->Control_BaseAddress, XSRCNN_CONTROL_ADDR_WEIGHTS1_DATA, (u32)(Data));
    XSrcnn_WriteReg(InstancePtr->Control_BaseAddress, XSRCNN_CONTROL_ADDR_WEIGHTS1_DATA + 4, (u32)(Data >> 32));
}

u64 XSrcnn_Get_weights1(XSrcnn *InstancePtr) {
    u64 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XSrcnn_ReadReg(InstancePtr->Control_BaseAddress, XSRCNN_CONTROL_ADDR_WEIGHTS1_DATA);
    Data += (u64)XSrcnn_ReadReg(InstancePtr->Control_BaseAddress, XSRCNN_CONTROL_ADDR_WEIGHTS1_DATA + 4) << 32;
    return Data;
}

void XSrcnn_Set_biases1(XSrcnn *InstancePtr, u64 Data) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XSrcnn_WriteReg(InstancePtr->Control_BaseAddress, XSRCNN_CONTROL_ADDR_BIASES1_DATA, (u32)(Data));
    XSrcnn_WriteReg(InstancePtr->Control_BaseAddress, XSRCNN_CONTROL_ADDR_BIASES1_DATA + 4, (u32)(Data >> 32));
}

u64 XSrcnn_Get_biases1(XSrcnn *InstancePtr) {
    u64 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XSrcnn_ReadReg(InstancePtr->Control_BaseAddress, XSRCNN_CONTROL_ADDR_BIASES1_DATA);
    Data += (u64)XSrcnn_ReadReg(InstancePtr->Control_BaseAddress, XSRCNN_CONTROL_ADDR_BIASES1_DATA + 4) << 32;
    return Data;
}

void XSrcnn_Set_weights2(XSrcnn *InstancePtr, u64 Data) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XSrcnn_WriteReg(InstancePtr->Control_BaseAddress, XSRCNN_CONTROL_ADDR_WEIGHTS2_DATA, (u32)(Data));
    XSrcnn_WriteReg(InstancePtr->Control_BaseAddress, XSRCNN_CONTROL_ADDR_WEIGHTS2_DATA + 4, (u32)(Data >> 32));
}

u64 XSrcnn_Get_weights2(XSrcnn *InstancePtr) {
    u64 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XSrcnn_ReadReg(InstancePtr->Control_BaseAddress, XSRCNN_CONTROL_ADDR_WEIGHTS2_DATA);
    Data += (u64)XSrcnn_ReadReg(InstancePtr->Control_BaseAddress, XSRCNN_CONTROL_ADDR_WEIGHTS2_DATA + 4) << 32;
    return Data;
}

void XSrcnn_Set_biases2(XSrcnn *InstancePtr, u64 Data) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XSrcnn_WriteReg(InstancePtr->Control_BaseAddress, XSRCNN_CONTROL_ADDR_BIASES2_DATA, (u32)(Data));
    XSrcnn_WriteReg(InstancePtr->Control_BaseAddress, XSRCNN_CONTROL_ADDR_BIASES2_DATA + 4, (u32)(Data >> 32));
}

u64 XSrcnn_Get_biases2(XSrcnn *InstancePtr) {
    u64 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XSrcnn_ReadReg(InstancePtr->Control_BaseAddress, XSRCNN_CONTROL_ADDR_BIASES2_DATA);
    Data += (u64)XSrcnn_ReadReg(InstancePtr->Control_BaseAddress, XSRCNN_CONTROL_ADDR_BIASES2_DATA + 4) << 32;
    return Data;
}

void XSrcnn_Set_weights3(XSrcnn *InstancePtr, u64 Data) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XSrcnn_WriteReg(InstancePtr->Control_BaseAddress, XSRCNN_CONTROL_ADDR_WEIGHTS3_DATA, (u32)(Data));
    XSrcnn_WriteReg(InstancePtr->Control_BaseAddress, XSRCNN_CONTROL_ADDR_WEIGHTS3_DATA + 4, (u32)(Data >> 32));
}

u64 XSrcnn_Get_weights3(XSrcnn *InstancePtr) {
    u64 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XSrcnn_ReadReg(InstancePtr->Control_BaseAddress, XSRCNN_CONTROL_ADDR_WEIGHTS3_DATA);
    Data += (u64)XSrcnn_ReadReg(InstancePtr->Control_BaseAddress, XSRCNN_CONTROL_ADDR_WEIGHTS3_DATA + 4) << 32;
    return Data;
}

void XSrcnn_Set_biases3(XSrcnn *InstancePtr, u64 Data) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XSrcnn_WriteReg(InstancePtr->Control_BaseAddress, XSRCNN_CONTROL_ADDR_BIASES3_DATA, (u32)(Data));
    XSrcnn_WriteReg(InstancePtr->Control_BaseAddress, XSRCNN_CONTROL_ADDR_BIASES3_DATA + 4, (u32)(Data >> 32));
}

u64 XSrcnn_Get_biases3(XSrcnn *InstancePtr) {
    u64 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XSrcnn_ReadReg(InstancePtr->Control_BaseAddress, XSRCNN_CONTROL_ADDR_BIASES3_DATA);
    Data += (u64)XSrcnn_ReadReg(InstancePtr->Control_BaseAddress, XSRCNN_CONTROL_ADDR_BIASES3_DATA + 4) << 32;
    return Data;
}

void XSrcnn_Set_out_r(XSrcnn *InstancePtr, u64 Data) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XSrcnn_WriteReg(InstancePtr->Control_BaseAddress, XSRCNN_CONTROL_ADDR_OUT_R_DATA, (u32)(Data));
    XSrcnn_WriteReg(InstancePtr->Control_BaseAddress, XSRCNN_CONTROL_ADDR_OUT_R_DATA + 4, (u32)(Data >> 32));
}

u64 XSrcnn_Get_out_r(XSrcnn *InstancePtr) {
    u64 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XSrcnn_ReadReg(InstancePtr->Control_BaseAddress, XSRCNN_CONTROL_ADDR_OUT_R_DATA);
    Data += (u64)XSrcnn_ReadReg(InstancePtr->Control_BaseAddress, XSRCNN_CONTROL_ADDR_OUT_R_DATA + 4) << 32;
    return Data;
}

void XSrcnn_InterruptGlobalEnable(XSrcnn *InstancePtr) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XSrcnn_WriteReg(InstancePtr->Control_BaseAddress, XSRCNN_CONTROL_ADDR_GIE, 1);
}

void XSrcnn_InterruptGlobalDisable(XSrcnn *InstancePtr) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XSrcnn_WriteReg(InstancePtr->Control_BaseAddress, XSRCNN_CONTROL_ADDR_GIE, 0);
}

void XSrcnn_InterruptEnable(XSrcnn *InstancePtr, u32 Mask) {
    u32 Register;

    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Register =  XSrcnn_ReadReg(InstancePtr->Control_BaseAddress, XSRCNN_CONTROL_ADDR_IER);
    XSrcnn_WriteReg(InstancePtr->Control_BaseAddress, XSRCNN_CONTROL_ADDR_IER, Register | Mask);
}

void XSrcnn_InterruptDisable(XSrcnn *InstancePtr, u32 Mask) {
    u32 Register;

    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Register =  XSrcnn_ReadReg(InstancePtr->Control_BaseAddress, XSRCNN_CONTROL_ADDR_IER);
    XSrcnn_WriteReg(InstancePtr->Control_BaseAddress, XSRCNN_CONTROL_ADDR_IER, Register & (~Mask));
}

void XSrcnn_InterruptClear(XSrcnn *InstancePtr, u32 Mask) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XSrcnn_WriteReg(InstancePtr->Control_BaseAddress, XSRCNN_CONTROL_ADDR_ISR, Mask);
}

u32 XSrcnn_InterruptGetEnabled(XSrcnn *InstancePtr) {
    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    return XSrcnn_ReadReg(InstancePtr->Control_BaseAddress, XSRCNN_CONTROL_ADDR_IER);
}

u32 XSrcnn_InterruptGetStatus(XSrcnn *InstancePtr) {
    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    return XSrcnn_ReadReg(InstancePtr->Control_BaseAddress, XSRCNN_CONTROL_ADDR_ISR);
}

