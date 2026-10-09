"""Run tests/find_cases.json against /find and print which searches land.

A case passes when one of its `want` addresses is in the top `n`. A case marked
`held: false` cannot pass until its record exists; it prints as NOT HELD rather
than FAIL, so the count of real search misses stays readable.

  python3 tests/test_find_cases.py                  # the live site
  python3 tests/test_find_cases.py --base URL       # a preview Worker
  python3 tests/test_find_cases.py --pull           # also list untapped queries from the tap log
Exit status is 1 when a case that passed in the last run fails now.
"""

from __future__ import annotations

import json
import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CASES = ROOT / "tests" / "find_cases.json"
LAST = ROOT / "cache" / "find_cases.last.json"


def ask(base: str, q: str) -> list[str]:
    url = f"{base}/find?fmt=json&q={urllib.parse.quote(q)}"
    req = urllib.request.Request(url, headers={"user-agent": "motdang-find-cases"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return [x.get("url", "") for x in json.load(r).get("results", [])]


def untapped() -> list[str]:
    """Queries a person left without tapping anything (fleetsearch/learn.sql)."""
    out = subprocess.run(
        ["npx", "wrangler", "d1", "execute", "motdang-search", "--remote", "--json",
         "--command", "SELECT qk FROM learn_q WHERE tapped = 0 ORDER BY last DESC"],
        cwd=ROOT / "publish", capture_output=True, text=True)
    try:
        return [r["qk"] for r in json.loads(out.stdout)[0]["results"]]
    except (ValueError, KeyError, IndexError):
        return []


def main(argv: list[str]) -> int:
    base = "https://motdang.net"
    if "--base" in argv:
        base = argv[argv.index("--base") + 1].rstrip("/")
    cases = json.loads(CASES.read_text())["cases"]
    last = json.loads(LAST.read_text()) if LAST.exists() else {}
    now, regressed = {}, []
    tally = {"PASS": 0, "FAIL": 0, "NOT HELD": 0}
    for c in cases:
        urls = ask(base, c["q"])
        top = urls[: c.get("n", 3)]
        hit = next((i + 1 for i, u in enumerate(urls) if any(w in u for w in c["want"])), 0)
        ok = 0 < hit <= c.get("n", 3)
        mark = "PASS" if ok else ("NOT HELD" if c.get("held") is False else "FAIL")
        tally[mark] += 1
        now[c["q"]] = ok
        if last.get(c["q"]) and not ok:
            regressed.append(c["q"])
        where = f"at {hit}" if hit else "absent"
        print(f"{mark:8}  {c['q']:28} {where:8} {c.get('cause', '')}")
        if not ok and top:
            print(f"{'':10}top: {top[0][-70:]}")
    print(f"\n{tally['PASS']} pass · {tally['FAIL']} fail · {tally['NOT HELD']} not held")
    if regressed:
        print("worse than last run: " + ", ".join(regressed))
    if base == "https://motdang.net":
        LAST.parent.mkdir(exist_ok=True)
        LAST.write_text(json.dumps(now, ensure_ascii=False, indent=1))
    if "--pull" in argv:
        known = {c["q"].lower() for c in cases}
        fresh = [q for q in untapped() if q not in known]
        print("\nuntapped, not yet a case: " + (", ".join(fresh) if fresh else "none"))
    return 1 if regressed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
