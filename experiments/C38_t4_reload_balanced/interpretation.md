C38 passes all13 E065-exact images with unchanged border and mean PSNR delta.
All three compute folds achieve II1, and DSP/BRAM remain1032/146BRAM18K.
The HLS top reports131780LUT and248672FF. FF exceeds the230000 screening line,
so this attempt conservatively stops before new RTL or routing. Final physical
resources and timing are unknown; retain its infeasible HLS result and review
a separately planned diagnostic route later rather than silently overriding
the screen or publishing a hypothetical speedup.

The tree's Winograd fold explains the added FF: C32 reports23858 parent-register
FF and zero instance FF, whereas C38 has19154parent-register FF plus59392instance
FF, totaling78546. Net increase is54688FF, beyond the paper32640FF allowance
by67.55percent; the entire design is9.73percent above its226624FF estimate.
The multiplication count is unchanged. The plan counted one full-width output
register per tree node but omitted the generated fabric-add core's internal
partial-sum/carry/upper-operand storage and pipeline alignment. Registered add
instances have their own HLS resource models: add_25ns_25ns_25_2_1 reports116FF
per instance. The fold depth increases from8 to10, while the HLS frame bound
rises only two cycles to263092, confirming II1 but not measured RTL throughput.

Read-only inspection of
workspace/exp_runs/C38/hls/syn/verilog/srcnn_reload_add_25ns_25ns_25_2_1.v
(SHA256 c3343eccf63030e5cd026e4f972bbfa6045d160808b73b647acae7df9bafae7b)
shows a split12/13-bit add: clocked sum_s1/carry_s1 and high ain_s1/bin_s1,
then a combinational upper add. NUM_STAGE=2 describes these two adder pieces;
it alone does not mean two full-cycle registers. Its39 explicit data-register
bits are different from the116FF HLS model. As earlier mapped/HLS calibration
also differs substantially, a physical result cannot be predicted precisely
from either number. The complete generated HDL stays outside Git in the raw
workspace; the archived HLS instance/module tables are the resource evidence.

Proceed with the smaller C37 parameter-register probe and required W35 before
WS-I. A compact-tree or diagnostic physical followup needs a fresh paper plan;
this result does not qualify for a4ns probe or a candidate handoff.
