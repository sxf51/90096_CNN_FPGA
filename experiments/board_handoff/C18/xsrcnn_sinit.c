// ==============================================================
// Vitis HLS - High-Level Synthesis from C, C++ and OpenCL v2026.1 (64-bit)
// Tool Version Limit: 2026.06
// Copyright 1986-2022 Xilinx, Inc. All Rights Reserved.
// Copyright 2022-2026 Advanced Micro Devices, Inc. All Rights Reserved.
// 
// ==============================================================
#ifndef __linux__

#include "xstatus.h"
#ifdef SDT
#include "xparameters.h"
#endif
#include "xsrcnn.h"

extern XSrcnn_Config XSrcnn_ConfigTable[];

#ifdef SDT
XSrcnn_Config *XSrcnn_LookupConfig(UINTPTR BaseAddress) {
	XSrcnn_Config *ConfigPtr = NULL;

	int Index;

	for (Index = (u32)0x0; XSrcnn_ConfigTable[Index].Name != NULL; Index++) {
		if (!BaseAddress || XSrcnn_ConfigTable[Index].Control_BaseAddress == BaseAddress) {
			ConfigPtr = &XSrcnn_ConfigTable[Index];
			break;
		}
	}

	return ConfigPtr;
}

int XSrcnn_Initialize(XSrcnn *InstancePtr, UINTPTR BaseAddress) {
	XSrcnn_Config *ConfigPtr;

	Xil_AssertNonvoid(InstancePtr != NULL);

	ConfigPtr = XSrcnn_LookupConfig(BaseAddress);
	if (ConfigPtr == NULL) {
		InstancePtr->IsReady = 0;
		return (XST_DEVICE_NOT_FOUND);
	}

	return XSrcnn_CfgInitialize(InstancePtr, ConfigPtr);
}
#else
XSrcnn_Config *XSrcnn_LookupConfig(u16 DeviceId) {
	XSrcnn_Config *ConfigPtr = NULL;

	int Index;

	for (Index = 0; Index < XPAR_XSRCNN_NUM_INSTANCES; Index++) {
		if (XSrcnn_ConfigTable[Index].DeviceId == DeviceId) {
			ConfigPtr = &XSrcnn_ConfigTable[Index];
			break;
		}
	}

	return ConfigPtr;
}

int XSrcnn_Initialize(XSrcnn *InstancePtr, u16 DeviceId) {
	XSrcnn_Config *ConfigPtr;

	Xil_AssertNonvoid(InstancePtr != NULL);

	ConfigPtr = XSrcnn_LookupConfig(DeviceId);
	if (ConfigPtr == NULL) {
		InstancePtr->IsReady = 0;
		return (XST_DEVICE_NOT_FOUND);
	}

	return XSrcnn_CfgInitialize(InstancePtr, ConfigPtr);
}
#endif

#endif

