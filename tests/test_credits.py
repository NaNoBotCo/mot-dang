#!/usr/bin/env python3
"""WO-110. The generator, and the credit hook in accept_suggestion.py.

    python3 tests/test_credits.py              # the generator and the hook, in this repo
    MD_ROOT=/path/to/tree python3 tests/test_credits.py

The hook half runs importers/accept_suggestion.py under MD_ROOT (default: the repo root) on scratch files,
through the tool's own environment overrides. It skips with a line when that tool does not carry the credit hook.
"""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.environ.get("MD_ROOT") or os.path.join(HERE, ".."))
sys.path.insert(0, ROOT)
import credits_layer as bc  # noqa: E402

TOOL = os.path.join(ROOT, "importers", "accept_suggestion.py")
bad = []


def check(name, ok, why=""):
    if not ok:
        bad.append(name + (" — " + why if why else ""))


GOOD = {"name": "Example Reader", "kind": "fix", "month": "2026-10", "consent": "2026-10-11"}


def row(**kw):
    r = dict(GOOD)
    r.update(kw)
    return r


# rows
check("a good row passes", bc.row_problems(GOOD) == [], str(bc.row_problems(GOOD)))
for label, r in [
    ("no consent", {k: v for k, v in GOOD.items() if k != "consent"}),
    ("an unknown wording version", row(consent="2020-01-01")),
    ("an email as the name", row(name="reader@example.org")),
    ("a phone as the name", row(name="081 234 5678")),
    ("angle brackets", row(name="<script>x</script>")),
    ("a bad kind", row(kind="praise")),
    ("a bad month", row(month="2026-13")),
    ("a bad ref", row(ref="xyz")),
    ("a page with traversal", row(page="cm/../etc/passwd")),
    ("a page with a scheme", row(page="https://example.org/x")),
    ("a fix row that is not a number", row(fix="1")),
]:
    check("rejects " + label, bc.row_problems(r) != [])
check("accepts Thai", bc.row_problems(row(name="ตัวอย่าง ผู้อ่าน")) == [])
check("accepts a ref and a page", bc.row_problems(row(ref="0a1b2c3d", page="cm/p/x.html", fix=3)) == [])

# the page
doc = {"credits": [row(name="Zed", month="2026-09"), row(name="Amy", month="2026-10"),
                   row(name="Bob", month="2026-10"), row(name="reader@example.org")]}
rows, left = bc.listed(doc)
check("a failing row is left off and named", [r["name"] for r in rows] == ["Amy", "Bob", "Zed"] and [i for i, _ in left] == [3],
      str([r["name"] for r in rows]))
page = bc.document(rows)
check("the left-off name is not on the page", "reader@example.org" not in page)
hostile = {"credits": [row(name="O'Neil & Sons", page="cm/p/a-b.html")]}
hp = bc.document(bc.listed(hostile)[0])
check("a name is escaped", "O&#x27;Neil &amp; Sons" in hp, hp[hp.find("cr-name"):][:120])
check("empty state", "No names yet" in bc.document([]) and "<table" not in bc.document([]))
check("sample page is noindex, live page is not", "noindex" in bc.document([], sample=True) and "noindex" not in bc.document([]))
check("the page carries no ref", "0a1b2c3d" not in bc.document(bc.listed({"credits": [row(ref="0a1b2c3d")]})[0]))
check("no contact address on the page", "@" not in bc.body(rows))
check("the live file lists nobody", bc.listed(bc.load(os.path.join(ROOT, "data", "credits.json")))[0] == [])

# add
with tempfile.TemporaryDirectory() as td:
    p = os.path.join(td, "c.json")
    json.dump({"credits": []}, open(p, "w"))
    check("add writes a row", bc.main(["add", "--in", p, "--name", "Example Reader", "--kind", "bug", "--month", "2026-10",
                                       "--ref", "0a1b2c3d"]) == 0 and len(json.load(open(p))["credits"]) == 1)
    check("add refuses an address as a name", bc.main(["add", "--in", p, "--name", "a@b.co", "--kind", "bug",
                                                      "--month", "2026-10"]) == 1 and len(json.load(open(p))["credits"]) == 1)
    check("check passes the file", bc.main(["check", "--in", p]) == 0)

