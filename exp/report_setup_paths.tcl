set_param general.maxThreads 1
set exp_checkpoint [lindex $argv 0]
set exp_report [lindex $argv 1]
open_checkpoint $exp_checkpoint
report_timing -delay_type max -max_paths 5 -nworst 1 -sort_by slack -path_type full -file $exp_report
close_design
