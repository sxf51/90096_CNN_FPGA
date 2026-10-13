# ==============================================================
# Vitis HLS - High-Level Synthesis from C, C++ and OpenCL v2026.1 (64-bit)
# Tool Version Limit: 2026.06
# Copyright 1986-2022 Xilinx, Inc. All Rights Reserved.
# Copyright 2022-2026 Advanced Micro Devices, Inc. All Rights Reserved.
# 
# ==============================================================
source ./settings.tcl
source -notrace ./extraction.tcl

set vivado_proj_name project
set vivado_proj_dir .
set target_device "${device}${package}${speed}"
set target_clk_period_ns "4.500"
set target_clk_freq_hz [expr {floor(1000 / $target_clk_period_ns) * 1000000}]
set other_clks_freq_hz {}
set ip_vlnv xilinx.com:hls:srcnn:1.0
set ip_repo_path ../ip
set bd_design_name bd_0
set bd_inst_name hls_inst
set bd_props {}

set has_synth true
set synth_design_args {-directive sdx_optimization_effort_high}
set synth_dcp ""
set synth_props {}

set has_impl 1
set impl_props {}
set has_subcore 1

set report_options [dict create]
dict set report_options report_level 2
dict set report_options report_max_paths 10
dict set report_options stdout_hls_reports 1
dict set report_options stdout_vivado_reports 0
dict set report_options hls_project C21
dict set report_options hls_solution hls
dict set report_options has_synth $has_synth
dict set report_options has_impl $has_impl
dict set report_options vivado_reportbasename $top_module
dict set report_options vivado_reportdir ./report
dict set report_options hls_impl_dir ..
dict set report_options hls_reportdir ../report/$language
dict set report_options target_clk_period $target_clk_period_ns
dict set report_options target_device $target_device
dict set report_options language $language
dict set report_options clock_name $clock
dict set report_options error_if_impl_timing_fails false
dict set report_options topmodule "srcnn"
dict set report_options funcmodules {srcnn_conv12 srcnn_conv1_stream srcnn_conv2_stream srcnn_conv2_stream_Pipeline_continuous_c2_fold srcnn_conv2_stream_Pipeline_local_load_bias srcnn_conv2_stream_Pipeline_local_load_taps srcnn_conv3_stream srcnn_dataflow_region srcnn_distribute_tiles srcnn_engine3 srcnn_engine3_Pipeline_continuous_c3_fold srcnn_engine3_Pipeline_local_load_taps srcnn_online_pad_ap_int_10_4_Pipeline_online_bottom_repeats_online_bottom_write srcnn_online_pad_ap_int_10_4_Pipeline_online_first_read srcnn_online_pad_ap_int_10_4_Pipeline_online_first_repeats_online_first_write srcnn_online_pad_ap_int_10_4_Pipeline_online_rows_online_columns srcnn_online_pad_ap_int_10_4_s srcnn_online_pad_pixel2_2_Pipeline_online_bottom_repeats_online_bottom_write srcnn_online_pad_pixel2_2_Pipeline_online_first_read srcnn_online_pad_pixel2_2_Pipeline_online_first_repeats_online_first_write srcnn_online_pad_pixel2_2_Pipeline_online_rows_online_columns srcnn_online_pad_pixel2_2_s srcnn_read_input srcnn_read_params srcnn_read_raw_params srcnn_reorder_rows srcnn_transform_params1 srcnn_transform_params1_Pipeline_transform_bias srcnn_transform_params1_Pipeline_transform_groups srcnn_transform_params1_Pipeline_transform_read_columns srcnn_windows3 srcnn_wino_engine srcnn_wino_engine_Pipeline_continuous_wino_fold srcnn_wino_engine_Pipeline_wino_local_load_bias srcnn_wino_engine_Pipeline_wino_local_load_groups srcnn_wino_windows srcnn_write_output}
dict set report_options bindmodules {srcnn_add_21s_21s_21_2_1 srcnn_add_22s_22s_22_2_1 srcnn_add_23ns_23ns_23_2_1 srcnn_add_23ns_23s_23_2_1 srcnn_add_23s_23s_23_2_1 srcnn_bitselect_1ns_54ns_6ns_1_1_1 srcnn_control_s_axi srcnn_conv2_stream_p_ZZL12conv2_streamRN3hls6streamIN7numeric6pixel1ELi0EEERNS0_INSeYW srcnn_fifo_w10_d16_D srcnn_fifo_w10_d16_D_x srcnn_fifo_w10_d16_S srcnn_fifo_w10_d36_S srcnn_fifo_w10_d512_A srcnn_fifo_w1728_d16_D srcnn_fifo_w224_d4_D srcnn_fifo_w2560_d17_D srcnn_fifo_w320_d16_D srcnn_fifo_w320_d22_D srcnn_fifo_w4000_d5_D srcnn_fifo_w640_d512_A srcnn_fifo_w640_d5_D srcnn_flow_control_loop_pipe srcnn_flow_control_loop_pipe_sequential_init srcnn_fpext_32ns_64_2_no_dsp_1 srcnn_frp_pipeline_valid srcnn_image_in_m_axi srcnn_image_out_m_axi srcnn_mul_10s_10s_20_1_1 srcnn_mul_14s_12s_26_1_1 srcnn_online_pad_ap_int_10_4_s_row_RAM_2P_BRAM_1R1W srcnn_online_pad_pixel2_2_s_row_RAM_2P_BRAM_1R1W srcnn_parameters_m_axi srcnn_sparsemux_17_3_10_1_1 srcnn_sparsemux_19_4_10_1_1 srcnn_sparsemux_65_5_10_1_1 srcnn_sparsemux_7_2_10_1_1 srcnn_sparsemux_7_2_1_1_1 srcnn_sparsemux_9_2_10_1_1 srcnn_sparsemux_9_3_10_1_1 srcnn_start_for_conv12_U0 srcnn_start_for_conv2_stream_U0 srcnn_start_for_conv3_stream_U0 srcnn_start_for_distribute_tiles_U0 srcnn_start_for_engine3_U0 srcnn_start_for_online_pad_ap_int_10_4_U0 srcnn_start_for_online_pad_pixel2_2_U0 srcnn_start_for_reorder_rows_U0 srcnn_start_for_transform_params1_U0 srcnn_start_for_wino_engine_U0 srcnn_start_for_write_output_U0 srcnn_windows3_windows3_stream_pixel2_0_stream_window3_0_stream_window3_0_line_99_Ri6b srcnn_wino_engine_p_ZZL11wino_engineRN3hls6streamI18transformed_windowLi0EEERNS0_I1kbM srcnn_wino_windows_wino_windows_stream_ap_int_10_0_stream_transformed_window_0_linebkb}
dict set report_options max_module_depth 9



open_project [file normalize ${vivado_proj_dir}/${vivado_proj_name}.xpr]
if { [get_property PROGRESS [get_runs synth_1]] ne "100%" } {
  error "Staged implementation requires completed synthesis"
}
set_param general.maxThreads 1
set_param synth.maxThreads 1
puts "EXP_STAGED_PROJECT_REOPENED"
if { $has_impl } {
  # launch run impl
  if { [llength $impl_props] } {
    set_property -dict $impl_props [get_runs impl_1]
  }
  launch_runs impl_1
  wait_on_run impl_1
  # impl reports
  hls_vivado_reports_impl impl_1 $report_options
}
hls_vivado_reports_finalize $report_options

close_design
close_project
exit
