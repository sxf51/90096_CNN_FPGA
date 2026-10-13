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
set ip_vlnv xilinx.com:hls:srcnn_reload:1.0
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
dict set report_options hls_project C40
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
dict set report_options topmodule "srcnn_reload"
dict set report_options funcmodules {srcnn_reload_conv12 srcnn_reload_conv1_stream srcnn_reload_conv2_stream srcnn_reload_conv2_stream_Pipeline_continuous_c2_fold srcnn_reload_conv2_stream_Pipeline_packed_load_bias srcnn_reload_conv2_stream_Pipeline_packed_load_first srcnn_reload_conv2_stream_Pipeline_packed_load_second srcnn_reload_conv3_stream srcnn_reload_dataflow_region srcnn_reload_distribute_tiles srcnn_reload_engine3 srcnn_reload_engine3_Pipeline_continuous_c3_fold srcnn_reload_engine3_Pipeline_local_load_taps srcnn_reload_online_pad_ap_int_10_4_Pipeline_online_bottom_repeats_online_bottom_write srcnn_reload_online_pad_ap_int_10_4_Pipeline_online_first_read srcnn_reload_online_pad_ap_int_10_4_Pipeline_online_first_repeats_online_first_write srcnn_reload_online_pad_ap_int_10_4_Pipeline_online_rows_online_columns srcnn_reload_online_pad_ap_int_10_4_s srcnn_reload_online_pad_pixel2_2_Pipeline_online_bottom_repeats_online_bottom_write srcnn_reload_online_pad_pixel2_2_Pipeline_online_first_read srcnn_reload_online_pad_pixel2_2_Pipeline_online_first_repeats_online_first_write srcnn_reload_online_pad_pixel2_2_Pipeline_online_rows_online_columns srcnn_reload_online_pad_pixel2_2_s srcnn_reload_params1_write_register srcnn_reload_read_input srcnn_reload_read_params srcnn_reload_read_raw_params srcnn_reload_read_raw_params_Pipeline_read_all_params srcnn_reload_reorder_rows srcnn_reload_transform_params1 srcnn_reload_transform_params1_Pipeline_transform_bias srcnn_reload_transform_params1_Pipeline_transform_groups srcnn_reload_transform_params1_Pipeline_transform_read_columns srcnn_reload_windows3 srcnn_reload_wino_engine srcnn_reload_wino_engine_Pipeline_continuous_wino_fold srcnn_reload_wino_engine_Pipeline_wino_local_load_bias srcnn_reload_wino_engine_Pipeline_wino_local_load_groups srcnn_reload_wino_windows srcnn_reload_write_output}
dict set report_options bindmodules {srcnn_reload_add_19s_19s_19_2_1 srcnn_reload_add_20s_20s_20_2_1 srcnn_reload_add_21ns_21ns_21_2_1 srcnn_reload_add_21s_21s_21_2_1 srcnn_reload_add_22s_22s_22_2_1 srcnn_reload_add_23ns_23ns_23_2_1 srcnn_reload_add_23s_23s_23_2_1 srcnn_reload_bitselect_1ns_54ns_6ns_1_1_1 srcnn_reload_control_s_axi srcnn_reload_conv2_stream_p_ZZL12conv2_streamRN3hls6streamIN7numeric6pixel1ELi0EEERNS0_INSjCb srcnn_reload_engine3_engine3_hls_stream_window3_0_hls_stream_window3_0_hls_stream_ap_int_1nOc srcnn_reload_fifo_w10_d16_D srcnn_reload_fifo_w10_d16_D_x srcnn_reload_fifo_w10_d16_S srcnn_reload_fifo_w10_d512_A srcnn_reload_fifo_w1728_d32_D srcnn_reload_fifo_w224_d4_D srcnn_reload_fifo_w2560_d2_D srcnn_reload_fifo_w320_d16_D srcnn_reload_fifo_w320_d4_D srcnn_reload_fifo_w4000_d2_D srcnn_reload_fifo_w640_d4_D srcnn_reload_fifo_w640_d512_A srcnn_reload_flow_control_loop_pipe srcnn_reload_flow_control_loop_pipe_sequential_init srcnn_reload_fpext_32ns_64_2_no_dsp_1 srcnn_reload_image_in_m_axi srcnn_reload_image_out_m_axi srcnn_reload_mul_10s_10s_20_1_1 srcnn_reload_mul_14s_12s_26_1_1 srcnn_reload_mul_27s_10s_37_1_1 srcnn_reload_online_pad_ap_int_10_4_s_row_RAM_2P_BRAM_1R1W srcnn_reload_online_pad_pixel2_2_s_row_RAM_2P_BRAM_1R1W srcnn_reload_parameters_m_axi srcnn_reload_sparsemux_129_6_8_1_1 srcnn_reload_sparsemux_19_4_10_1_1 srcnn_reload_sparsemux_33_4_10_1_1 srcnn_reload_sparsemux_7_2_10_1_1 srcnn_reload_sparsemux_7_2_1_1_1 srcnn_reload_sparsemux_7_2_8_1_1 srcnn_reload_sparsemux_9_2_10_1_1 srcnn_reload_sparsemux_9_2_8_1_1 srcnn_reload_sparsemux_9_3_10_1_1 srcnn_reload_start_for_conv12_U0 srcnn_reload_start_for_conv2_stream_U0 srcnn_reload_start_for_conv3_stream_U0 srcnn_reload_start_for_distribute_tiles_U0 srcnn_reload_start_for_engine3_U0 srcnn_reload_start_for_online_pad_ap_int_10_4_U0 srcnn_reload_start_for_online_pad_pixel2_2_U0 srcnn_reload_start_for_reorder_rows_U0 srcnn_reload_start_for_transform_params1_U0 srcnn_reload_start_for_wino_engine_U0 srcnn_reload_start_for_write_output_U0 srcnn_reload_windows3_windows3_stream_pixel2_0_stream_window3_0_stream_window3_0_line_RAM_nKc srcnn_reload_wino_engine_p_ZZL11wino_engineRN3hls6streamI18transformed_windowLi0EEERNS0_I1kbM srcnn_reload_wino_windows_wino_windows_stream_ap_int_10_0_stream_transformed_window_0_linebkb}
dict set report_options max_module_depth 9


