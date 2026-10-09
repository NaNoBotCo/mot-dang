#!/usr/bin/env python3
"""A suggestion accepted by number becomes a fixes.json row in the shape
/fixed.html reads, and is never listed again.

    python3 tests/test_accept_suggestion.py

Everything runs on scratch copies: a fake queue, a temp fixes.json with one
existing row, a temp ledger, an empty canonical directory. The real
data/fixes.json is read once for its shape and compared byte-for-byte at the
end — this tool is the only thing allowed to write it, and only on a real
accept. What is held:

  1. the appended row has exactly the keys build_fixed_page() reads, in the
     file's order, ISO dates, reported = the reader's date, fixed = today,
     the page as a site-root path;
  2. the file keeps its top-level ordering and the rows already in it;
  3. the ledger entry carries id, date, decision and the fixes row index,
     and the row drops out of the next listing;
  4. a rejection writes the ledger and nothing else;
  5. the CLI lists numbered lines and takes a number at the prompt;
  6. no temp file is left behind by an atomic write.
"""
import io
import json
import os
import subprocess
import sys
import tempfile
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(ROOT, "importers", "accept_suggestion.py")
REAL_FIXES = os.path.join(ROOT, "data", "fixes.json")

OLD_ROW = {"reported": "2026-08-19", "fixed": "2026-08-19", "via": "ตรวจเอง / self-audit",
           "what_th": "แถวเดิม", "what_en": "an earlier row", "page": "cm/tattoo/index.html"}
ROW_KEYS = ["reported", "fixed", "via", "what_th", "what_en", "page"]

QUEUE = {"fetched": 3, "suggestions": [
    {"id": "aaaa1111-0000-4000-8000-000000000001", "kind": "contact",
     "what": "fact:" + json.dumps({"field": "phone", "value": "081-234 5678", "note": "on the sign"}),
     "detail": None, "placeId": "cm-osm-node-1", "from": "someone@example.com",
     "page": "https://motdang.net/cm/food/noodle/cm-osm-node-1.html?x=1#top", "lang": "th",
     "status": "new", "createdAt": "2026-09-06T01:00:00.000Z"},
    {"id": "bbbb2222-0000-4000-8000-000000000002", "kind": "closed",
     "what": "shut since August, sign says moved to Hang Dong", "detail": "since 2026-08-01",
     "placeId": "cm-osm-node-2", "from": None, "page": "https://motdang.net/suggest.html",
     "lang": "en", "status": "new", "createdAt": "2026-09-07T02:00:00.000Z"},
    {"id": "cccc3333-0000-4000-8000-000000000003", "kind": "question",
     "what": "where do I find a luthier", "detail": None, "placeId": None, "from": None,
     "page": None, "lang": "en", "status": "new", "createdAt": "2026-09-08T03:00:00.000Z"},
]}


