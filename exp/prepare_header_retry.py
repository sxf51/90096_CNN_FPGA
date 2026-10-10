#!/usr/bin/env python3
"""Retain header-order failures and prepare independent corrected variants."""
import json
import shutil
import subprocess
import sys
from plan_arch import plan
from run_exp import ROOT, append_log, check_protected, lock


def main():
    cases = (("W04","W07"),("W05","W08"),("W06","W09"),
             ("C01","C04"),("C02","C05"),("C03","C06"))
    for parent,exp_id in cases:
        config = json.loads((ROOT / "exp/configs" / (parent+".json")).read_text())
        config.update(id=exp_id,name=config["name"]+"_header_retry",design=config["design"]+"_r1",
                      purpose=config["purpose"]+" Header-order correction: load AMD fixed headers before network F2/F3 macros; preserve all arithmetic and paper estimates.",
                      changes="Independent correction of "+parent+" source: types.h is included before dimension macros in srcnn.h. Original failed designs/runs stay immutable.")
        plan(config)
        subprocess.run([sys.executable,str(ROOT / "exp/commit_exp.py"),exp_id,"plan_header_retry_"+parent],cwd=ROOT,check=True)
    for name in ("winograd_network","combination_network"):
        target = ROOT / "designs" / (name+"_r1")
        if target.exists():
            raise RuntimeError("Corrected design already exists")
        shutil.copytree(ROOT / "designs" / name,target)
        header = target / "srcnn.h"
        text = header.read_text().replace('\n#include "types.h"\n','\n')
        header.write_text('#include "types.h"\n'+text)
    with lock(ROOT / "workspace/exp_runs/.results.lock",wait_timeout=120):
        append_log("C01-C03: compile failure from F2/F3 dimension macro collision with AMD ap_fixed identifiers. W04-W06 share the same header; retain their attempted runs. W07-W09/C04-C06 use independent source copies with SDK headers included first; no protected test/source changed.")
    check_protected()
    subprocess.run([sys.executable,str(ROOT / "exp/commit_exp.py"),"C06","implement_header_order_correction"],cwd=ROOT,check=True)


if __name__ == "__main__":
    main()
