#!/usr/bin/env python3
"""Bring what the LINE bot caught in the team group down to the desk.

    python3 importers/pull_line.py              # fetch, file, acknowledge
    python3 importers/pull_line.py --dry-run    # show what is waiting, take nothing

The Worker (motdang-line) keeps what arrives because a Worker is always up and
this Mac is not; LINE drops photo bytes after a while, so catching them is its
job, not ours. Nothing is deleted up there on a pull — /desk/ack only stamps a
row — so a run that dies halfway repeats itself instead of losing a photo.

Everything lands under _incoming/line/:

    chat/<date>.jsonl                             EVERY message, in order
    photos/<date>/<place-slug>/<message-id>.jpg   filed against a record
    photos/<date>/_unfiled/<message-id>.jpg       nobody named it yet
    photos/.../<message-id>.json                  who sent it, when, what they said
    photos/.../<message-id>.jpg.qr.json           the LINE QR on the sign, decoded
    bugs.jsonl + BUGS.txt                         Michael's reports, numbered
    _drive-queue.txt                              new files not yet copied to Drive
    thoughts/<date>.jsonl                         Nan's private room, every message
    thoughts/media/<date>/<message-id>.<ext>      its photos, files and voice notes
    thoughts/media/.../<message-id>.json          who sent it, when, from which room

Three rooms reach the Worker (motdang-line, 2026-09-30), and every row says
which in `channel`: "ops" (the operations room), "bots" (the team talking to
the bots) and "thoughts" (Nan's private room with a silent bot). ops and bots
are the team's and land as they always did, each transcript line and sidecar
carrying its channel. thoughts is private and goes only under thoughts/: never
into chat/, photos/, the bug list or the Drive queue, and the QR pass does not
read it. A row from a Worker older than the channel column is ops.

The sidecar is the provenance: a photo with no record of who stood where and
said what is a photo we cannot use. Nothing is pre-filtered out — a photo the
bot could not place is still pulled, still kept, and shows up in _unfiled.

Two coordinate fields, and they are not interchangeable. `gps` is somewhere a
person stood: a location shared from the paperclip, or EXIF off a picture sent
as a file. `pin_candidate` is somewhere we REASONED to, by resolving the other
shop signs standing in the same frame against the catalogue (resolve_frame.py)
— it exists because LINE strips EXIF from photo sends and no amount of asking
people to send files differently is a fix. It carries its own confidence, the
anchors that agreed, and a stated uncertainty, and it is null far more often
than not. A candidate never overwrites `gps` and never becomes a record's pin
on its own; promoting it is a person's step, like every other row here.

The transcript is new as of 2026-09-07, when Nan made this an ops channel:
"if it's in the channel it's because it's an action item for motdang." A line
about a shop's opening time is a fact about a record and a line about Beer's
hours is not, and nothing in the plumbing can tell those apart — so the
plumbing carries every line down and the desk, which can read, decides.
"""
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

from exif_gps import gps

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from resolve_frame import FrameResolver
except ImportError:  # the desk still runs without the resolver
    FrameResolver = None
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "_incoming", "line")
DESK = os.environ.get("LINE_DESK", "https://line.motdang.net")
TOKEN_FILE = os.path.expanduser("~/.motdang-line-pull-token")
UA = "motdang-desk/1.0 (+https://motdang.net)"
DRY = "--dry-run" in sys.argv


def token():
    t = os.environ.get("PULL_TOKEN", "").strip()
    if not t and os.path.exists(TOKEN_FILE):
        t = open(TOKEN_FILE).read().strip()
    if not t:
        raise SystemExit(
            f"No desk token. deploy.sh makes one at {TOKEN_FILE}; it is the\n"
            f"PULL_TOKEN secret on the Worker. Without it the desk cannot prove itself.")
    return t


