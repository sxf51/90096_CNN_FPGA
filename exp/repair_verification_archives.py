#!/usr/bin/env python3
"""Preserve existing parsed routed reports outside generated-HDL ignore paths."""
import csv
import hashlib
import json
import subprocess
from pathlib import Path
from run_exp import ROOT, append_log, check_protected, markdown_table, write_json
from verify_exp import archive_verification_reports


def main():
    check_protected()
    repaired = []
    for row in csv.DictReader((ROOT / "experiments/results.csv").open(newline="")):
        archive = ROOT / "experiments" / Path(row["md_path"]).parent
        path = archive / "config.json"
        config = json.loads(path.read_text())
        if config.get("operation") not in {"impl", "cosim"}:
            continue
        records = archive_verification_reports(archive / "reports",archive,config["operation"])
        if not records:
            continue
        for record in records:
            target = archive / record["archived_file"]
            if hashlib.sha256(target.read_bytes()).hexdigest() != record["sha256"]:
                raise RuntimeError("Verification archive copy changed: "+str(target))
            ignored = subprocess.run(["git","check-ignore","-q","--",str(target)],cwd=ROOT)
            if ignored.returncode != 1:
                raise RuntimeError("Verification evidence is ignored: "+str(target))
        config["verification_reports"] = records
        write_json(path,config)
        md = ROOT / "experiments" / row["md_path"]
        text = md.read_text()
        marker = "\n<!-- AUTO: tracked verification reports -->"
        if marker in text:
            text = text[:text.index(marker)]+text[text.index("<!-- END: tracked verification reports -->")+len("<!-- END: tracked verification reports -->"):]
        position = text.index("## 6. Interpretation / 解读")
        section = marker+"\n\nArchived copies of the original parsed verification reports; numerical results and sources are unchanged. The original generated-HDL paths remain ignored.\n\n"
        section += markdown_table(records,["raw_file","archived_file","sha256"])+"\n<!-- END: tracked verification reports -->\n\n"
        md.write_text(text[:position]+section+text[position:])
        repaired.append(row["id"])
    append_log("F25: archived existing routed/RTL source reports at Git-visible neutral report paths for "+
               ", ".join(repaired)+"; original ignore rules, sources and measurements unchanged.")
    check_protected()
    print("VERIFICATION_REPORT_ARCHIVES",", ".join(repaired))


if __name__ == "__main__":
    main()
