#!/usr/bin/env python3
"""Reader-supplied facts reach the record, typed, validated, with provenance.

facts.py is the one path a reader's typed field takes onto a record. This
holds: a fact parses and validates (and a bad one is refused, not applied);
apply() sets the field, its provenance and a matching sources[] entry that
provenance.py accepts; applying twice changes nothing; and the numbered CLI
(importers/apply_facts.py) runs the whole loop on scratch files.

    python3 tests/test_facts.py
"""
import copy
import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import facts  # noqa: E402
import provenance  # noqa: E402

REC = {"id": "cm-test-noodles", "province": "cm", "cat": ["food"], "sub": ["noodle"],
       "name": "ก๋วยเตี๋ยวทดสอบ", "nameEn": "", "address": "", "phone": "", "website": "",
       "hours": "", "attrs": {}, "featured": False, "landmark": False,
       "sources": [{"type": "osm", "ref": "https://www.openstreetmap.org/node/1", "fetched": "2026-08-01"}],
       "confidence": "crawled", "updatedAt": "2026-08-01", "lat": 18.79, "lng": 98.99,
       "geoPrecision": "exact", "provenance": {}}


def row(field, value, pid="cm-test-noodles", sid="s1"):
    return {"id": sid, "kind": "contact", "placeId": pid, "createdAt": "2026-09-06T01:00:00Z",
            "what": "fact:" + json.dumps({"field": field, "value": value, "note": "seen on the sign"})}


def main():
    fails = []

    # 1. parse + validate
    f = facts.parse(row("phone", "081-234 5678"))
    if not f or f.get("value") != "0812345678":
        fails.append(f"phone did not parse/normalise: {f}")
    bad = facts.parse(row("phone", "call me"))
    if not bad or "error" not in bad:
        fails.append(f"a bad phone was accepted: {bad}")
    if "error" not in (facts.parse(row("pin", "50.1, 8.6")) or {}):
        fails.append("a pin outside the two provinces was accepted")
    if (facts.parse(row("pin", "18.7890, 98.9921")) or {}).get("value") != [18.789, 98.9921]:
        fails.append("a good pin did not parse")
    if facts.parse({"what": "just words", "placeId": "cm-x"}) is not None:
        fails.append("free text was taken for a fact")
    if (facts.parse(row("tags", "ตอกเส้น, ประคบ")) or {}).get("value") != ["ตอกเส้น", "ประคบ"]:
        fails.append("tags did not split")

    # 2. apply, provenance, idempotency
    doc = {"facts": {"cm-test-noodles": {
        "phone": {"value": "0812345678", "at": "2026-09-06", "suggestion": "s1"},
        "hours": {"value": "Mo-Sa 09:00-18:00", "at": "2026-09-06", "suggestion": "s2"},
        "line": {"value": "noodles.cm", "at": "2026-09-06", "suggestion": "s3"},
        "tags": {"value": ["ก๋วยเตี๋ยวเรือ"], "at": "2026-09-06", "suggestion": "s4"}}}}
    recs = [copy.deepcopy(REC)]
    n = facts.apply(recs, doc)
    r = recs[0]
    if n != 4:
        fails.append(f"apply set {n} fields, want 4")
    if r["phone"] != "0812345678" or r["hours"] != "Mo-Sa 09:00-18:00":
        fails.append("fields not set on the record")
    if r["attrs"].get("lineId") != "noodles.cm" or r["attrs"].get("tradeTags") != ["ก๋วยเตี๋ยวเรือ"]:
        fails.append("attrs fields not set")
    if r["provenance"].get("phone", {}).get("source") != facts.SOURCE_KEY:
        fails.append("no reader provenance on phone")
    complaints = provenance.validate(r) if hasattr(provenance, "validate") else []
    if complaints:
        fails.append(f"provenance.py rejects the applied record: {complaints[:3]}")
    again = facts.apply(recs, doc)
    if again != 0:
        fails.append(f"second apply changed {again} field(s); want 0")

    # 3. the CLI on scratch files
    with tempfile.TemporaryDirectory() as td:
        q = os.path.join(td, "queue.json")
        fj = os.path.join(td, "facts.json")
        rj = os.path.join(td, "rejected.json")
        real = None
        for pv in ("cm",):
            p = os.path.join(ROOT, "data", "canonical", f"{pv}.json")
            if os.path.exists(p):
                real = json.load(open(p, encoding="utf-8"))[0]["id"]
        json.dump({"suggestions": [row("hours", "Mo-Su 10:00-22:00", pid=real or "cm-test-noodles", sid="q1"),
                                   row("phone", "nope", pid=real or "cm-test-noodles", sid="q2")]},
                  open(q, "w"))
        env = dict(os.environ, MD_FACTS_QUEUE=q, MD_FACTS_FILE=fj, MD_FACTS_REJECTED=rj)
        out = subprocess.run([sys.executable, os.path.join(ROOT, "importers", "apply_facts.py")],
                             env=env, capture_output=True, text=True).stdout
        if "1 typed fact(s) waiting · 1 that did not validate" not in out:
            fails.append(f"CLI listing wrong:\n{out[-400:]}")
        out = subprocess.run([sys.executable, os.path.join(ROOT, "importers", "apply_facts.py"),
                              "--approve", "1"], env=env, capture_output=True, text=True).stdout
        written = json.load(open(fj)) if os.path.exists(fj) else {}
        if not written.get("facts"):
            fails.append(f"approve wrote nothing:\n{out[-400:]}")
        if "0 typed fact(s) waiting" not in out:
            fails.append("approved item still listed as waiting")

    if fails:
        print("\n".join(fails))
        print(f"FAIL: {len(fails)}")
        return 1
    print("OK: typed facts parse, validate, apply once, and carry provenance")
    return 0


if __name__ == "__main__":
    sys.exit(main())
