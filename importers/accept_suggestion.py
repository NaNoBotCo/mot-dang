#!/usr/bin/env python3
"""Accept or reject a reader's suggestion by number, and write the receipt.

    python3 importers/accept_suggestion.py              # numbered list, then a prompt
    python3 importers/accept_suggestion.py accept 2     # take row 2
    python3 importers/accept_suggestion.py --reject 3   # note it; never list it again
    python3 importers/accept_suggestion.py accept 2 --th "…" --en "…"
                                                        # the ledger line, given up front

The queue is _incoming/suggestions.json (importers/sync_suggestions.py). Until
now nothing tied a row in it to a row on /fixed.html: the page renders
data/fixes.json, and fixes.json was typed by hand. Accepting a suggestion
appends the fixes row itself — the reader's date as `reported`, today as
`fixed`, in exactly the shape build_fixed_page() reads — and notes the
decision in _incoming/suggestions-accepted.json so the row is not shown again.

The curated file is NOT touched. The tool prints the edit that still has to
be made by hand — which file under data/curated/, which id, which field, the
value — and stops there. A typed fact (facts.py) already has its own path,
importers/apply_facts.py; this prints the same facts.json line so the two
agree. A rejection writes the ledger only.

The ledger line is public copy, so it is shown as Thai and English defaults
built from the row and confirmed at a prompt (Enter keeps a default); the
reader's own words are shown for context and never copied onto the page.

data/fixes.json is a tracked file the build reads. Nothing else writes it;
this writes it only on an accept, whole file or not at all (temp + rename in
the same directory). The three paths are overridable so tests/test_accept_
suggestion.py can run the loop on scratch files and never on the real ones.
"""
import argparse
import json
import os
import re
import sys
import tempfile
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import facts  # noqa: E402

QUEUE = os.environ.get("MD_SUGGEST_QUEUE") or os.path.join(ROOT, "_incoming", "suggestions.json")
LEDGER = os.environ.get("MD_SUGGEST_LEDGER") or os.path.join(ROOT, "_incoming",
                                                              "suggestions-accepted.json")
FIXES = os.environ.get("MD_FIXES_FILE") or os.path.join(ROOT, "data", "fixes.json")
CREDITS = os.environ.get("MD_CREDITS_FILE") or os.path.join(ROOT, "data", "credits.json")
# The kinds on the form and the label each earns on /credits.html. A kind not listed has no label
# (question, crawl); the tool says so and leaves the row to be added by hand.
CREDIT_KIND = {"correction": "fix", "contact": "fix", "closed": "fix", "moved": "fix",
               "duplicate": "fix", "other": "fix", "missing": "add", "photo": "photo"}
CANONICAL = os.environ.get("MD_CANONICAL_DIR") or os.path.join(ROOT, "data", "canonical")

# The channel column on /fixed.html, in the file's own "Thai / English" habit.
VIA = "ผู้อ่านแจ้งทางเว็บ / reader, via the site"
LEDGER_NOTE = ("Decisions on _incoming/suggestions.json, by importers/accept_suggestion.py. "
               "`row` is the 0-based position of the appended entry in data/fixes.json "
               "fixes[]; null on a rejection. A row here is never listed again.")

# What the ledger line says by default. {name} is the place, {field} and
# {value} the typed fact; the operator confirms or types over it.
FIELD_TH = {"phone": "เบอร์โทร", "line": "ไลน์", "hours": "เวลาเปิด", "website": "เว็บไซต์",
            "pin": "พิกัด", "tags": "ป้ายค้นหา"}
FIELD_EN = {"phone": "phone", "line": "LINE", "hours": "hours", "website": "website",
            "pin": "pin", "tags": "tags"}
FACT_WHAT = ("{field} {name} ตามที่ผู้อ่านแจ้ง: {value}",
             "{field} for {name}, as a reader reported: {value}")
