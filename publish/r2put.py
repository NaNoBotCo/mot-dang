#!/usr/bin/env python3
"""Upload docs/ to R2 over Cloudflare's REST API, using wrangler's own token.

    python3 publish/r2put.py --limit 60      # measure throughput on a sample
    python3 publish/r2put.py                 # upload everything changed
    python3 publish/r2put.py --prune         # also delete bucket keys no longer built

WHY NOT rclone
--------------
rclone talks S3, and R2's S3 endpoint needs an access key/secret pair that only
the dashboard issues. The REST API takes the OAuth token wrangler already holds
on this machine, so the whole site can go up without minting a new credential
or putting one on disk. The tradeoff is that this path shares the general
Cloudflare API rate limit, so it is slower per request — measured before use,
not assumed (--limit).

INCREMENTAL
-----------
build.py rewrites every file on every run, so timestamps say nothing. This
keeps a manifest of MD5 per key in publish/.uploaded.json and sends only what
actually differs. R2 returns the MD5 as the object etag for single-part uploads,
so the manifest can be rebuilt from the bucket if it is ever lost.
"""

import concurrent.futures as futures
import hashlib
import json
import pathlib
import re
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
MANIFEST = ROOT / "publish" / ".uploaded.json"
ACCOUNT = "fe332688b1b25b543f8429d7f08292a3"
BUCKET = "mot-dang-site"
API = "https://api.cloudflare.com/client/v4/accounts/%s/r2/buckets/%s/objects/" % (ACCOUNT, BUCKET)
FLOOR = 20000
WORKERS = 16

TYPES = {"html": "text/html; charset=utf-8", "json": "application/json; charset=utf-8",
         "geojson": "application/geo+json", "js": "text/javascript; charset=utf-8",
         "css": "text/css; charset=utf-8", "svg": "image/svg+xml", "png": "image/png",
         "jpg": "image/jpeg", "jpeg": "image/jpeg", "webp": "image/webp",
         "ico": "image/x-icon", "woff2": "font/woff2", "txt": "text/plain; charset=utf-8",
         "xml": "application/xml; charset=utf-8", "ics": "text/calendar; charset=utf-8",
         "pdf": "application/pdf", "pmtiles": "application/octet-stream",
         "apk": "application/vnd.android.package-archive"}


def token():
    for p in ("~/.wrangler/config/default.toml",
              "~/Library/Preferences/.wrangler/config/default.toml"):
        f = pathlib.Path(p).expanduser()
        if f.exists():
            m = re.search(r'oauth_token\s*=\s*"([^"]+)"', f.read_text())
            if m:
                return m.group(1)
    sys.exit("no wrangler token — run: npx wrangler login")


def ctype(key):
    return TYPES.get(key.rsplit(".", 1)[-1].lower(), "application/octet-stream")


class Counter:
    def __init__(self):
        self.n = self.fail = 0
        self.lock = threading.Lock()

    def tick(self, ok):
        with self.lock:
            if ok:
                self.n += 1
            else:
                self.fail += 1
            return self.n + self.fail


def put(tok, key, data, ct, counter, total, t0):
    url = API + urllib.parse.quote(key)
    for attempt in range(5):
        req = urllib.request.Request(url, data=data, method="PUT",
                                     headers={"Authorization": "Bearer " + tok,
                                              "Content-Type": ct})
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                r.read()
            done = counter.tick(True)
            if done % 250 == 0 or done == total:
                el = time.time() - t0
                print("  %6d/%d  %5.1f/s  %s" % (done, total, done / max(el, .001), key[:52]),
                      flush=True)
            return True
        except urllib.error.HTTPError as e:
            # 429 is the shared API rate limit; back off rather than hammer.
            if e.code in (429, 500, 502, 503, 504):
                time.sleep(2 ** attempt)
                continue
            counter.tick(False)
            print("  FAIL %s %s %s" % (key, e.code, e.read()[:120]), flush=True)
            return False
        except (urllib.error.URLError, TimeoutError, OSError):
            time.sleep(2 ** attempt)
    counter.tick(False)
    print("  FAIL %s (retries exhausted)" % key, flush=True)
    return False


def main():
    limit = 0
    if "--limit" in sys.argv:
        limit = int(sys.argv[sys.argv.index("--limit") + 1])

    if not DOCS.is_dir():
        sys.exit("no docs/ — run python3 build.py first")
    files = sorted(p for p in DOCS.rglob("*") if p.is_file())
    print("files in docs/: %s" % f"{len(files):,}")
    if len(files) < FLOOR and not limit:
        sys.exit("REFUSING: %s files, floor %s — that is a broken build."
                 % (f"{len(files):,}", f"{FLOOR:,}"))

    seen = {}
    if MANIFEST.exists():
        try:
            seen = json.loads(MANIFEST.read_text())
        except ValueError:
            seen = {}

    todo = []
    for p in files:
        key = p.relative_to(DOCS).as_posix()
        data = p.read_bytes()
        h = hashlib.md5(data).hexdigest()
        if seen.get(key) != h:
            todo.append((key, data, h))
    print("changed since last upload: %s" % f"{len(todo):,}")
    if limit:
        todo = todo[:limit]
        print("LIMITED to %d for measurement" % len(todo))
    if not todo:
        print("nothing to do")
        return

    tok = token()
    counter = Counter()
    t0 = time.time()
    done = {}
    with futures.ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = {ex.submit(put, tok, k, d, ctype(k), counter, len(todo), t0): (k, h)
                for k, d, h in todo}
        for f in futures.as_completed(futs):
            k, h = futs[f]
            if f.result():
                done[k] = h

    seen.update(done)
    MANIFEST.write_text(json.dumps(seen, separators=(",", ":")))
    el = time.time() - t0
    print("\nuploaded %s in %.0fs (%.1f/s), %d failed"
          % (f"{len(done):,}", el, len(done) / max(el, .001), counter.fail))
    if counter.fail:
        sys.exit("some uploads failed — rerun to retry just those")


if __name__ == "__main__":
    main()
