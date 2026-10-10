if {$argc != 2} {
    error "Usage: inspect_dsp.tcl routed.dcp output.csv"
}
open_checkpoint [lindex $argv 0]
set output [open [lindex $argv 1] w]
puts $output "cell,property,value"
foreach cell [get_cells -hier -filter {REF_NAME == DSP48E2}] {
    foreach prop {REF_NAME PREADDINSEL AMULTSEL BMULTSEL AREG BREG DREG ADREG MREG PREG INMODEREG USE_MULT USE_SIMD} {
        puts $output "$cell,$prop,[get_property $prop $cell]"
    }
    foreach pin_name {INMODE OPMODE ALUMODE A B C D} {
        foreach pin [get_pins -of_objects $cell -filter "REF_PIN_NAME =~ $pin_name*"] {
            set net [get_nets -of_objects $pin]
            puts $output "$cell,pin_[get_property REF_PIN_NAME $pin],$net"
        }
    }
}
close $output
close_design