KIND_WHAT = {
    "correction": ("แก้ข้อมูล {name} ตามที่ผู้อ่านแจ้ง", "{name}: corrected as a reader reported"),
    "contact": ("ช่องทางติดต่อ {name} ตามที่ผู้อ่านแจ้ง", "{name}: contact added, as a reader reported"),
    "missing": ("เพิ่มรายการใหม่ตามที่ผู้อ่านแจ้ง", "a place added, as a reader reported"),
    "photo": ("รูป {name} จากผู้อ่าน", "{name}: a reader's photo"),
    "crawl": ("ส่งมดไปเดินมุมที่ผู้อ่านชี้", "crawled a corner a reader pointed to"),
    "closed": ("{name} ปิดถาวร — ผู้อ่านแจ้ง", "{name} closed for good, as a reader reported"),
    "moved": ("{name} ย้ายที่แล้ว — ผู้อ่านแจ้ง", "{name} moved, as a reader reported"),
    "duplicate": ("รวมรายการซ้ำของ {name} — ผู้อ่านแจ้ง",
                  "{name}: two records folded into one, as a reader reported"),
    "question": ("คำถามผู้อ่านขึ้นหน้าถามมดแล้ว", "a reader's question, answered on asked.html"),
    "other": ("แก้ตามที่ผู้อ่านแจ้ง — {name}", "as a reader reported — {name}"),
}


def load(p, default):
    try:
        with open(p, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return default


def atomic_write(path, doc):
    """Whole file or not at all: a temp file beside the target, then rename.
    The same directory matters — a rename across filesystems is a copy."""
    d = os.path.dirname(os.path.abspath(path))
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=d, prefix="." + os.path.basename(path) + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(doc, fh, ensure_ascii=False, indent=1)
            fh.write("\n")
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def names_for(ids):
    """Place names for the ids on the menu, from data/canonical/ — only read
    when a row names a place, since the files are large."""
    ids = {i for i in ids if i}
    out = {}
    if not ids:
        return out
    for pv in ("cm", "cr"):
        for r in load(os.path.join(CANONICAL, pv + ".json"), []):
            if r.get("id") in ids:
                out[r["id"]] = r.get("nameEn") or r.get("name") or r["id"]
    return out


# What a page on this site can be called. The reader's browser supplies the
# address, so it is their text until it has been checked: fixed.html prints
# it as a live href, and "javascript:..." typed into that field would be a
# live javascript: link on a published page. Only an ordinary relative path
# to one of our own pages survives — our host or none, no scheme, no host of
# their choosing, no traversal, and it ends the way our pages end.
SITE_PATH = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]{0,119}$")


def site_path(url):
    """The page the reader stood on, as fixes.json writes it: a path from the
    site root, or nothing. The form itself is not the page that changed."""
    p = (url or "").strip()
    m = re.match(r"^https?://([^/]+)(/.*)?$", p, re.I)
    if m:
        if m.group(1).lower().split(":")[0] not in ("motdang.net", "www.motdang.net"):
            return ""
        p = m.group(2) or ""
    elif "//" in p or ":" in p:
        return ""                       # a scheme, or a host with no scheme
    p = p.split("#")[0].split("?")[0].strip("/")
    if not p or p == "suggest.html" or ".." in p or not SITE_PATH.match(p):
        return ""
    return p if p.endswith(".html") or p.endswith("/") else p + "/"


def describe(row, names):
    """One queue row as the menu sees it: field and value from a typed fact
    when there is one, the reader's words as the note either way."""
    what = (row.get("what") or "").strip()
    d = {"id": row.get("id") or "", "date": (row.get("createdAt") or "")[:10],
         "kind": row.get("kind") or "other", "placeId": row.get("placeId") or "",
         "field": "", "value": "", "note": what, "page": site_path(row.get("page")),
         "valid": True}
    d["place"] = names.get(d["placeId"]) or d["placeId"]
    cr = row.get("credit") if isinstance(row.get("credit"), dict) else None
    d["credit"] = cr if cr and cr.get("name") and cr.get("v") else None
    d["ref"] = (d["id"] or "")[:8]
    if what.startswith(facts.PREFIX):
        try:
            body = json.loads(what[len(facts.PREFIX):])
        except ValueError:
            body = {}
        d["field"] = str(body.get("field") or "")
        d["value"] = str(body.get("value") or "")
        d["note"] = str(body.get("note") or "")
        f = facts.parse(row)
        if f and "error" not in f:
            v = f["value"]
            d["value"] = ", ".join(str(x) for x in v) if isinstance(v, list) else str(v)
        else:
            d["valid"] = False
    if row.get("detail"):
        d["note"] = (d["note"] + " — " + str(row["detail"])).strip(" —")
    d["note"] = " ".join(d["note"].split())
    return d