# the hook
src = open(TOOL, encoding="utf-8").read() if os.path.exists(TOOL) else ""
if "CREDITS" not in src:
    print("hook half skipped: %s does not carry credit-form.patch" % TOOL)
else:
    queue = {"suggestions": [
        {"id": "dddd4444-0000-4000-8000-000000000004", "kind": "correction", "what": "phone is wrong", "detail": None,
         "placeId": None, "from": "reader@example.org", "page": "https://motdang.net/cm/p/foo-123.html",
         "lang": "en", "status": "new", "createdAt": "2026-10-11T01:00:00.000Z",
         "credit": {"name": "Example Reader", "v": "2026-10-11"}},
        {"id": "eeee5555-0000-4000-8000-000000000005", "kind": "correction", "what": "hours are wrong", "detail": None,
         "placeId": None, "from": None, "page": None, "lang": "en", "status": "new",
         "createdAt": "2026-10-11T02:00:00.000Z", "credit": None},
        {"id": "ffff6666-0000-4000-8000-000000000006", "kind": "question", "what": "where is a luthier", "detail": None,
         "placeId": None, "from": None, "page": None, "lang": "en", "status": "new",
         "createdAt": "2026-10-11T03:00:00.000Z", "credit": {"name": "Example Asker", "v": "2026-10-11"}},
    ]}
    with tempfile.TemporaryDirectory() as td:
        env = dict(os.environ, MD_SUGGEST_QUEUE=os.path.join(td, "q.json"), MD_SUGGEST_LEDGER=os.path.join(td, "l.json"),
                   MD_FIXES_FILE=os.path.join(td, "fixes.json"), MD_CREDITS_FILE=os.path.join(td, "credits.json"),
                   MD_CANONICAL_DIR=os.path.join(td, "canon"))
        os.makedirs(env["MD_CANONICAL_DIR"])
        json.dump(queue, open(env["MD_SUGGEST_QUEUE"], "w"))
        json.dump({"note": "x", "fixes": []}, open(env["MD_FIXES_FILE"], "w"))

        def run(*args):
            p = subprocess.run([sys.executable, TOOL] + list(args), env=env, input="", capture_output=True, text=True, timeout=60)
            return p.stdout + p.stderr

        out = run()
        check("the menu marks the credit", "[credit: Example Reader]" in out and out.count("[credit:") == 2, out)
        out = run("accept", "1", "--th", "แก้", "--en", "fixed")
        credits = json.load(open(env["MD_CREDITS_FILE"]))["credits"] if os.path.exists(env["MD_CREDITS_FILE"]) else []
        check("accepting row 1 writes one credit row", len(credits) == 1, out)
        if credits:
            c = credits[0]
            check("the credit row holds name, kind, month, consent, ref, fix, page",
                  c["name"] == "Example Reader" and c["kind"] == "fix" and len(c["month"]) == 7 and c["consent"] == "2026-10-11"
                  and c["ref"] == "dddd4444" and c["fix"] == 0 and c["page"] == "cm/p/foo-123.html", str(c))
            check("the credit row passes the generator's check", bc.row_problems(c) == [], str(bc.row_problems(c)))
            check("the contact address is not in the credits file",
                  "example.org" not in open(env["MD_CREDITS_FILE"]).read())
        out = run("accept", "1", "--th", "แก้", "--en", "fixed")      # the old row 2, no credit
        credits = json.load(open(env["MD_CREDITS_FILE"]))["credits"]
        check("accepting a row with no credit writes none", len(credits) == 1, out)
        out = run("accept", "1", "--th", "ถาม", "--en", "asked")      # the question, which has no label
        credits = json.load(open(env["MD_CREDITS_FILE"]))["credits"]
        check("a kind with no label writes none and says so", len(credits) == 1 and "no label" in out, out)

print("credits: %s" % ("ok" if not bad else "%d failing" % len(bad)))
for b in bad:
    print("FAIL  " + b)
sys.exit(1 if bad else 0)