def call(path, method="GET", body=None):
    req = urllib.request.Request(
        DESK + path, data=body, method=method,
        headers={"Authorization": "Bearer " + token(),
                 # Cloudflare's bot rules on the zone answer the default
                 # Python-urllib agent with 403/1010 before the Worker sees the
                 # request, so the desk says who it is. Named, not disguised.
                 "User-Agent": UA,
                 **({"Content-Type": "application/json"} if body else {})})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()
    except (urllib.error.URLError, OSError) as e:
        raise SystemExit(f"Cannot reach the desk at {DESK}: {e}")


def day(ms):
    return time.strftime("%Y-%m-%d", time.localtime((ms or 0) / 1000))


def stamp(ms):
    return time.strftime("%Y-%m-%d %H:%M", time.localtime((ms or 0) / 1000))


_RESOLVER = [None]  # built once per run, and only if a photo has anchors


def anchors_of(row, sign):
    """The signs standing in one frame, as anchors the resolver can vote on.

    Two sources, in order of how much they can be trusted:

      row["anchors"]  the Worker's own reading, already split into subject and
                      background with a role on each. This is the shape that
                      makes the resolver work, because the BACKGROUND is what
                      pins the photo — a reading that returns only the subject
                      has thrown the coordinates away.
      sign            the flat {name_th, name_en, other_text} reading. Its
                      names are the subject; other_text is whatever else was
                      legible, so it enters as neighbours.

    Nothing is derived from what a person typed. A caption is prose, and a
    resolver that guesses anchors out of prose is how "This is" became a
    record. What people say is read by the desk, which can read.
    """
    explicit = row.get("anchors")
    if isinstance(explicit, str):
        try:
            explicit = json.loads(explicit)
        except (TypeError, ValueError):
            explicit = None
    if isinstance(explicit, list) and explicit:
        return [a for a in explicit if isinstance(a, dict) and a.get("text")]

    if not sign:
        return []
    out = []
    for k in ("name_en", "name_th"):
        if sign.get(k):
            out.append({"text": sign[k], "role": "subject"})
            break
    other = sign.get("other_text")
    if isinstance(other, str):
        other = [other]
    for t in (other or []):
        if t:
            out.append({"text": t, "role": "neighbour"})
    return out


def resolve_pin(anchors):
    """Best-effort. A photo is never lost because the resolver had a bad day."""
    if not anchors or FrameResolver is None:
        return None
    try:
        if _RESOLVER[0] is None:
            index = os.path.join(ROOT, "docs", "data", "index.json")
            if not os.path.exists(index):
                # A build rewrites this file in place; missing is transient.
                return None
            _RESOLVER[0] = FrameResolver(index)
        out = _RESOLVER[0].resolve(anchors)
    except Exception as e:  # noqa: BLE001 — never let this cost us a photo
        return {"resolved": False, "reason": f"resolver failed: {e}"}
    return out


def queue_for_drive(paths):
    if not paths:
        return
    with open(os.path.join(OUT, "_drive-queue.txt"), "a", encoding="utf-8") as f:
        for p in paths:
            f.write(p + "\n")


def channel(r):
    return r.get("channel") or "ops"


def append_new(path, recs):
    """Append records whose message_id the file does not already hold.
    An unacked batch comes back verbatim on the next run (by design: better a
    repeat than a lost photo), so a file that did not refuse repeats would
    double each time."""
    held = set()
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            for line in f:
                try:
                    mid = json.loads(line).get("message_id")
                except ValueError:
                    continue
                if mid:
                    held.add(mid)
    recs = [x for x in recs if x.get("message_id") not in held]
    if recs:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            for x in recs:
                f.write(json.dumps(x, ensure_ascii=False) + "\n")
    return len(recs)


def line_of(r):
    return {
        "at": stamp(r["ts"]),
        "who": r.get("user_name") or r.get("user_id"),
        "channel": channel(r),
        "kind": r["kind"],
        "said": r.get("text"),
        "ticket": r.get("ticket"),
        "photo": r.get("photo_key"),
        "place_slug": r.get("place_slug"),
        "lat": r.get("lat"), "lng": r.get("lng"), "address": r.get("address"),
        "sign": r.get("sign"),
        "message_id": r.get("message_id"),
        "quoted": r.get("quoted_id"),
    }