def pending():
    """Queue rows not yet decided, in arrival order, with their names."""
    seen = {e.get("id") for e in load(LEDGER, {}).get("decisions", [])}
    rows = [r for r in load(QUEUE, {}).get("suggestions", [])
            if r.get("status") != "done" and r.get("id") not in seen]
    names = names_for(r.get("placeId") for r in rows)
    return [describe(r, names) for r in rows]


def defaults(d):
    """The ledger line in both registers, from the row."""
    name = d["place"] or "รายการ"
    if d["field"] and d["valid"]:
        th, en = FACT_WHAT
        th = th.format(field=FIELD_TH.get(d["field"], d["field"]), name=name, value=d["value"])
        en = en.format(field=FIELD_EN.get(d["field"], d["field"]),
                       name=d["place"] or "a listing", value=d["value"])
        return th, en
    th, en = KIND_WHAT.get(d["kind"]) or KIND_WHAT["other"]
    return th.format(name=name), en.format(name=d["place"] or "a listing")


def hand_edit(d, today):
    """The curated edit this tool leaves to a person: file, id, field, value."""
    pid = d["placeId"] or "(no place id — find or create the record)"
    note = d["note"] or "(no note)"
    if d["field"] and d["valid"]:
        return [("file", "data/curated/facts.json"), ("id", pid), ("field", d["field"]),
                ("value", d["value"]),
                ("shape", 'facts["%s"]["%s"] = {"value": …, "at": "%s", "suggestion": "%s"}'
                          % (pid, d["field"], today, d["id"])),
                ("or", "importers/apply_facts.py --approve writes this line by number")]
    if d["field"]:
        return [("file", "data/curated/facts.json"), ("id", pid), ("field", d["field"]),
                ("value", d["value"] + "  (did not validate — check it against the place first)")]
    k = d["kind"]
    if k in ("closed", "moved"):
        return [("file", "data/curated/status.json"), ("id", pid), ("field", "status[id]"),
                ("value", '{"state": "%s", "since": "…", "to": "…", "source": "reader:suggest %s"}'
                          % (k, d["id"][:8])), ("note", note)]
    if k == "duplicate":
        return [("file", "data/curated/merges.json"), ("id", pid + "  (the keeper)"),
                ("field", "{keep_id: [drop_ids]}"), ("value", note)]
    if k == "missing":
        cr = d["page"].startswith("cr/")
        return [("file", "data/curated/additions-%s.json" % ("chiang-rai" if cr else "chiang-mai")),
                ("id", "(new) %s-curated-<slug>" % ("cr" if cr else "cm")),
                ("or", "elsewhere in the north: data/curated/additions-north.json, "
                       "id <key>-curated-<slug>, province <key> from data/coverage.json"),
                ("field", "a whole record"), ("value", note)]
    if k == "photo":
        return [("file", "data/curated/image_picks.json"), ("id", pid),
                ("field", "a pick, with its licence"), ("value", note)]
    if k == "question":
        return [("file", "data/asked.json, through asked_new.py --from-suggestion %s" % d["id"][:8]),
                ("id", "<key>"), ("field", "q-th / q-en"), ("value", note)]
    if k == "crawl":
        return [("file", "(none — a crawl, not a curated edit)"), ("id", pid),
                ("field", "—"), ("value", note)]
    return [("file", "data/curated/enrich.json"), ("id", pid),
            ("field", "(from the note: phone, hours, website, address, attrs.*)"), ("value", note)]


def show(items):
    if not items:
        print("🐜 nothing waiting")
        return
    print("🐜 %d suggestion(s) waiting" % len(items))
    for i, d in enumerate(items, 1):
        fv = ("%s=%s" % (d["field"], d["value"])) if d["field"] else ""
        if fv and not d["valid"]:
            fv += " (did not validate)"
        line = "  %2d. %-8s %-10s %-10s %s" % (i, d["id"][:8], d["date"], d["kind"],
                                                d["place"] or "(no place)")
        if fv:
            line += "  " + fv
        if d["note"]:
            line += "  — " + d["note"][:80]
        if d["credit"]:
            line += "  [credit: %s]" % d["credit"]["name"]
        print(line)


