"""Short place IDs — MD-4F2K9 — that a person can read aloud, type, or paste into LINE.

Michael, 2026-09-28, through Nan: he wants to work with place IDs and maps
directly. The record ids (cm-curated-fubar, cm-osm-node-1234567890) are too
long to say or type.

A code is Crockford base32 (no I, L, O, U) of sha1(record id), cut to the
shortest prefix of at least five characters that no other place holds. The
register data/curated/place_codes.json is append-only: once a place has a code
it keeps it, so a code written on paper or sent in a chat still opens the
same place after the catalogue grows. A record that leaves the catalogue keeps
its row, so its code is not handed to a different place.

The site gets docs/data/codes/<first char>.json — {code: "cm/slug"} — so the
map can look a code up with one small fetch."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REG = ROOT / "data" / "curated" / "place_codes.json"
ALPHA = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
MIN_LEN = 5


def _b32(raw: bytes) -> str:
    n, out = int.from_bytes(raw, "big"), []
    for _ in range(len(raw) * 8 // 5):
        out.append(ALPHA[n & 31])
        n >>= 5
    return "".join(reversed(out))


def load():
    try:
        return json.loads(REG.read_text())
    except (OSError, ValueError):
        return {}


def assign(ids):
    """Codes for every id, adding new ones to the register. Returns {id: code}."""
    reg = load()
    used = set(reg.values())
    added = 0
    for i in sorted(set(ids)):
        if i in reg:
            continue
        h = _b32(hashlib.sha1(i.encode("utf-8")).digest())
        n = MIN_LEN
        while h[:n] in used:
            n += 1
        reg[i] = h[:n]
        used.add(h[:n])
        added += 1
    if added:
        REG.write_text(json.dumps(reg, ensure_ascii=False, sort_keys=True, indent=0))
    return reg


def emit(docs, paths):
    """paths: {record id: "cm/slug"} for places that have a page this build."""
    reg = load()
    shards = {}
    for i, path in paths.items():
        c = reg.get(i)
        if c:
            shards.setdefault(c[0], {})[c] = path
    out = Path(docs) / "data" / "codes"
    out.mkdir(parents=True, exist_ok=True)
    for k, v in shards.items():
        (out / f"{k}.json").write_text(json.dumps(v, ensure_ascii=False, separators=(",", ":")))
    return f"{sum(len(v) for v in shards.values()):,} codes in {len(shards)} shards"


def show(code):
    return "MD-" + code