create_project $vivado_proj_name $vivado_proj_dir -part $target_device -force
set_property target_language $language [current_project]


# setup design sources and constraints

if { ![file exists $ip_repo_path] } {
  error "Cannot find packaged HLS IP"
}
set_property ip_repo_paths [file normalize $ip_repo_path] [current_project]
update_ip_catalog
create_bd_design $bd_design_name

# Instantiate HLS IP
set cell_inst [create_bd_cell -type ip -vlnv $ip_vlnv $bd_inst_name]
if { [llength $bd_props] } { 
  set_property -dict $bd_props $cell_inst 
}

# Update BD pins
make_bd_pins_external $cell_inst
make_bd_intf_pins_external $cell_inst

# Set BD clock port freq property
set bd_clk_ports [get_bd_ports -filter {TYPE==clk}]
if { $target_clk_freq_hz ne "" } { 
  foreach bd_clk_port $bd_clk_ports {
    # Remove "_0" suffix from BD ports & interfaces so they match IP ports 
    set clk_name [regsub {_0$} [get_property name $bd_clk_port] {}]
    set port_freq_hz $target_clk_freq_hz
    if { [dict exists $other_clks_freq_hz $clk_name] } {
        set port_freq_hz [dict get $other_clks_freq_hz $clk_name]
    }
    set_property CONFIG.FREQ_HZ $port_freq_hz $bd_clk_port
  }
}

# Remove "_0" suffix from BD ports & interfaces so they match IP ports (XDC names will match)
foreach bd_port [get_bd_intf_ports] {
  set_property name [regsub {_0$} [get_property name $bd_port] {}] $bd_port
}
foreach bd_port [get_bd_ports -filter {INTF!=TRUE}] {
  set_property name [regsub {_0$} [get_property name $bd_port] {}] $bd_port
}

