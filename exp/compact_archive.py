#!/usr/bin/env python3
"""Keep performance evidence while excluding bulky compiler instruction inventories."""
import csv
from pathlib import Path
import xml.etree.ElementTree as ET


def compact(archive):
    detail = []
    for path in sorted((archive / "reports").glob("*")):
        if not path.is_file():
            continue
        size = path.stat().st_size
        if path.name.startswith("csynth_design_size"):
            path.unlink()
            detail.append({"file": "reports/" + path.name, "original_bytes": size,
                           "archived_bytes": 0, "reason": "Compiler instruction inventory; full remote raw file retained"})
        elif path.suffix == ".rpt" and size > 100_000:
            lines = path.read_text(errors="replace").splitlines()
            text = "\n".join(lines[:180]) + "\n\nARCHIVE EXCERPT: complete raw report remains in the corresponding workspace/exp_runs directory.\n"
            path.write_text(text)
            detail.append({"file": "reports/" + path.name, "original_bytes": size,
                           "archived_bytes": path.stat().st_size,
                           "reason": "Timing, latency, loop and resource summary excerpt; parsed detail remains in data.csv"})
        elif path.suffix == ".xml" and size > 100_000:
            root = ET.parse(path).getroot()
            if root.tag == "profile":
                for node in list(root):
                    if node.tag not in {"ReportVersion", "UserAssignments", "PerformanceEstimates", "AreaEstimates"}:
                        root.remove(node)
                ET.SubElement(root, "ArchiveExcerpt").text = "Internal RTL-port inventories omitted; complete remote raw report retained"
                ET.indent(root)
                ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)
                detail.append({"file": "reports/" + path.name, "original_bytes": size,
                               "archived_bytes": path.stat().st_size,
                               "reason": "Structured XML retains all performance/loop/resource nodes; omits bulky internal-port inventories"})
    if detail:
        inventory = archive / "archive_inventory.csv"
        records = {row["file"]: row for row in csv.DictReader(inventory.open(newline=""))} if inventory.exists() else {}
        records.update({row["file"]: row for row in detail})
        with inventory.open("w", newline="") as out:
            writer = csv.DictWriter(out, fieldnames=list(detail[0]))
            writer.writeheader()
            writer.writerows(records.values())
    return detail


if __name__ == "__main__":
    import sys
    for item in sys.argv[1:]:
        print(item, compact(Path(item)))
