foreach exp_symbol {::AP::printMsg ::AP::check_bin_exist} {
    puts "EXP_MONITOR_COMMAND $exp_symbol [expr {[llength [info commands $exp_symbol]] > 0}]"
}
puts "EXP_MONITOR_DEBUG_EXISTS [info exists ::AESL_AUTOSIM::gDebug]"
if {[info exists ::AESL_AUTOSIM::gDebug]} {
    puts "EXP_MONITOR_DEBUG_VALUE $::AESL_AUTOSIM::gDebug"
}
exit
