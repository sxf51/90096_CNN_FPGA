foreach exp_impl_run [get_runs -filter {IS_IMPLEMENTATION == 1}] {
  set_property strategy Performance_Explore $exp_impl_run
  set_property STEPS.POST_ROUTE_PHYS_OPT_DESIGN.IS_ENABLED true $exp_impl_run
  puts "EXP_VIVADO_STRATEGY run=$exp_impl_run strategy=[get_property STRATEGY $exp_impl_run] post_route_phys_opt=[get_property STEPS.POST_ROUTE_PHYS_OPT_DESIGN.IS_ENABLED $exp_impl_run]"
}