def pull_thoughts(rows, took):
    """Nan's private room. Its own folder, its own transcript, nothing shared."""
    base_dir = os.path.join(OUT, "thoughts")
    media = 0
    for r in rows:
        key = r.get("photo_key")
        if not key:
            continue
        st, blob = call("/desk/photo?key=" + urllib.parse.quote(key, safe=""))
        if st != 200:
            print(f"  ! {key}: desk said {st} — leaving it for the next run")
            continue
        folder = os.path.join(base_dir, "media", day(r["ts"]))
        os.makedirs(folder, exist_ok=True)
        ext = os.path.splitext(key)[1] or ".bin"
        path = os.path.join(folder, (r.get("message_id") or str(r["id"])) + ext)
        with open(path, "wb") as f:
            f.write(blob)
        where = gps(blob) if ext.lower() in (".jpg", ".jpeg", ".png", ".heic", ".tif", ".tiff", ".webp") else None
        shared = (r.get("lat"), r.get("lng")) if r.get("lat") is not None else None
        side = {
            "message_id": r.get("message_id"),
            "sent_at": stamp(r["ts"]),
            "sent_at_ms": r["ts"],
            "sender": r.get("user_name"),
            "sender_id": r.get("user_id"),
            "group_id": r.get("group_id"),
            "channel": "thoughts",
            "said": r.get("text"),
            "sent_as": r.get("via") or "photo",
            "gps": ({"lat": shared[0], "lng": shared[1], "from": "line-location"} if shared
                    else {"lat": where[0], "lng": where[1], "from": "exif"} if where else None),
            "source": {"type": "private", "ref": "line-thoughts", "via": "motdang-line",
                       "r2_key": key, "fetched": time.strftime("%Y-%m-%d")},
        }
        with open(os.path.splitext(path)[0] + ".json", "w", encoding="utf-8") as f:
            json.dump(side, f, ensure_ascii=False, indent=2)
        media += 1
        print(f"  ← {os.path.relpath(path, ROOT)}")
    # Rows whose bytes did not come down stay unacked, so they come back.
    fetched = {r["id"] for r in rows if not r.get("photo_key")}
    fetched |= {r["id"] for r in rows if r.get("photo_key") and os.path.exists(os.path.join(
        base_dir, "media", day(r["ts"]),
        (r.get("message_id") or str(r["id"])) + (os.path.splitext(r["photo_key"])[1] or ".bin")))}
    by_day = {}
    for r in sorted(rows, key=lambda r: r["ts"]):
        if r["id"] in fetched:
            by_day.setdefault(day(r["ts"]), []).append(r)
    for d, group in by_day.items():
        n = append_new(os.path.join(base_dir, d + ".jsonl"), [line_of(r) for r in group])
        if n:
            print(f"  ← _incoming/line/thoughts/{d}.jsonl  (+{n})")
    took.extend(sorted(fetched))
    return media


