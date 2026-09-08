"""The self-hosted type, fetched and subset — assets/fonts/.

A font from someone else's CDN is a request the reader never asked to make,
and on this site it would also be a request to Google on every page. So the
faces are fetched once, here, and served from our own bucket.

    python3 importers/fetch_fonts.py            # fetch what FACES names
    python3 importers/fetch_fonts.py --list     # print what is on disk

Google's CSS API is the source because it is the only place that publishes the
per-script subsets already cut: asking for one family with a modern browser's
user agent returns woff2 URLs split by unicode-range, and a Thai reader then
downloads no Latin at all. Everything here is SIL Open Font Licence 1.1 and
the licence file travels with the woff2 into docs/fonts/ (build.py).
"""
import json
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "fonts"

# family → (weights, the subsets we keep)
#
# READING order matters only for the manifest. What each face is FOR:
#   JetBrains Mono   the Latin reading face. Every figure on this site is a
#                    fact somebody acts on — a phone number they dial, a price,
#                    an opening hour, a distance — and its zero is slashed, its
#                    1lI are three different shapes, and its figures are one
#                    width, so a column of them lines up and a dialled number
#                    cannot be misread. It carries no Thai and is never asked to.
#   Prompt           the Thai reading face, and the Latin fallback inside a
#                    Thai run. Already on the site; now it does the body too.
#   Atkinson Hyperlegible   the easy-read Latin face, from the Braille
#                    Institute, drawn so that letters which collapse into each
#                    other at low acuity do not.
#   Sarabun          the easy-read Thai face. LOOPED (ตัวมีหัว) where Prompt is
#                    loopless: the loop is the letter's identifying mark and it
#                    is the first thing to go at low acuity or small size.
FACES = {
    "JetBrains Mono": ([400, 700], ("latin", "latin-ext")),
    "Prompt": ([400, 600], ("latin", "latin-ext", "thai")),
    "Atkinson Hyperlegible": ([400, 700], ("latin", "latin-ext")),
    "Sarabun": ([400, 600], ("latin", "latin-ext", "thai")),
}
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")


def get(url, binary=False):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read() if binary else r.read().decode()


def slug(family):
    return family.lower().replace(" ", "-")


def fetch(family, weights, keep):
    css = get("https://fonts.googleapis.com/css2?family="
              + family.replace(" ", "+") + ":wght@" + ";".join(str(w) for w in weights)
              + "&display=swap")
    rows, subset = [], None
    for block in css.split("@font-face")[0:]:
        m = re.search(r"/\*\s*([a-z0-9-]+)\s*\*/", block)
        if m and "font-family" not in block:
            subset = m.group(1)
            continue
        if "font-family" not in block:
            continue
        sub = subset
        m = re.search(r"/\*\s*([a-z0-9-]+)\s*\*/\s*$", block)
        if m:
            subset = m.group(1)
        if sub not in keep:
            continue
        w = int(re.search(r"font-weight:\s*(\d+)", block).group(1))
        url = re.search(r"src:\s*url\(([^)]+)\)", block).group(1)
        rng = re.search(r"unicode-range:\s*([^;}]+)", block).group(1).strip()
        data = get(url, binary=True)
        # A VARIABLE font answers every weight with one file — JetBrains Mono
        # does, and asking for 400 and 700 downloaded the same 31 kB twice and
        # declared it twice. One file, one @font-face, `font-weight: 400 700`,
        # and the browser interpolates. Detected by the bytes rather than by a
        # list of which families are variable, because that list goes stale.
        same = next((r for r in rows if r["subset"] == sub and r["_b"] == data), None)
        if same:
            same["weight"] = f'{min(int(same["weight"].split()[0]), w)} {max(int(same["weight"].split()[-1]), w)}'
            continue
        name = f"{slug(family)}-{w}-{sub}.woff2"
        (OUT / name).write_bytes(data)
        rows.append({"family": family, "weight": str(w), "subset": sub,
                     "file": name, "range": rng, "_b": data})
        print(f"  {name:44s} {(OUT / name).stat().st_size:>7,} b")
    return rows


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    if "--list" in sys.argv:
        for f in sorted(OUT.glob("*.woff2")):
            print(f"{f.name:44s} {f.stat().st_size:>7,} b")
        return
    rows = []
    for family, (weights, keep) in FACES.items():
        print(family)
        rows += fetch(family, weights, keep)
    for r in rows:
        r.pop("_b", None)
    (OUT / "_manifest.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1))
    (OUT / "_faces.css").write_text("\n".join(
        f"@font-face{{font-family:'{r['family']}';font-style:normal;"
        f"font-weight:{r['weight']};font-display:swap;"
        f"src:url(fonts/{r['file']}) format('woff2');unicode-range:{r['range']}}}"
        for r in rows) + "\n")
    total = sum((OUT / r["file"]).stat().st_size for r in rows)
    print(f"\n{len(rows)} files, {total:,} bytes")


if __name__ == "__main__":
    main()
