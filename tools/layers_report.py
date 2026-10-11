#!/usr/bin/env python3
"""The layers of the last build: time, files written, files read, failures.

    python3 tools/layers_report.py [ledger]     default MD_LAYER_STATE or cache/layers.json
                                                 on the server: /srv/state/layers.json
"""

import json
import os
import sys
from pathlib import Path

path = Path(sys.argv[1] if len(sys.argv) > 1 else
            os.environ.get("MD_LAYER_STATE") or Path(__file__).resolve().parent.parent / "cache" / "layers.json")
d = json.loads(path.read_text())
print("build %s — %d layers, failed: %s" % (d["at"], len(d["order"]), ", ".join(d["failed"]) or "none"))
print("%-26s %8s %7s %6s  %s" % ("layer", "seconds", "writes", "reads", "last worked"))
for name in sorted(d["order"], key=lambda n: -d["layers"][n]["seconds"]):
    r = d["layers"][name]
    print("%-26s %8.1f %7d %6d  %s%s" % (name, r["seconds"], len(r["outputs"]), len(r["reads"]),
                                          r.get("last_ok") or "-", "" if r["ok"] else "  FAILED " + r["error"][:60]))