# Vitis kernels have minimum width for s_axi target address space 
# This changes external port address space, not IP
set s_axi_addr_width_min 32
foreach bd_port [get_bd_intf_ports -filter {MODE == "Slave" && VLNV =~ "xilinx.com:interface:aximm_rtl:*"}] {
  set bd_port_addr_width [get_property CONFIG.ADDR_WIDTH $bd_port]
  if { $bd_port_addr_width < $s_axi_addr_width_min } {
    puts "INFO: Updating $bd_port CONFIG.ADDR_WIDTH to $s_axi_addr_width_min"
    set_property CONFIG.ADDR_WIDTH $s_axi_addr_width_min $bd_port
  }
}

# Downgrade slave segment critical warnings since this is an OOC design
set_msg_config -id {[BD 41-1265]} -severity {CRITICAL WARNING} -new_severity {INFO}

# Use default address assignment
assign_bd_address

# Set top of design to use BD wrapper
set toprtl [make_wrapper -files [get_files ${bd_design_name}.bd] -top]
add_files -norecurse $toprtl
set top_inst_name [file root [file tail $toprtl]]
puts "Using BD top: $top_inst_name"

# Add XDC files
set xdc_files [glob -nocomplain ./*.xdc]
if { [llength $xdc_files] } {
    add_files -fileset constrs_1 -norecurse $xdc_files
}

# Create the ooc run objects without running them
launch_runs synth_1 -scripts_only

# Rest all the synthesis runs
foreach run [get_runs -filter {IS_SYNTHESIS == 1}] {
  reset_run [get_runs $run]
}


set_property XPM_LIBRARIES {XPM_MEMORY XPM_FIFO} [current_project]

set_param general.maxThreads 1
set_param synth.maxThreads 1
foreach exp_run [get_runs -filter {IS_SYNTHESIS == 1}] {
  set_property STEPS.SYNTH_DESIGN.TCL.PRE [file normalize ./serial_synthesis.tcl] $exp_run
}
# EXP_IMPLEMENTATION_STRATEGY_BEGIN
source ./implementation_strategy.tcl
# EXP_IMPLEMENTATION_STRATEGY_END
# EXP_IMPLEMENTATION_THREADS_BEGIN
source ./bounded_implementation.tcl
foreach exp_impl_run [get_runs -filter {IS_IMPLEMENTATION == 1}] {
  set_property STEPS.OPT_DESIGN.TCL.PRE [file normalize ./bounded_implementation.tcl] $exp_impl_run
}
# EXP_IMPLEMENTATION_THREADS_END
hls_vivado_reports_setup $report_options
if { $has_subcore } { report_ip_status }
if { $has_synth || $has_impl } {
  # synth properties setting
  set_property -name {STEPS.SYNTH_DESIGN.ARGS.MORE OPTIONS} -value {-mode out_of_context} -objects [get_runs synth_1]
  set ip_inst [get_ips -quiet ${bd_design_name}*${bd_inst_name}*]
  if { ![llength $ip_inst] } {
      error "Cannot find HLS IP instance: ${bd_design_name}*${bd_inst_name}*"
  }
  set synth_run [get_runs -filter {IS_SYNTHESIS == 1} ${ip_inst}*]
  if { ![llength $synth_run] } {
      error "Cannot find synth run for HLS IP: ${ip_inst}*"
  }

  if { [llength $synth_design_args] } {
      set_property -name {STEPS.SYNTH_DESIGN.ARGS.MORE OPTIONS} -value $synth_design_args -objects $synth_run
  }

  if { [llength $synth_props] } {
    set_property -dict $synth_props $synth_run
  }

  # launch run synth
  launch_runs synth_1
  wait_on_run synth_1
  # synth reports
  hls_vivado_reports_synth synth_1 $report_options
  if { $synth_dcp ne "" } {
    file mkdir [file dirname $synth_dcp]
    set run_dcp [glob -nocomplain [get_property DIRECTORY $synth_run]/*.dcp]
    if { [llength $run_dcp] != 1 } { error "Cannot find single dcp file for run $synth_run" }
    file copy -force $run_dcp $synth_dcp
  }
}



puts "EXP_STAGED_SYNTH_REPORT_DONE"
close_design
close_project
exit
