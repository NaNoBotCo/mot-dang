#!/usr/bin/env python3
"""ALPHA ONLY — pull the testers' thumbs out of the worker and write them
somewhere Nan can read them. Delete this file at beta.

Every report is emailed to 530kings@proton.me the moment it is sent, so this
is the second copy, not the first: the whole queue in one file, and a plain-
text digest of it, for reading a week of testing in one sitting.

    python3 importers/sync_alpha.py            # data/alpha_reports.json + the digest
    python3 importers/sync_alpha.py --print    # digest to the terminal as well

The key. `GET /alpha-reports` answers only to the ALPHA_KEY secret, because
the reports carry free text written by named people. The key lives OUTSIDE the
repo, the same arrangement as the showtimes recipe and the LINE token:

    ~/.mot-dang-alpha.json    {"key": "…"}     (or $MD_ALPHA_KEY)

and it is set on the worker with:

    cd worker && npx wrangler secret put ALPHA_KEY

Without a key this exits saying so and writes nothing — an unreadable queue is
not an empty one.

Screenshots stay in R2 (`alpha/<report id>/1.jpg`) and are not pulled here;
the ones small enough to travel are already attached to the email, and the
digest names the key of every one so a picture can always be found.
"""
import argparse
import json
import os
import urllib.error
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# MD_ALPHA_URL points this at `wrangler dev` while the route is being worked on.
WORKER_URL = os.environ.get("MD_ALPHA_URL") or "https://mot-dang-claims.nanobotco.workers.dev"
OUT = os.path.join(ROOT, "data", "alpha_reports.json")
DIGEST = os.path.join(ROOT, "notes", "alpha-reports.txt")
UA = "MotDangAlphaSync/1.0 (+https://motdang.net/)"


def key():
    k = os.environ.get("MD_ALPHA_KEY", "").strip()
    if k:
        return k
    p = os.path.expanduser("~/.mot-dang-alpha.json")
    if os.path.exists(p):
        try:
            return str(json.load(open(p)).get("key", "")).strip()
        except (ValueError, OSError):
            return ""
    return ""


def digest(reports):
    """One block per report, newest first, wide enough to read on a phone."""
    out = []
    up = sum(1 for r in reports if r.get("v") == "up")
    down = len(reports) - up
    out.append("ALPHA REPORTS — มดแดง Mot Dang")
    out.append(f"{len(reports)} in all · {up} worked · {down} went wrong")
    out.append("")
    for r in sorted(reports, key=lambda r: str(r.get("at", "")), reverse=True):
        c = r.get("ctx") or {}
        out.append("=" * 68)
        out.append(f"{'WORKED' if r.get('v') == 'up' else 'WENT WRONG'}"
                   f" — {r.get('who') or 'unnamed tester'} — {r.get('at', '')}")
        out.append(c.get("url", ""))
        if c.get("q"):
            out.append(f"searched: {c['q']}")
        if r.get("note"):
            out.append("")
            out.append(r["note"])
        out.append("")
        counts = c.get("counts") or {}
        if counts:
            out.append("on the page: "
                       + " · ".join(f"{k} {v}" for k, v in counts.items()))
        for m in (c.get("map") or []):
            out.append("map: " + (f"{m.get('lat')},{m.get('lng')} z{m.get('z')}"
                                  if m.get("live") else "no tiles"))
        for e in (c.get("errs") or []):
            out.append(f"  error {e.get('at')}ms  {e.get('m')}  {e.get('f', '')}")
        for n in (c.get("nets") or []):
            out.append(f"  request {n.get('s')}  {n.get('u')}  {n.get('ms')}ms")
        for t in (c.get("trail") or []):
            out.append(f"  tap {t.get('at')}ms  {t.get('t')} {t.get('x', '')} "
                       f"{t.get('h', '')} {t.get('d', '')}".rstrip())
        for s in (r.get("shots") or []):
            out.append(f"  picture {s.get('key')} ({round((s.get('bytes') or 0) / 1000)} kB)")
        for d in (r.get("dropped") or []):
            out.append(f"  picture NOT kept — {d.get('name')} ({d.get('why')})")
        out.append(f"  build {r.get('build', '?')} · {c.get('view', '')} · "
                   f"{c.get('lang', '')} · {c.get('net', 'connection unknown')} · "
                   f"service worker {'on' if c.get('sw') else 'off'}")
        if c.get("ua"):
            out.append(f"  {c['ua']}")
        out.append(f"  {r.get('id', '')}")
        out.append("")
    return "\n".join(out) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--print", dest="show", action="store_true",
                    help="print the digest as well as writing it")
    args = ap.parse_args()

    k = key()
    if not k:
        print("🐜 no ALPHA_KEY — put {\"key\": \"…\"} in ~/.mot-dang-alpha.json "
              "or set MD_ALPHA_KEY. Nothing written.")
        return 1

    url = WORKER_URL + "/alpha-reports?key=" + urllib.parse.quote(k)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = json.loads(resp.read())
    except urllib.error.HTTPError as err:
        if err.code == 404:
            print("🐜 the worker did not recognise the key (or ALPHA_KEY is not set "
                  "on it: cd worker && npx wrangler secret put ALPHA_KEY). "
                  "Nothing written.")
        else:
            print(f"🐜 worker said {err.code} — keeping what is on disk.")
        return 1
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as err:
        have = os.path.exists(OUT)
        print(f"🐜 worker unreachable ({err}) — "
              + ("keeping the reports already on disk" if have
                 else "no reports file yet, nothing written"))
        return 1

    reports = payload.get("reports", [])
    if not reports and os.path.exists(OUT):
        existing = json.load(open(OUT)).get("reports", [])
        if existing:
            print(f"🐜 worker returned 0 but {len(existing)} are on disk — keeping them.")
            return 0

    with open(OUT, "w") as fh:
        json.dump({"count": len(reports), "reports": reports}, fh,
                  ensure_ascii=False, indent=1)
    text = digest(reports)
    os.makedirs(os.path.dirname(DIGEST), exist_ok=True)
    with open(DIGEST, "w") as fh:
        fh.write(text)
    if args.show:
        print(text)
    print(f"🐜 {len(reports)} alpha report(s) -> {OUT}")
    print(f"🐜 readable copy -> {DIGEST}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
