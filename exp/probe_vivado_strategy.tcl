help phys_opt_design
create_project -in_memory -part xck26-sfvc784-2LV-c
set run [get_runs impl_1]
puts "EXP_SUPPORTED_STRATEGIES [list_property_value STRATEGY $run]"
set_property STRATEGY Performance_Explore $run
set_property STEPS.POST_ROUTE_PHYS_OPT_DESIGN.IS_ENABLED true $run
puts "EXP_STRATEGY_PROBE strategy=[get_property STRATEGY $run] post_route_phys_opt=[get_property STEPS.POST_ROUTE_PHYS_OPT_DESIGN.IS_ENABLED $run]"
