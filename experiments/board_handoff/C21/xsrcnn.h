// ==============================================================
// Vitis HLS - High-Level Synthesis from C, C++ and OpenCL v2026.1 (64-bit)
// Tool Version Limit: 2026.06
// Copyright 1986-2022 Xilinx, Inc. All Rights Reserved.
// Copyright 2022-2026 Advanced Micro Devices, Inc. All Rights Reserved.
// 
// ==============================================================
#ifndef XSRCNN_H
#define XSRCNN_H

#ifdef __cplusplus
extern "C" {
#endif

/***************************** Include Files *********************************/
#ifndef __linux__
#include "xil_types.h"
#include "xil_assert.h"
#include "xstatus.h"
#include "xil_io.h"
#else
#include <stdint.h>
#include <assert.h>
#include <dirent.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <unistd.h>
#include <stddef.h>
#endif
#include "xsrcnn_hw.h"

/**************************** Type Definitions ******************************/
#ifdef __linux__
typedef uint8_t u8;
typedef uint16_t u16;
typedef uint32_t u32;
typedef uint64_t u64;
#else
typedef struct {
#ifdef SDT
    char *Name;
#else
    u16 DeviceId;
#endif
    u64 Control_BaseAddress;
} XSrcnn_Config;
#endif

typedef struct {
    u64 Control_BaseAddress;
    u32 IsReady;
} XSrcnn;

typedef u32 word_type;

/***************** Macros (Inline Functions) Definitions *********************/
#ifndef __linux__
#define XSrcnn_WriteReg(BaseAddress, RegOffset, Data) \
    Xil_Out32((BaseAddress) + (RegOffset), (u32)(Data))
#define XSrcnn_ReadReg(BaseAddress, RegOffset) \
    Xil_In32((BaseAddress) + (RegOffset))
#else
#define XSrcnn_WriteReg(BaseAddress, RegOffset, Data) \
    *(volatile u32*)((BaseAddress) + (RegOffset)) = (u32)(Data)
#define XSrcnn_ReadReg(BaseAddress, RegOffset) \
    *(volatile u32*)((BaseAddress) + (RegOffset))

#define Xil_AssertVoid(expr)    assert(expr)
#define Xil_AssertNonvoid(expr) assert(expr)

#define XST_SUCCESS             0
#define XST_DEVICE_NOT_FOUND    2
#define XST_OPEN_DEVICE_FAILED  3
#define XIL_COMPONENT_IS_READY  1
#endif

/************************** Function Prototypes *****************************/
#ifndef __linux__
#ifdef SDT
int XSrcnn_Initialize(XSrcnn *InstancePtr, UINTPTR BaseAddress);
XSrcnn_Config* XSrcnn_LookupConfig(UINTPTR BaseAddress);
#else
int XSrcnn_Initialize(XSrcnn *InstancePtr, u16 DeviceId);
XSrcnn_Config* XSrcnn_LookupConfig(u16 DeviceId);
#endif
int XSrcnn_CfgInitialize(XSrcnn *InstancePtr, XSrcnn_Config *ConfigPtr);
#else
int XSrcnn_Initialize(XSrcnn *InstancePtr, const char* InstanceName);
int XSrcnn_Release(XSrcnn *InstancePtr);
#endif

void XSrcnn_Start(XSrcnn *InstancePtr);
u32 XSrcnn_IsDone(XSrcnn *InstancePtr);
u32 XSrcnn_IsIdle(XSrcnn *InstancePtr);
u32 XSrcnn_IsReady(XSrcnn *InstancePtr);
void XSrcnn_EnableAutoRestart(XSrcnn *InstancePtr);
void XSrcnn_DisableAutoRestart(XSrcnn *InstancePtr);

void XSrcnn_Set_in_r(XSrcnn *InstancePtr, u64 Data);
u64 XSrcnn_Get_in_r(XSrcnn *InstancePtr);
void XSrcnn_Set_weights1(XSrcnn *InstancePtr, u64 Data);
u64 XSrcnn_Get_weights1(XSrcnn *InstancePtr);
void XSrcnn_Set_biases1(XSrcnn *InstancePtr, u64 Data);
u64 XSrcnn_Get_biases1(XSrcnn *InstancePtr);
void XSrcnn_Set_weights2(XSrcnn *InstancePtr, u64 Data);
u64 XSrcnn_Get_weights2(XSrcnn *InstancePtr);
void XSrcnn_Set_biases2(XSrcnn *InstancePtr, u64 Data);
u64 XSrcnn_Get_biases2(XSrcnn *InstancePtr);
void XSrcnn_Set_weights3(XSrcnn *InstancePtr, u64 Data);
u64 XSrcnn_Get_weights3(XSrcnn *InstancePtr);
void XSrcnn_Set_biases3(XSrcnn *InstancePtr, u64 Data);
u64 XSrcnn_Get_biases3(XSrcnn *InstancePtr);
void XSrcnn_Set_out_r(XSrcnn *InstancePtr, u64 Data);
u64 XSrcnn_Get_out_r(XSrcnn *InstancePtr);

void XSrcnn_InterruptGlobalEnable(XSrcnn *InstancePtr);
void XSrcnn_InterruptGlobalDisable(XSrcnn *InstancePtr);
void XSrcnn_InterruptEnable(XSrcnn *InstancePtr, u32 Mask);
void XSrcnn_InterruptDisable(XSrcnn *InstancePtr, u32 Mask);
void XSrcnn_InterruptClear(XSrcnn *InstancePtr, u32 Mask);
u32 XSrcnn_InterruptGetEnabled(XSrcnn *InstancePtr);
u32 XSrcnn_InterruptGetStatus(XSrcnn *InstancePtr);

#ifdef __cplusplus
}
#endif

#endif
