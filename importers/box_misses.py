#!/usr/bin/env python3
"""What readers typed that the site could not answer — the miss loop's first half.

Nan, 2026-09-10: "Do items 1–5 in order for search." Item 3: learn from misses.
The results page reports every search to /api/box (white-label-ai's box_log:
the query, how many rows, the tier, the words that matched NOTHING, and later
whether the reader opened anything). This pulls that table and writes the list
a person or a bot can act on:

  _incoming/box-misses-<date>.txt     the digest, plain text
  _incoming/box-misses-<date>.json    the same, as data

Four lists, each a vocabulary or a record waiting to be written:
  1. words nobody understood      (`unknown`, ranked)          -> thesaurus lines
  2. searches that found nothing  (n = 0, ranked by repeats)    -> records or shelves
  3. searches that only half-matched (quality = partial)       -> vocabulary or records
  4. searches shown results nobody touched (outcome = '')       -> ranking to look at

No reader is in this table: no ip, no seat, no session (see the migration).

  python3 importers/box_misses.py [--days 14]
"""
import collections, datetime, json, os, pathlib, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
WLA = ROOT.parent / "white-label-ai"
OUT = ROOT / "_incoming"
TODAY = datetime.date.today().isoformat()


def query(sql):
    """One SQL statement against the remote D1, through wrangler (logged in on
    this Mac, or the token file the other scripts use)."""
    env = dict(os.environ)
    keys = pathlib.Path.home() / ".config/nanobotco/keys.json"
    if keys.exists():
        try:
            env["CLOUDFLARE_API_TOKEN"] = json.load(open(keys))["cloudflare"]["api_token"]
        except Exception:
            pass
    out = subprocess.run(["npx", "wrangler", "d1", "execute", "white-label-ai", "--remote", "--json",
                          "--command", sql], cwd=WLA, env=env, capture_output=True, text=True, timeout=180)
    if out.returncode:
        sys.exit("wrangler d1 failed:\n" + (out.stderr or out.stdout)[-800:])
    txt = out.stdout[out.stdout.index("["):] if "[" in out.stdout else "[]"
    doc = json.loads(txt)
    return (doc[0] or {}).get("results", []) if doc else []


def main():
    days = 14
    if "--days" in sys.argv:
        days = int(sys.argv[sys.argv.index("--days") + 1])
    rows = query(f"SELECT ts, source, q, unknown, n, quality, top, outcome FROM box_log "
                 f"WHERE site = 'motdang' AND ts >= datetime('now', '-{days} days') ORDER BY ts DESC LIMIT 5000")
    unknown = collections.Counter()
    zero = collections.Counter()
    partial = collections.Counter()
    untouched = collections.Counter()
    asked = collections.Counter()
    for r in rows:
        q = (r.get("q") or "").strip().lower()
        if not q:
            continue
        asked[q] += 1
        for w in (r.get("unknown") or "").split():
            unknown[w] += 1
        if int(r.get("n") or 0) == 0:
            zero[q] += 1
        elif (r.get("quality") or "") == "partial":
            partial[q] += 1
        elif not (r.get("outcome") or ""):
            untouched[q] += 1
    OUT.mkdir(exist_ok=True)
    lines = [f"MOT DANG — WHAT THE BOX COULD NOT ANSWER · last {days} days · pulled {TODAY}",
             "=" * 72, "",
             f"{len(rows):,} searches logged · {len(asked):,} distinct questions",
             f"{sum(zero.values()):,} found nothing · {sum(partial.values()):,} half-matched · "
             f"{sum(untouched.values()):,} shown results nobody opened", ""]

    def block(title, counter, n=40):
        lines.append(title); lines.append("-" * len(title))
        if not counter:
            lines.append("  (none)")
        for k, v in counter.most_common(n):
            lines.append(f"  {v:4}  {k}")
        lines.append("")

    block("1. WORDS NOBODY UNDERSTOOD — a thesaurus line each", unknown)
    block("2. SEARCHES THAT FOUND NOTHING — a record or a shelf each", zero)
    block("3. SEARCHES THAT ONLY HALF-MATCHED", partial)
    block("4. SHOWN RESULTS, NOBODY OPENED ONE — the ranking to look at", untouched, 25)
    block("MOST ASKED", asked, 25)
    txt = "\n".join(lines) + "\n"
    (OUT / f"box-misses-{TODAY}.txt").write_text(txt, encoding="utf-8")
    (OUT / f"box-misses-{TODAY}.json").write_text(json.dumps(
        {"pulled": TODAY, "days": days, "searches": len(rows), "unknown": unknown.most_common(200),
         "zero": zero.most_common(200), "partial": partial.most_common(200),
         "untouched": untouched.most_common(100), "asked": asked.most_common(200)},
        ensure_ascii=False, indent=1), encoding="utf-8")
    print(txt)
    print(f"-> {OUT / f'box-misses-{TODAY}.txt'}")


if __name__ == "__main__":
    main()
