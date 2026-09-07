#!/usr/bin/env python3
"""heard.py — the nod ledger. One keypress per person you told about the site.

WHY THIS EXISTS. Nothing on the site counts readers, so there is no number
anywhere that answers "has anyone in this city heard of Mot Dang?" The
recognition plan (notes/heard-of-it-proposal-2026-08-20.md) is measured against
this file and nothing else. It counts CONVERSATIONS Nan had, not readers — it
is a diary, not a tracker, and it never leaves this machine.

    python3 heard.py            the menu: press 1, 2 or 3, Enter, done
    python3 heard.py 2          log one nod without the menu
    python3 heard.py --report   the rate, this month and every month
    python3 heard.py --undo     remove the last entry

The three states, and the line between them is the whole point:

    1  didn't know it        you had to explain from scratch
    2  knew the site         "the red-ant one?" — the site has a name
    3  knew it was yours     they connected the site to you

Stage 3 is the goal in the user's own words: "you've heard of motdang.net?
then you've seen my work." Stage 2 is the site becoming a landmark. Both are
worth counting separately, because they move at different speeds and the
plan's targets are quoted as "nods" = 2 and 3 together.

Entries append to data/heard.jsonl — one JSON object per line, never rewritten
except by --undo. NOT in docs/, so it is never published; NOT in data/curated/,
which is field truth about places. No name of the other person is stored:
what is useful is the count and the room, and a private log of who did not
recognise your work is not a thing worth keeping.
"""
import json
import sys
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LEDGER = ROOT / "data" / "heard.jsonl"

# (key, th, en, short) — the short form is what --report prints in a column.
STATES = [
    ("1", "ไม่เคยได้ยิน", "didn't know it", "cold"),
    ("2", "รู้จักเว็บ", "knew the site", "knew site"),
    ("3", "รู้ว่าเป็นงานของเรา", "knew it was yours", "knew it's yours"),
]
# Where the conversation happened. Optional — Enter skips it. Kept coarse on
# purpose: the plan is about rooms, and "which room earns nods" is the only
# question this field has to answer.
PLACES = [
    ("1", "งานเลี้ยง / party or event"),
    ("2", "ร้าน / ธุรกิจ — shop or business"),
    ("3", "เพื่อน / คนรู้จัก — friend or acquaintance"),
    ("4", "คนแปลกหน้า — stranger"),
    ("5", "ออนไลน์ — online, LINE, a group"),
]


def _load():
    if not LEDGER.exists():
        return []
    out = []
    for line in LEDGER.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            # A half-written line from a Ctrl-C mid-append. Skip it rather
            # than refuse to report: this is a diary, not an accounts ledger.
            continue
    return out


def _append(state, where=""):
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    row = {"at": datetime.now().isoformat(timespec="seconds"),
           "state": int(state)}
    if where:
        row["where"] = where
    with LEDGER.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    label = next(en for k, _th, en, _s in STATES if k == str(state))
    rows = _load()
    print(f"\n  logged: {label}" + (f" · {where}" if where else ""))
    _rate_line(rows, "  so far this month: ")


def _rate_line(rows, prefix=""):
    """The one number the plan is graded on: nods / attempts, this month."""
    today = date.today()
    month = [r for r in rows if r["at"][:7] == today.strftime("%Y-%m")]
    if not month:
        print(prefix + "no entries yet this month")
        return
    nods = sum(1 for r in month if r["state"] >= 2)
    pct = round(100 * nods / len(month))
    yours = sum(1 for r in month if r["state"] == 3)
    print(f"{prefix}{nods}/{len(month)} nodded ({pct}%) · "
          f"{yours} knew it was yours")


def menu():
    print("\n  🐜  Did they know it?\n")
    for k, th, en, _s in STATES:
        print(f"    {k}   {en:<20} {th}")
    print("\n    r   report        q   quit\n")
    try:
        pick = input("  press 1-3: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        return
    if pick in ("q", ""):
        return
    if pick == "r":
        report()
        return
    if pick not in [k for k, *_ in STATES]:
        print("  not one of the numbers — nothing logged")
        return
    print("\n  where? (Enter to skip)\n")
    for k, lbl in PLACES:
        print(f"    {k}   {lbl}")
    try:
        w = input("\n  press 1-5 or Enter: ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        w = ""
    where = next((lbl.split(" — ")[0].split(" / ")[0].strip()
                  for k, lbl in PLACES if k == w), "")
    _append(pick, where)


def report():
    rows = _load()
    if not rows:
        print("\n  nothing logged yet. Run `python3 heard.py` after the next "
              "time you tell someone.\n")
        return
    print(f"\n  🐜  the nod ledger — {len(rows)} conversations logged\n")
    months = {}
    for r in rows:
        months.setdefault(r["at"][:7], []).append(r)
    print(f"  {'month':<9}{'told':>6}{'nods':>6}{'rate':>7}{'yours':>7}")
    for m in sorted(months):
        mr = months[m]
        nods = sum(1 for r in mr if r["state"] >= 2)
        yours = sum(1 for r in mr if r["state"] == 3)
        print(f"  {m:<9}{len(mr):>6}{nods:>6}{round(100 * nods / len(mr)):>6}%"
              f"{yours:>7}")
    # Rooms, best first — which one is actually earning recognition.
    wheres = {}
    for r in rows:
        if r.get("where"):
            wheres.setdefault(r["where"], []).append(r)
    if wheres:
        print(f"\n  {'where':<28}{'told':>6}{'nods':>6}")
        for w, wr in sorted(wheres.items(),
                            key=lambda kv: -sum(1 for r in kv[1]
                                                if r["state"] >= 2)):
            print(f"  {w:<28}{len(wr):>6}"
                  f"{sum(1 for r in wr if r['state'] >= 2):>6}")
    # The plan's staged targets, so a glance says whether it is on track.
    print("\n  plan targets: 1 in 4 by end Oct · 1 in 3 by mid Dec · "
          "1 in 2 by Jan 30")
    _rate_line(rows, "  this month:   ")
    print(f"\n  ledger: {LEDGER}\n")


def undo():
    rows = _load()
    if not rows:
        print("  nothing to undo")
        return
    last = rows[-1]
    LEDGER.write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows[:-1]),
        encoding="utf-8")
    print(f"  removed: {last['at']} state {last['state']}")


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else ""
    if arg in ("--report", "-r", "report"):
        report()
    elif arg in ("--undo", "-u", "undo"):
        undo()
    elif arg in ("1", "2", "3"):
        _append(arg)
    elif arg in ("-h", "--help", "help"):
        print(__doc__)
    else:
        menu()