def main():
    status, raw = call("/desk/pull?limit=300")
    if status != 200:
        raise SystemExit(f"desk said {status}: {raw[:300].decode('utf-8', 'replace')}")
    rows = json.loads(raw)["rows"]
    if not rows:
        print("nothing waiting.")
        return
    thoughts = [r for r in rows if channel(r) == "thoughts"]
    rows = [r for r in rows if channel(r) != "thoughts"]

    photos = [r for r in rows if r["kind"] in ("photo", "file") and r.get("photo_key")]
    bugs = [r for r in rows if r["kind"] == "bug"]
    said = [r for r in rows if r["kind"] == "text"]
    pins = [r for r in rows if r["kind"] == "location"]
    bots = sum(1 for r in rows if channel(r) == "bots")
    print(f"{len(photos)} photo(s), {len(bugs)} bug report(s), {len(said)} message(s), "
          f"{len(pins)} location(s) waiting ({bots} of them from the bots room); "
          f"{len(thoughts)} private thought(s).")
    if DRY:
        for r in rows + thoughts:
            who = r.get("user_name") or r.get("user_id") or "?"
            what = ("(private)" if channel(r) == "thoughts"
                    else r.get("place_name") or r.get("ticket") or "(unfiled)")
            print(f"  {stamp(r['ts'])}  {channel(r):<8}  {r['kind']:<8}  {who:<12}  {what}")
        return

    took, queued = [], []
    thought_media = pull_thoughts(thoughts, took) if thoughts else 0

    for r in photos:
        key = r.get("photo_key")
        if not key:
            continue
        st, blob = call("/desk/photo?key=" + urllib.parse.quote(key, safe=""))
        if st != 200:
            print(f"  ! {key}: desk said {st} — leaving it for the next run")
            continue
        slug = r.get("place_slug") or "_unfiled"
        folder = os.path.join(OUT, "photos", day(r["ts"]), slug)
        os.makedirs(folder, exist_ok=True)
        ext = os.path.splitext(key)[1] or ".jpg"
        base = os.path.join(folder, (r.get("message_id") or str(r["id"])) + ext)
        with open(base, "wb") as f:
            f.write(blob)
        # Where it was taken, if the bytes still say. A picture sent as a LINE
        # *photo* has been re-encoded and has nothing left to read; one sent
        # through the paperclip as a *file* keeps its EXIF. Either way the
        # answer goes in the sidecar as it is — None is a fact, not a gap to
        # fill, and a photo without coordinates must never be given any.
        where = gps(blob)
        # A location somebody shared from the shop is exact and survives however
        # the photo was sent; EXIF is the fallback for pictures sent as files.
        shared = (r.get("lat"), r.get("lng")) if r.get("lat") is not None else None
        sign = None
        if r.get("sign"):
            try:
                sign = json.loads(r["sign"])
            except (TypeError, ValueError):
                sign = None
        side = {
            "message_id": r.get("message_id"),
            "sent_at": stamp(r["ts"]),
            "sent_at_ms": r["ts"],
            "sender": r.get("user_name"),
            "sender_id": r.get("user_id"),
            "group_id": r.get("group_id"),
            "channel": channel(r),
            "said": r.get("text"),
            "place_slug": r.get("place_slug"),
            "place_name": r.get("place_name"),
            "confidence": r.get("confidence"),
            "status": r.get("status"),
            "sent_as": r.get("via") or "photo",
            "gps": ({"lat": shared[0], "lng": shared[1], "from": "line-location"} if shared
                    else {"lat": where[0], "lng": where[1], "from": "exif"} if where else None),
            "sign": sign,  # what a vision model read off the picture — a reading, not a fact
            # Where the FRAME says it stands, from the neighbouring signs in
            # the same picture. A candidate, never the pin: `gps` above is the
            # only field that carries a coordinate somebody actually stood on,
            # and a computed pin must never be mistaken for a surveyed one or
            # promoted over one. Null when the frame did not settle it, which
            # is most of the time and is the point.
            "pin_candidate": resolve_pin(anchors_of(r, sign)),
            "source": {"type": "field", "ref": "line-" + channel(r), "via": "motdang-line",
                       "r2_key": key, "fetched": time.strftime("%Y-%m-%d")},
        }
        with open(os.path.splitext(base)[0] + ".json", "w", encoding="utf-8") as f:
            json.dump(side, f, ensure_ascii=False, indent=2)
        took.append(r["id"])
        queued.append(base)
        pin = shared or where
        where_note = f"  📍 {pin[0]},{pin[1]}" if pin else ""
        # A frame-resolved pin prints differently from a surveyed one on
        # purpose. 📍 is somewhere a person stood; 🧭 is somewhere we reasoned
        # to, and the reader should never have to guess which they are looking
        # at. When both exist the 📍 stays first and the 🧭 is a cross-check.
        cand = side["pin_candidate"]
        if cand and cand.get("resolved"):
            where_note += (f"  🧭 {cand['pin'][0]},{cand['pin'][1]}"
                           f" ±{cand['uncertainty_m']:.0f} m"
                           f" ({cand['precision']}, {cand['anchors_agreeing']} anchors)")
        if sign and (sign.get("name_th") or sign.get("name_en")):
            where_note += f"  🪧 {sign.get('name_th') or sign.get('name_en')}"
        print(f"  ← {os.path.relpath(base, ROOT)}{where_note}")

    if bugs:
        with open(os.path.join(OUT, "bugs.jsonl"), "a", encoding="utf-8") as jf, \
             open(os.path.join(OUT, "BUGS.txt"), "a", encoding="utf-8") as tf:
            for r in bugs:
                jf.write(json.dumps({
                    "ticket": r.get("ticket"), "at": stamp(r["ts"]), "channel": channel(r),
                    "from": r.get("user_name"), "text": r.get("text"),
                    "message_id": r.get("message_id"),
                }, ensure_ascii=False) + "\n")
                tf.write(f"{r.get('ticket')}  {stamp(r['ts'])}  {r.get('user_name') or '?'}\n"
                         f"    {r.get('text')}\n\n")
                took.append(r["id"])
                print(f"  ← {r.get('ticket')}  {(r.get('text') or '')[:60]}")

    # The transcript: every line, in the order it was said, one file a day.
    # Photos and bugs appear here too — the desk needs to see a message in
    # the run of talk around it, not as a row torn out of the conversation.
    if rows:
        os.makedirs(os.path.join(OUT, "chat"), exist_ok=True)
        by_day = {}
        for r in sorted(rows, key=lambda r: r["ts"]):
            by_day.setdefault(day(r["ts"]), []).append(r)
        for d, group in by_day.items():
            n = append_new(os.path.join(OUT, "chat", d + ".jsonl"), [line_of(r) for r in group])
            if not n:
                continue
            print(f"  ← _incoming/line/chat/{d}.jsonl  (+{n})")
        took.extend(r["id"] for r in said)
        took.extend(r["id"] for r in pins)

    queue_for_drive(queued)

    # D1 allows 100 bound parameters per statement and the Worker's ack spends
    # one on the timestamp, so a full 100-row page asked for 101 and threw
    # (Cloudflare 1101) — every row stayed unacked and the same page came back
    # forever. Chunk it; the Worker is correct for any batch of 99 or fewer.
    for i in range(0, len(took), 50):
        batch = took[i:i + 50]
        st, raw = call("/desk/ack", "POST", json.dumps({"ids": batch}).encode())
        # The Worker has answered a good ack with an empty body; a crash here
        # left every row unacked, so the same batch came back every run and the
        # backlog never drained past one page. Status is the truth, not the body.
        try:
            acked = json.loads(raw).get("acked", 0)
        except (ValueError, AttributeError):
            acked = len(batch) if st in (200, 204) else 0
        if st not in (200, 204):
            print(f"ack FAILED: HTTP {st} {raw[:200]!r} — {len(batch)} row(s) "
                  f"not drained, they will come back next run")
        else:
            print(f"acknowledged {acked} of {len(batch)}")
    # The QR beside the shop's name on the sign. Read here rather than in the
    # Worker: no deploy, no CPU budget, and it can be re-run over photos
    # already pulled. Never allowed to fail the pull — a decoder that throws
    # costs the handles from this run and nothing else.
    qr = {}
    try:
        from decode_line_qr import run as decode_run
        qr = decode_run([os.path.join(OUT, "photos")])
        if qr.get("handles"):
            print(f"  LINE handles off the signs: {qr['handles']} "
                  f"({qr.get('newToSeeds', 0)} new) → cache/line_oa_seeds.json")
    except Exception as e:
        print(f"  qr decode skipped: {e}")

    with open(os.path.join(OUT, "pull.log"), "a", encoding="utf-8") as f:
        f.write(f"{time.strftime('%Y-%m-%d %H:%M')}  photos={len(queued)} bugs={len(bugs)} "
                f"messages={len(said)} thoughts={len(thoughts)} thought_media={thought_media} "
                f"qr={qr.get('handles', 0)}\n")


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    main()
