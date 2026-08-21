#!/usr/bin/env python3
"""The reply to paste back into the group — made from the data, not typed.

    python3 make_post.py khat-khi-khlai            # English, for a farang group
    python3 make_post.py khat-khi-khlai --th       # Thai
    python3 make_post.py --list                    # every question we hold

Why this exists: a reader asked where the glove scrub is, the answer went
back as a hand-typed paragraph, and the moment the site learned a walked
price the paragraph in that thread was wrong. A reply that is generated from
`data/asked.json` + the canonical records is remade in a second and cannot
disagree with the page it links to.

What comes out, in order: the question; the lead paragraph(s) from the data
file, placeholders filled with the live counts; one line per place — name,
where, phone, price shortened the way the card shortens it (a spread for a
multi-tier board, never a duration welded to the wrong price); the notes;
the page link; the card link. Plain text, no markup: LINE, Facebook and
WhatsApp all eat that. Where the price is unwalked it says so, because
that sentence is the one thing that must survive being pasted.

Prose is copied out verbatim — nothing here rewrites the data file's
sentences. If the reply reads badly, fix the data file: the page is wrong
in the same place.
"""
import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import asked_layer  # noqa: E402
from make_shelf_cards import price_of, where_line  # noqa: E402

BASE = "https://motdang.net/"


def place_line(r, lang):
    """One place, one line. Address stays as the record has it — the reply
    is not the place to invent a landmark."""
    bits = [r.get("name") or r.get("nameEn") or r["id"]]
    en = r.get("nameEn") or ""
    # the English name only when the Thai one has no Latin in it at all —
    # "The Home Massage and Spa (ระแกง) (The Home Massage and Spa (Ragang))"
    # is what the naive rule produced
    if lang == "en" and en and en != bits[0] and not re.search("[A-Za-z]", bits[0]):
        bits[0] = f"{bits[0]} ({en})"
    where = where_line(r) or (r.get("address") or "")[:60]
    if where:
        bits.append(where)
    if r.get("phone"):
        bits.append(r["phone"])
    price, verified = price_of(r)
    if price:
        bits.append(price)
    return "• " + " — ".join(bits), (price and not verified)


def post(entry, data, lang="en"):
    shown, counts = asked_layer.select(entry, data)
    key = entry["key"]
    out = [entry["q"][lang], ""]
    for p in entry.get("lead", []):
        out += [asked_layer._fill(p[lang], counts), ""]
    unverified = False
    for r in shown:
        line, unver = place_line(r, lang)
        out.append(line)
        unverified = unverified or unver
    if shown:
        out.append("")
    for p in entry.get("notes", []):
        out += [asked_layer._fill(p[lang], counts), ""]
    if unverified:
        out += ["ราคาตามที่ร้านบอก ยังไม่ได้เดินตรวจ" if lang == "th"
                else "Prices are as the shops quote them — not walked yet.", ""]
    ask = entry.get("ask_at_the_door")
    if ask and lang == "en":
        out += [f'The sentence to ask at the door: "{ask["th"]}" — {ask["en"]}', ""]
    out.append(f"{BASE}asked/{key}.html")
    if entry.get("shelf"):
        out.append(f"{BASE}{entry['shelf']}")
    card = ROOT / "assets" / "og" / f"asked-{key}.png"
    if card.exists():
        out.append(f"{BASE}og/asked-{key}.png")
    return "\n".join(out).rstrip() + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("key", nargs="?")
    ap.add_argument("--th", action="store_true", help="Thai instead of English")
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args()

    entries = {e["key"]: e for e in asked_layer.load(include_drafts=True)}
    if args.list or not args.key:
        for k, e in entries.items():
            print(f"{k:20} {'DRAFT ' if e.get('draft') else '      '}{e['q']['th']}")
        return
    if args.key not in entries:
        sys.exit(f"no such question: {args.key} — try --list")
    if entries[args.key].get("draft"):
        sys.exit(f"{args.key} is still a draft — fill find/lead/notes in data/asked.json "
                 "and delete \"draft\" first; a reply to a half-answered question is not one")

    import build  # the data, loaded exactly as the site loads it
    data = build.load()
    sys.stdout.write(post(entries[args.key], data, "th" if args.th else "en"))


if __name__ == "__main__":
    main()
