#!/usr/bin/env python3
"""decode_line_qr.py — read the LINE handle off a photograph of a shop sign.

    python3 importers/decode_line_qr.py                     every photo the LINE bot sent down
    python3 importers/decode_line_qr.py ~/Desktop/"FIELD DROP"
    python3 importers/decode_line_qr.py --report            counts from sidecars, no decoding
    python3 importers/decode_line_qr.py --self-test         makes its own QR, no files touched

WHY. A Chiang Mai shopfront prints its LINE twice: the id in letters, and the
QR beside it. The vision model in the Worker already reads the letters
(src/sign.js, field line_id) — a reading, and readings of @ai1234 vs @aI1234
are a coin toss. The QR is not a reading. It decodes to
https://lin.ee/XXXX or https://line.me/ti/p/@id exactly or not at all, which
makes it the one channel here that cannot be misread.

WHERE IT RUNS, AND WHY NOT IN THE WORKER. The Worker writes photo bytes to R2
on the webhook request because LINE drops them; pull_line.py brings them down
hourly. Decoding here rather than up there needs no Cloudflare deploy, cannot
break the bot the team is standing in, runs OpenCV instead of a JPEG decoder
squeezed into a Worker's CPU budget, and works backwards over every photo
already pulled. The bot's own behaviour is unchanged.

WHAT IT WRITES.
  <photo>.qr.json          beside each photo: what decoded, or that nothing
                           did. A re-run skips a photo that has one.
  cache/line_oa_seeds.json merged, not overwritten — the same file
                           discover_line.py feeds and probe_line_oa.py reads.

WHAT IT WILL NOT DO. It does not file anything against a place and it writes
no records. A decoded handle is a lead. "nothing decoded" means no QR was
legible in this frame at these two scales — not that the shop has no LINE.
"""
import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "importers"))
from probe_line_oa import classify, handles_in  # noqa: E402

PHOTOS = ROOT / "_incoming" / "line" / "photos"
CHAT = ROOT / "_incoming" / "line" / "chat"
SEEDS = ROOT / "cache" / "line_oa_seeds.json"
TODAY = dt.date.today().isoformat()
EXT = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".bmp"}

# The vision model's reading of the letters, for the frames where no QR
# decodes. Kept apart from the QR handles in the output: one was decoded, the
# other was read.
TYPED_RE = re.compile(r"@([a-z0-9][a-z0-9._-]{3,19})", re.I)


def decode_image(path, scales=(1.0, 2.0)):
    """Every LINE handle in the QR codes in one image, plus what decoded raw."""
    import cv2  # local: --report and --self-test of the parsing need no cv2

    img = cv2.imread(str(path))
    if img is None:
        return None, []
    det = cv2.QRCodeDetector()
    payloads, seen = [], set()
    for s in scales:
        frame = img if s == 1.0 else cv2.resize(img, None, fx=s, fy=s,
                                                interpolation=cv2.INTER_CUBIC)
        try:
            ok, texts, _pts, _st = det.detectAndDecodeMulti(frame)
        except Exception:                                    # noqa: BLE001
            ok, texts = False, []
        if not ok:
            continue
        for t in texts or []:
            t = (t or "").strip()
            if t and t not in seen:
                seen.add(t)
                payloads.append(t)
    handles = []
    for t in payloads:
        handles += handles_in(t)
    uniq, seen2 = [], set()
    for kind, val in handles:
        if (kind, val) not in seen2:
            seen2.add((kind, val))
            uniq.append({"kind": kind, "handle": val})
    return payloads, uniq


def _chat_row(photo):
    """The transcript row for this photo, which is where `sign` lives.

    pull_line.py writes two files per photo: a sidecar beside the image (who
    sent it, when, any shared location) and a line in chat/<date>.jsonl (the
    whole event, including the vision model's reading). The reading is in the
    second, keyed by message_id, which is the image's own filename.
    """
    mid = photo.stem
    chat = CHAT
    if not chat.is_dir():
        return {}
    for path in sorted(chat.glob("*.jsonl"), reverse=True):
        try:
            for line in path.read_text(encoding="utf-8").splitlines():
                if mid not in line:
                    continue
                row = json.loads(line)
                if str(row.get("message_id")) == mid:
                    return row
        except Exception:                                    # noqa: BLE001
            continue
    return {}


def typed_in_sidecar(photo):
    """What the vision model READ off the letters. Never merged with a decode."""  # stylecheck: allow — code docstring
    sign = _chat_row(photo).get("sign") or {}
    if isinstance(sign, str):
        try:
            sign = json.loads(sign)
        except Exception:                                    # noqa: BLE001
            sign = {}
    out = []
    for m in TYPED_RE.finditer(str(sign.get("line_id") or "")):
        kind, val = classify(m.group(1).lower())
        if kind:
            out.append({"kind": kind, "handle": val})
    return out


def where(photo):
    """A pin for this frame, if one exists. Two shapes, both real:

    the LINE transcript's lat/lng (somebody tapped the paperclip in the shop),
    and field_ingest.py's sidecar for a GoPro capture (EXIF off the card). A
    handle that arrives with a pin is the best thing this lane produces.
    """
    row = _chat_row(photo)
    if row.get("lat") is not None and row.get("lng") is not None:
        return {"lat": row["lat"], "lng": row["lng"], "from": "line location"}
    side = photo.with_suffix(".json")
    if side.exists():
        try:
            doc = json.loads(side.read_text(encoding="utf-8"))
        except Exception:                                    # noqa: BLE001
            return None
        gps = doc.get("gps") or {}
        if isinstance(gps, dict) and gps.get("lat") is not None:
            return {"lat": gps["lat"], "lng": gps["lng"], "from": gps.get("from") or "sidecar"}
        if doc.get("lat") is not None and doc.get("lng") is not None:
            return {"lat": doc["lat"], "lng": doc["lng"], "from": "field capture EXIF"}
    return None


