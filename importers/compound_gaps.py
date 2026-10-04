#!/usr/bin/env python3
"""compound_gaps.py — searches that name a drug or compound and found no ready answer.

The lexicon grows from what readers type (Nan, 2026-10-04: "systemic and planned"). Reads three
logs read-only — the site search box (white-label-ai box_log), the /find learning log
(motdang-search learn_q) and the reader assistant (white-label-ai search_log, tenant 3) — keeps
the queries shaped like a compound (a drug suffix, a code like BPC-157, or a word the Thai drug
register knows), drops those an answer already catches, and writes notes/compound-gaps.txt,
one line each, most-asked first. Add a row to data/curated/compounds.json for each real one,
then: fda_register.py <id> && answers_compounds.py.

    python3 importers/compound_gaps.py [--days 30]
"""
import json
import os
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
WLA = ROOT.parent / "white-label-ai"
OUT = ROOT / "notes" / "compound-gaps.txt"
ANSWERS = [ROOT / "data" / "curated" / f for f in ("answers_compounds.json", "answers_health.json")]

# the endings drug names share, and the code shape research compounds use
SUFFIX = re.compile(r"(tide|relin|morelin|rphin|mab|nib|zole|olone|sterone|terone|pril|sartan|statin|azepam|"
                    r"zolam|fil|mycin|cillin|floxacin|prazole|triptan|setron|tidine|lukast|gliptin|gliflozin|"
                    r"glutide|dronate|parin|xaban|vir|azole|afil|amine|oxetine|aline|apine|idone|olol|dipine|"
                    r"thiazide|semide|cycline|trel|gestrel|estrol|tropin|peptide|sarm)\b", re.I)
CODE = re.compile(r"\b[a-z]{2,5}-?\d{2,5}\b", re.I)  # BPC-157, MK677; not "size 43"
WORDS = re.compile(r"\b(peptide|steroid|sarm|hormone|injection|pill|tablet|ยา|ฮอร์โมน|เปปไทด์|สเตียรอยด์)\b", re.I)


def d1(db, sql, cwd):
    env = dict(os.environ)
    if "CLOUDFLARE_API_TOKEN" not in env:
        keys = json.loads((pathlib.Path.home() / ".config/nanobotco/keys.json").read_text())
        env["CLOUDFLARE_API_TOKEN"] = keys["cloudflare"]["api_token"]
    r = subprocess.run(["npx", "wrangler", "d1", "execute", db, "--remote", "--json", "--command", sql],
                       cwd=cwd, env=env, capture_output=True, text=True, timeout=180)
    try:
        return json.loads(r.stdout)[0].get("results", [])
    except (ValueError, IndexError):
        print(f"  {db}: no answer ({r.stderr.strip()[:120]})")
        return []


def fold(s):
    return re.sub(r"[^\w฀-๿]+", " ", (s or "").lower()).strip()


def main(argv):
    days = int(argv[argv.index("--days") + 1]) if "--days" in argv else 30
    asked = {}
    for row in d1("white-label-ai", f"SELECT q, n FROM box_log WHERE source='box' AND q<>'' AND ts > datetime('now','-{days} days')", WLA):
        asked[row["q"]] = asked.get(row["q"], 0) + 1
    for row in d1("white-label-ai", f"SELECT question AS q FROM search_log WHERE tenant_id=3 AND ts > datetime('now','-{days} days')", WLA):
        asked[row["q"]] = asked.get(row["q"], 0) + 1
    for row in d1("motdang-search", f"SELECT qk AS q, views FROM learn_q WHERE last > datetime('now','-{days} days')", ROOT / "publish"):
        asked[row["q"]] = asked.get(row["q"], 0) + int(row.get("views") or 1)

    triggers = set()
    for p in ANSWERS:
        if p.exists():
            for a in json.loads(p.read_text(encoding="utf-8"))["answers"]:
                triggers.update(fold(w) for w in a.get("w", []))

    gaps = []
    for q, n in asked.items():
        fq = fold(q)
        if not (SUFFIX.search(fq) or CODE.search(fq) or WORDS.search(fq)):
            continue
        if any(t and (f" {t} " in f" {fq} ") for t in triggers):
            continue
        gaps.append((n, q))
    gaps.sort(key=lambda x: (-x[0], x[1].lower()))
    lines = [f"COMPOUND GAPS — searches shaped like a drug or compound with no ready answer, last {days} days",
             "Each real one becomes a row in data/curated/compounds.json; then fda_register.py <id> and answers_compounds.py.", ""]
    lines += [f"{n:4}  {q}" for n, q in gaps] or ["(none)"]
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"compound_gaps: {len(gaps)} of {len(asked)} queries -> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main(sys.argv[1:])