def ask(prompt, default):
    try:
        ans = input("%s [%s]: " % (prompt, default)).strip()
    except EOFError:
        ans = ""
    return ans or default


def decide(d, decision, row_index, today):
    doc = load(LEDGER, {})
    if not isinstance(doc, dict):
        doc = {}
    doc.setdefault("note", LEDGER_NOTE)
    doc.setdefault("decisions", []).append(
        {"id": d["id"], "date": today, "decision": decision, "row": row_index})
    atomic_write(LEDGER, doc)


def accept(d, th=None, en=None, today=None):
    """Append the fixes row, note the decision, return the row's index."""
    today = today or date.today().isoformat()
    dth, den = defaults(d)
    th = th or ask("   what changed (th)", dth)
    en = en or ask("   what changed (en)", den)
    doc = load(FIXES, None)
    if not isinstance(doc, dict) or not isinstance(doc.get("fixes"), list):
        raise SystemExit("%s is not the fixes ledger — nothing written" % FIXES)
    doc["fixes"].append({"reported": d["date"] or today, "fixed": today, "via": VIA,
                         "what_th": th, "what_en": en, "page": d["page"]})
    atomic_write(FIXES, doc)
    idx = len(doc["fixes"]) - 1
    decide(d, "accepted", idx, today)
    add_credit(d, idx, today)
    print("   ✓ %s — row %d on %s" % (d["id"][:8], idx, os.path.relpath(FIXES, ROOT)))
    print("   by hand, still:")
    for k, v in hand_edit(d, today):
        print("      %-6s %s" % (k, v))
    return idx


def add_credit(d, fix_row, today):
    """A reader who ticked the box and typed a name gets a row in data/credits.json. The row holds the
    name, the kind of help, the month, the wording version ticked, the first 8 characters of the queue
    id and the page. Contact address, note and voter id stay in the queue."""
    cr = d.get("credit")
    if not cr:
        return
    kind = CREDIT_KIND.get(d["kind"])
    if not kind:
        print("   credit ticked, and kind %r has no label on /credits.html — add the row by hand "
              "(notes/engineers-2026-10-11/credits/build_credits.py add)" % d["kind"])
        return
    doc = load(CREDITS, {"credits": []})
    if not isinstance(doc, dict) or not isinstance(doc.get("credits"), list):
        raise SystemExit("%s is not the credits file — credit not written" % CREDITS)
    row = {"name": cr["name"], "kind": kind, "month": today[:7], "consent": cr["v"], "ref": d["ref"],
           "fix": fix_row}
    if d["page"]:
        row["page"] = d["page"]
    doc["credits"].append(row)
    atomic_write(CREDITS, doc)
    print("   credit row %d on %s" % (len(doc["credits"]) - 1, os.path.relpath(CREDITS, ROOT)))


def reject(d, today=None):
    today = today or date.today().isoformat()
    decide(d, "rejected", None, today)
    print("   ✗ %s — rejected, not listed again" % d["id"][:8])


def pick(items, n):
    if not 1 <= n <= len(items):
        print("   %d: no such item (1–%d)" % (n, len(items)))
        return None
    return items[n - 1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", nargs="*", metavar="accept N", help='"accept N", or just N')
    ap.add_argument("--reject", type=int, metavar="N", help="note it; never list it again")
    ap.add_argument("--th", help="the ledger line in Thai (else a prompt with a default)")
    ap.add_argument("--en", help="the ledger line in English (else a prompt with a default)")
    args = ap.parse_args()

    items = pending()
    n = None
    if args.cmd:
        words = [w for w in args.cmd if w != "accept"]
        if len(words) != 1 or not words[0].isdigit():
            ap.error('say "accept N"')
        n = int(words[0])

    if args.reject is not None:
        d = pick(items, args.reject)
        if d:
            reject(d)
        return 0
    if n is not None:
        d = pick(items, n)
        if not d:
            show(items)
            return 1
        accept(d, args.th, args.en)
        return 0

    while True:
        show(items)
        if not items:
            return 0
        try:
            ans = input("number to accept, q to quit: ").strip()
        except EOFError:
            ans = "q"
        if ans in ("q", ""):
            return 0
        if not ans.isdigit():
            print("   a number, or q")
            continue
        d = pick(items, int(ans))
        if d:
            accept(d)
        items = pending()


if __name__ == "__main__":
    sys.exit(main())
