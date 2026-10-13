"""Reject parameter-stage claims that have no clocked data or bypass the stage."""
import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from archive_param_registers import register_fields


def fixture():
    helper, inputs, writes, baseline = [], [], [], []
    clocked, returns, ports = [], [], []
    for index in range(16):
        register = f"value_{index}_read_reg_{100+index}"
        helper.append(f"reg [13:0] {register};")
        clocked.append(f"{register} <= value_{index};")
        returns.append(f"assign ap_return_{index} = {register};")
        incoming, outgoing = f"pe_value_{index}", f"pe_ap_return_{index}"
        ports.extend((f".value_{index}({incoming})", f".ap_return_{index}({outgoing})"))
        inputs.append(f"assign {incoming} = params1_dout[{14*index+13}:{14*index}];")
        writes.append(f"assign bank_{index}_d1 = {outgoing};")
        baseline.append(f"assign bank_{index}_d1 = {{{{params1_dout[{14*index+13}:{14*index}]}}}};")
    helper += ["always @ (posedge ap_clk) begin", *clocked, "end", *returns, "endmodule"]
    caller = "top_params1_write_register pe(\n"+",\n".join(ports)+"\n);\n"+"\n".join(inputs+writes)
    return "\n".join(helper), caller, "\n".join(baseline)


class ParameterRegisterEvidenceTests(unittest.TestCase):
    def test_all_fields_are_clocked_and_drive_the_banks(self):
        fields = register_fields(*fixture())
        self.assertEqual(sum(field["bits"] for field in fields), 224)

    def test_combinational_block_is_not_a_data_register(self):
        helper, caller, baseline = fixture()
        with self.assertRaises(RuntimeError):
            register_fields(helper.replace("posedge ap_clk", "*"), caller, baseline)

    def test_control_registers_do_not_prove_registered_returns(self):
        helper, caller, baseline = fixture()
        helper = helper.replace("assign ap_return_0 = value_0_read_reg_100;", "assign ap_return_0 = value_0;")
        with self.assertRaises(RuntimeError):
            register_fields(helper, caller, baseline)

    def test_wrong_clock_or_partial_packet_is_rejected(self):
        helper, caller, baseline = fixture()
        for changed in (helper.replace("posedge ap_clk", "posedge other_clk"),
                        helper.replace("value_15_read_reg_115 <= value_15;", "")):
            with self.assertRaises(RuntimeError):
                register_fields(changed, caller, baseline)

    def test_fifo_bypass_is_rejected(self):
        helper, caller, baseline = fixture()
        with self.assertRaises(RuntimeError):
            register_fields(helper, caller+"\nassign bypass_d1 = params1_dout[13:0];", baseline)

    def test_parent_combinational_low_field_alias(self):
        helper, caller, baseline = fixture()
        baseline = baseline.replace("{{params1_dout[13:0]}}", "trunc_low")
        baseline += "\nassign trunc_low = params1_dout[13:0];"
        self.assertEqual(len(register_fields(helper, caller, baseline)), 16)

    def test_caller_concatenates_an_unchanged_field(self):
        helper, caller, baseline = fixture()
        caller = caller.replace("= params1_dout[27:14];", "= {{params1_dout[27:14]}};")
        self.assertEqual(len(register_fields(helper, caller, baseline)), 16)

    def test_aliased_fifo_bypass_is_rejected(self):
        helper, caller, baseline = fixture()
        with self.assertRaises(RuntimeError):
            register_fields(helper, caller+"\nassign bypass_d1 = pe_value_0;", baseline)


if __name__ == "__main__":
    unittest.main()