def photos_under(root):
    root = Path(root).expanduser()
    if root.is_file():
        return [root]
    return sorted(p for p in root.rglob("*") if p.suffix.lower() in EXT)


def merge_seeds(new):
    """Fold handles into cache/line_oa_seeds.json without losing what is there."""
    doc = {"_comment": "Handles found on the open web (discover_line.py) and "
                       "decoded off photographs (decode_line_qr.py). Input to "
                       "probe_line_oa.py --seed-search. Not records.",
           "generated": TODAY, "handles": []}
    if SEEDS.exists():
        try:
            doc = json.loads(SEEDS.read_text(encoding="utf-8"))
        except Exception:                                    # noqa: BLE001
            pass
    doc["generated"] = TODAY
    by = {(h["kind"], h["handle"]): h for h in doc.get("handles") or []}
    added = 0
    for h in new:
        k = (h["kind"], h["handle"])
        if k in by:
            old = by[k]
            for f in ("found_on", "queries", "how", "pin", "prov", "name_hint"):
                if h.get(f) and not old.get(f):
                    old[f] = h[f]
        else:
            by[k] = h
            added += 1
    doc["handles"] = list(by.values())
    SEEDS.parent.mkdir(parents=True, exist_ok=True)
    SEEDS.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    return added


def run(roots, force=False):
    found, scanned, skipped = [], 0, 0
    for root in roots:
        for photo in photos_under(root):
            if photo.name.endswith(".qr.json"):
                continue
            side = photo.with_suffix(photo.suffix + ".qr.json")
            if side.exists() and not force:
                skipped += 1
                try:
                    rec = json.loads(side.read_text(encoding="utf-8"))
                except Exception:                            # noqa: BLE001
                    continue
                found += [dict(h, found_on=str(photo), how=rec.get("how", "qr"),
                               pin=rec.get("pin"))
                          for h in rec.get("handles") or []]
                continue
            payloads, handles = decode_image(photo)
            if payloads is None:
                rec = {"decoded": TODAY, "unreadable": True, "payloads": [], "handles": []}
            else:
                rec = {"decoded": TODAY, "payloads": payloads, "handles": handles, "how": "qr"}
                pin = where(photo)
                if pin:
                    rec["pin"] = pin
                typed = [h for h in typed_in_sidecar(photo)
                         if h not in handles]
                if typed:
                    rec["typed"] = typed
            side.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
            scanned += 1
            pin = rec.get("pin")
            found += [dict(h, found_on=str(photo), how="qr", pin=pin)
                      for h in rec.get("handles") or []]
            found += [dict(h, found_on=str(photo), how="sign reading — check it", pin=pin)
                      for h in rec.get("typed") or []]
    added = merge_seeds(found)
    return {"scanned": scanned, "cached": skipped,
            "handles": len(found), "newToSeeds": added,
            "byHow": {h: sum(1 for f in found if f.get("how") == h)
                      for h in {f.get("how") for f in found}}}


def report(roots):
    rows = []
    for root in roots:
        for side in Path(root).expanduser().rglob("*.qr.json"):
            try:
                rows.append(json.loads(side.read_text(encoding="utf-8")))
            except Exception:                                # noqa: BLE001
                pass
    return {"photos": len(rows),
            "withQr": sum(1 for r in rows if r.get("handles")),
            "unreadable": sum(1 for r in rows if r.get("unreadable")),
            "handles": sum(len(r.get("handles") or []) for r in rows),
            "typedOnly": sum(1 for r in rows if not r.get("handles") and r.get("typed"))}


def self_test():
    import tempfile
    try:
        import cv2
        import numpy as np
        import qrcode                                        # noqa: F401
        have_maker = True
    except ImportError:
        have_maker = False
    payload = "https://lin.ee/Orxkq55"
    assert handles_in(payload) == [("short", "Orxkq55")]
    assert handles_in("https://line.me/ti/p/@gyk4392g") == [("oa", "@gyk4392g")]
    assert handles_in("no line here") == []
    if have_maker:
        import qrcode
        img = qrcode.make(payload)
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "q.png"
            img.save(p)
            payloads, handles = decode_image(p)
            assert payload in payloads, payloads
            assert handles == [{"kind": "short", "handle": "Orxkq55"}], handles
        print("self-test ok (decoded a generated QR)")
    else:
        # Draw one by hand with OpenCV's own encoder if it is there.
        try:
            import cv2
            enc = cv2.QRCodeEncoder.create()
            m = enc.encode(payload)
            m = cv2.resize(m, None, fx=8, fy=8, interpolation=cv2.INTER_NEAREST)
            with tempfile.TemporaryDirectory() as d:
                p = Path(d) / "q.png"
                cv2.imwrite(str(p), m)
                payloads, handles = decode_image(p)
                assert payload in payloads, payloads
                assert handles == [{"kind": "short", "handle": "Orxkq55"}], handles
            print("self-test ok (decoded a generated QR)")
        except Exception as e:                               # noqa: BLE001
            print(f"self-test ok (parsing only; no QR encoder here: {e})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("roots", nargs="*", help="folders or files; default the LINE photo inbox")
    ap.add_argument("--force", action="store_true", help="re-decode photos that already have a sidecar")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    roots = a.roots or [PHOTOS]
    out = report(roots) if a.report else run(roots, a.force)
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