def run(env, args, stdin=""):
    p = subprocess.run([sys.executable, TOOL] + args, env=env, input=stdin,
                       capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def check_site_path():
    """The reader's browser supplies the address and fixed.html prints it as
    a live href. Anything but a relative path to one of our pages is dropped:
    a javascript: link on a published page would otherwise be one suggestion
    away."""
    keep = {
        "https://motdang.net/cm/p/foo-123.html": "cm/p/foo-123.html",
        "https://www.motdang.net/map.html": "map.html",
        "https://motdang.net/cm/food/": "cm/food/",
        "cm/p/foo.html": "cm/p/foo.html",
        "https://motdang.net/cm/p/a.html#where": "cm/p/a.html",
    }
    drop = ["javascript:alert(1)", "JavaScript:alert(1)", "data:text/html,x",
            "//evil.com/x", "https://evil.com/x",
            "https://motdang.net/../../etc/passwd",
            "https://motdang.net/suggest.html?id=1", "suggest.html", "",
            "https://motdang.net/" + "a" * 200]
    import importlib.util
    spec = importlib.util.spec_from_file_location("accept_suggestion", TOOL)
    accept_suggestion = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(accept_suggestion)

    bad = []
    for url, want in keep.items():
        got = accept_suggestion.site_path(url)
        if got != want:
            bad.append("site_path(%r) -> %r, wanted %r" % (url, got, want))
    for url in drop:
        got = accept_suggestion.site_path(url)
        if got != "":
            bad.append("site_path(%r) should be dropped, got %r" % (url, got))
    return bad


def main():
    fails = []
    today = date.today().isoformat()
    real_before = open(REAL_FIXES, "rb").read() if os.path.exists(REAL_FIXES) else None
    real_keys = list(json.load(open(REAL_FIXES, encoding="utf-8")).keys()) if real_before else ["note", "fixes"]

    with tempfile.TemporaryDirectory() as td:
        q = os.path.join(td, "suggestions.json")
        fx = os.path.join(td, "fixes.json")
        lg = os.path.join(td, "suggestions-accepted.json")
        canon = os.path.join(td, "canonical")
        os.makedirs(canon)
        json.dump([{"id": "cm-osm-node-1", "name": "ก๋วยเตี๋ยวทดสอบ", "nameEn": "Test Noodles"}],
                  open(os.path.join(canon, "cm.json"), "w", encoding="utf-8"), ensure_ascii=False)
        json.dump(QUEUE, open(q, "w", encoding="utf-8"), ensure_ascii=False)
        with open(fx, "w", encoding="utf-8") as fh:
            json.dump({"note": "scratch ledger", "fixes": [OLD_ROW]}, fh, ensure_ascii=False, indent=1)
            fh.write("\n")
        env = dict(os.environ, MD_SUGGEST_QUEUE=q, MD_FIXES_FILE=fx, MD_SUGGEST_LEDGER=lg,
                   MD_CANONICAL_DIR=canon)

        # 5a. the numbered listing, then q at the prompt
        rc, out = run(env, [], stdin="q\n")
        if rc != 0 or "3 suggestion(s) waiting" not in out:
            fails.append("listing: %s\n%s" % (rc, out[-400:]))
        for want in ("   1. aaaa1111", "   2. bbbb2222", "   3. cccc3333", "number to accept, q to quit",
                     "Test Noodles", "phone=0812345678", "on the sign", "cm-osm-node-2", "since 2026-08-01"):
            if want not in out:
                fails.append("listing lacks %r" % want)
        if "someone@example.com" in out:
            fails.append("the sender's address was printed")

        # 1–3. accept 1, the ledger line given up front
        rc, out = run(env, ["accept", "1", "--th", "เบอร์โทรใหม่", "--en", "new phone"])
        doc = json.load(open(fx, encoding="utf-8"))
        if rc != 0:
            fails.append("accept 1 failed: %s" % out[-400:])
        if list(doc.keys()) != ["note", "fixes"] or doc.get("note") != "scratch ledger":
            fails.append("top-level ordering or note changed: %s" % list(doc.keys()))
        rows = doc.get("fixes") or []
        if len(rows) != 2 or rows[0] != OLD_ROW:
            fails.append("existing row not kept, or row count wrong: %d" % len(rows))
        new = rows[-1] if rows else {}
        if list(new.keys()) != ROW_KEYS:
            fails.append("row keys %s, want %s" % (list(new.keys()), ROW_KEYS))
        if new.get("reported") != "2026-09-06" or new.get("fixed") != today:
            fails.append("dates wrong: %s / %s" % (new.get("reported"), new.get("fixed")))
        for k in ("reported", "fixed"):
            try:
                date.fromisoformat(new.get(k, ""))
            except ValueError:
                fails.append("%s is not an ISO date: %r" % (k, new.get(k)))
        if new.get("what_th") != "เบอร์โทรใหม่" or new.get("what_en") != "new phone":
            fails.append("ledger line not taken from --th/--en: %s" % new)
        if new.get("page") != "cm/food/noodle/cm-osm-node-1.html":
            fails.append("page not a site-root path: %r" % new.get("page"))
        if not new.get("via") or "/" not in new["via"]:
            fails.append("via missing its Thai / English pair: %r" % new.get("via"))
        led = json.load(open(lg, encoding="utf-8")) if os.path.exists(lg) else {}
        dec = (led.get("decisions") or [{}])[-1]
        want = {"id": "aaaa1111-0000-4000-8000-000000000001", "date": today, "decision": "accepted", "row": 1}
        if dec != want:
            fails.append("ledger entry %s, want %s" % (dec, want))
        for want in ("data/curated/facts.json", "cm-osm-node-1", "phone", "0812345678", "row 1"):
            if want not in out:
                fails.append("accept output lacks %r" % want)
        rc, out = run(env, [], stdin="q\n")
        if "aaaa1111" in out or "2 suggestion(s) waiting" not in out:
            fails.append("accepted row listed again:\n%s" % out[-300:])

        # 5b. the number at the prompt, Enter keeping both defaults
        rc, out = run(env, [], stdin="1\n\n\nq\n")
        doc = json.load(open(fx, encoding="utf-8"))
        rows = doc.get("fixes") or []
        if rc != 0 or len(rows) != 3:
            fails.append("accept at the prompt: rc %s, %d rows\n%s" % (rc, len(rows), out[-400:]))
        else:
            new = rows[-1]
            if new.get("reported") != "2026-09-07" or not new.get("what_th") or not new.get("what_en"):
                fails.append("prompt accept row wrong: %s" % new)
            if "cm-osm-node-2" not in new.get("what_th", "") + new.get("what_en", ""):
                fails.append("default ledger line does not name the place: %s" % new)
            if new.get("page") != "":
                fails.append("the form's own page should not be the fixed page: %r" % new.get("page"))
            if "shut since August" in json.dumps(new, ensure_ascii=False):
                fails.append("the reader's words were copied onto the public row")
        if "data/curated/status.json" not in out or '"state": "closed"' not in out:
            fails.append("closed: hand edit does not point at status.json:\n%s" % out[-400:])
        led = json.load(open(lg, encoding="utf-8"))
        if len(led.get("decisions", [])) != 2 or led["decisions"][-1].get("row") != 2:
            fails.append("second ledger entry wrong: %s" % led.get("decisions"))

        # 4. reject the last one: ledger only
        before = open(fx, "rb").read()
        rc, out = run(env, ["--reject", "1"])
        if rc != 0 or open(fx, "rb").read() != before:
            fails.append("reject touched fixes.json or failed: %s" % out[-300:])
        led = json.load(open(lg, encoding="utf-8"))
        dec = (led.get("decisions") or [{}])[-1]
        if dec.get("id") != "cccc3333-0000-4000-8000-000000000003" or dec.get("decision") != "rejected" \
                or dec.get("row") is not None:
            fails.append("rejection entry wrong: %s" % dec)
        rc, out = run(env, [], stdin="q\n")
        if "nothing waiting" not in out:
            fails.append("queue not empty after three decisions:\n%s" % out[-300:])

        # out of range, and a bad word
        rc, out = run(env, ["accept", "9"])
        if rc == 0 or "no such item" not in out:
            fails.append("accept 9 should refuse: %s" % out[-200:])

        # 6. nothing left behind by the atomic writes
        stray = [f for f in os.listdir(td) if f.endswith(".tmp")]
        if stray:
            fails.append("temp files left behind: %s" % stray)

    # the real ledger is untouched
    if real_before is not None and open(REAL_FIXES, "rb").read() != real_before:
        fails.append("the real data/fixes.json changed during the test")
    fails.extend(check_site_path())
    if real_keys != ["note", "fixes"]:
        fails.append("the real fixes.json no longer has the note/fixes shape this tool assumes: %s" % real_keys)

    if fails:
        print("\n".join(fails))
        print("FAIL: %d" % len(fails))
        return 1
    print("OK: an accepted suggestion becomes a fixes.json row, a ledger entry, and a hand-edit note;\n    site_path keeps only our own pages")
    return 0

if __name__ == "__main__":
    sys.exit(main())
