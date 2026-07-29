from __future__ import annotations

import glob
import json
import sys

runs = sorted(glob.glob("runs/*.json"))
if not runs:
    print("No run files found in runs/")
    sys.exit(1)

target = sys.argv[1] if len(sys.argv) > 1 else runs[-1]
if target in runs or "/" in target:
    path = target
else:
    matches = [r for r in runs if target in r]
    path = matches[-1] if matches else runs[-1]

d = json.load(open(path, encoding="utf-8"))
out = []
out.append(f"=== {path} ===")
out.append(f"Version: {d['version']} | Accuracy: {d['summary']['case_accuracy']}")
out.append(f"Measured: {d['summary']['measured_cases']}/{d['summary']['total_cases']}")
out.append(f"Provider errors: {d['summary']['provider_error_cases']}")
out.append(f"Routing accuracy: {d['summary'].get('tool_routing_accuracy')}")
out.append(f"Arg accuracy: {d['summary'].get('argument_accuracy')}")
out.append(f"Multi-turn accuracy: {d['summary'].get('multiturn_accuracy')}")
out.append("")

for r in d["results"]:
    res = r["result"]
    if not res["passed"]:
        out.append(f"FAIL {r['id']}")
        out.append(f"  mismatch: {res.get('observed_mismatch')}")
        out.append(f"  failures: {res.get('failures')}")
        calls_str = json.dumps(res.get("actual_tool_calls"), ensure_ascii=False)
        out.append(f"  calls: {calls_str}")
        out.append("")

sys.stdout.reconfigure(encoding="utf-8")
print("\n".join(out))
