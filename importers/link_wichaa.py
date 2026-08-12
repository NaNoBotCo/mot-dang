#!/usr/bin/env python3
"""Match Mot Dang's temples to their pages in the wichaa vault.

Two of this household's properties hold the same 1,300-odd temples and neither
has ever pointed at the other. Mot Dang knows where a wat is, when it opens and
how to reach it; wichaa knows what is practised there. A reader who wants both
has had to know that both sites exist.

    python3 importers/link_wichaa.py [--vault PATH]

Writes data/wichaa_links.json, read by build.py. Nothing is imported across
repos at build time — the sibling is read once here and baked, the same shape
as make_sky.py reading jovilabe. If the vault is not on this machine the file
is left alone and the links simply do not render.

MATCHING. An exact Thai name and nothing else is NOT a match, and the failure
is not hypothetical: วัดสวนดอก is a real temple in Chiang Mai, another in
Chiang Rai and a third in Lamphun, and the vault holds all three. So a link is
only written where the name agrees AND the two records stand within
NEAR_M metres of each other. A wrong link here would send a reader to the
devotional page of a temple in another province, which is worse than no link —
the same reasoning that made harvest_commons.py demand name corroboration
rather than trusting proximity, run the other way round.

HOST. wichaa is published to its own domain and mirrored on Cloudflare. Which
one is written into the links is decided by asking them, here, at generation
time — this catalogue does not hyperlink a URL it has watched fail (see
check_links.py and reach_block). The answer and its date go in the file, so a
regeneration after the domain recovers flips every link back on its own.
"""
import argparse
import json
import math
import re
import unicodedata
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "wichaa_links.json"
DEFAULT_VAULT = ROOT.parent / "wichaa-vault" / "places"
UA = "mot-dang-directory/1.0 (+https://github.com/NaNoBotCo/mot-dang; sibling link check)"

# Preferred first. The apex is the name to publish when it answers; the mirror
# is the lifeboat that keeps the links alive while it does not.
HOSTS = ["https://wichaa.net", "https://wichaa.pages.dev"]
PROBE = "/place/wat-suan-dok-monk-chat/"
NEAR_M = 400.0


def norm(s):
    """Fold a Thai name to something comparable without fusing distinct names.

    Only whitespace, the ำ/ํา spelling split and bracketed asides are touched.
    Nothing is transliterated and no characters are dropped: วัดป่าแดง and
    วัดป่าแดด differ by one letter and are two temples.
    """
    if not s:
        return ""
    s = unicodedata.normalize("NFC", s)
    s = re.sub(r"[(（].*?[)）]", " ", s)
    return re.sub(r"\s+", "", s).strip()


def haversine(a, b, c, d):
    r = 6371000.0
    p1, p2 = math.radians(a), math.radians(c)
    dp, dl = math.radians(c - a), math.radians(d - b)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


def front_matter(text):
    """The handful of fields this needs, without a YAML dependency."""
    out = {}
    if not text.startswith("---"):
        return out
    body = text.split("---", 2)[1] if text.count("---") >= 2 else ""
    for line in body.splitlines():
        m = re.match(r'^([a-z_]+):\s*"?(.*?)"?\s*$', line)
        if m and m.group(2):
            out.setdefault(m.group(1), m.group(2))
    return out


def read_vault(vault):
    notes = []
    for f in sorted(Path(vault).glob("*.md")):
        fm = front_matter(f.read_text(encoding="utf-8", errors="ignore"))
        try:
            lat, lng = float(fm.get("lat", "")), float(fm.get("lng", ""))
        except ValueError:
            lat = lng = None
        notes.append({"id": fm.get("id") or f.stem, "th": fm.get("name_th", ""),
                      "roman": fm.get("name_roman", ""), "type": fm.get("type", ""),
                      "lat": lat, "lng": lng})
    return notes


def live_host():
    """Ask which host answers. Falls back to the apex rather than to nothing."""
    for h in HOSTS:
        try:
            req = urllib.request.Request(h + PROBE, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=20) as r:
                if r.status == 200:
                    return h, "answered"
        except Exception:
            continue
    return HOSTS[0], "none answered — links written against the canonical host"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vault", default=str(DEFAULT_VAULT))
    args = ap.parse_args()
    vault = Path(args.vault)
    if not vault.exists():
        print(f"🐜 no wichaa vault at {vault} — leaving {OUT.name} as it is")
        return

    notes = read_vault(vault)
    by_name = {}
    for n in notes:
        if n["th"] and n["lat"] is not None:
            by_name.setdefault(norm(n["th"]), []).append(n)

    records = []
    for f in sorted((ROOT / "data" / "canonical").glob("*.json")):
        d = json.loads(f.read_text())
        records += d if isinstance(d, list) else (d.get("places") or d.get("records") or [])

    host, why = live_host()
    links, ambiguous, name_only = {}, 0, 0
    for r in records:
        if r.get("lat") is None:
            continue
        key = norm(r.get("nameTh") or r.get("name"))
        cands = by_name.get(key)
        if not cands:
            continue
        near = [(haversine(r["lat"], r["lng"], n["lat"], n["lng"]), n) for n in cands]
        near = [(d, n) for d, n in near if d <= NEAR_M]
        if not near:
            # The name is in the vault but that one is somewhere else — a
            # different temple wearing the same name. Counted, never linked.
            name_only += 1
            continue
        near.sort(key=lambda x: x[0])
        if len(near) > 1 and near[1][0] - near[0][0] < 50:
            ambiguous += 1
            continue
        d, n = near[0]
        links[r["id"]] = {"slug": n["id"], "url": f"{host}/place/{n['id']}/",
                          "name_th": n["th"], "name_roman": n["roman"],
                          "type": n["type"], "metres": round(d)}

    OUT.write_text(json.dumps({
        "generated": date.today().isoformat(),
        "host": host, "host_note": why,
        "rule": (f"exact Thai name AND within {NEAR_M:.0f} m — a name alone is not "
                 "identity, three provinces hold a วัดสวนดอก"),
        "vault_notes": len(notes), "matched": len(links),
        "same_name_elsewhere": name_only, "too_close_to_call": ambiguous,
        "links": links}, ensure_ascii=False, indent=1))
    print(f"🐜 {len(links)} temples matched to wichaa ({len(notes)} vault notes) -> {OUT}")
    print(f"   host {host} — {why}")
    print(f"   {name_only} share a name with a vault place that stands elsewhere, "
          f"{ambiguous} too close to call; both left unlinked")


if __name__ == "__main__":
    main()
