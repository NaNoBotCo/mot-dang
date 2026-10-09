#!/usr/bin/env python3
"""Carry the queued LINE photos up to Drive, streaming the bytes off disk.

    python3 importers/push_drive.py                  # drain _incoming/line/_drive-queue.txt
    python3 importers/push_drive.py --dry-run        # show the plan, send nothing
    python3 importers/push_drive.py --check          # credential, folder, queue
    python3 importers/push_drive.py --install-key <downloaded.json>
    python3 importers/push_drive.py --auth           # the OAuth route instead

Why this exists. STEP 3 of the desk hands each photo to the Drive MCP tool,
which takes the file as base64 in a tool parameter — so the whole encoded image
has to pass through the model first. The smallest queued photo is 90 KB of
base64 and the shell truncates output well below that, which is why ten .jpg
files sat in the queue from 7 Sept while their .json sidecars went up fine.
This talks to Drive v3 directly: the bytes go from the file to the socket in
256 KiB chunks and no model sees them.

THE CREDENTIAL. Read from ~/.config/nanobotco/keys.json under "google_drive",
alongside the other fleet keys, and never from the repo. Two shapes work.

A service account (fewer steps, and it does not expire):

    "google_drive": {
      "kind": "service_account",
      "service_account": { ...the JSON Google downloads... },
      "folder_id": "1BfHdRJdGlNG8XHscHIAdi4InN2eRSoe6"
    }

  --install-key writes that block for you from the downloaded file. The folder
  has to be shared with the service account's own address, which --check prints.

An OAuth desktop client, if the account cannot make service accounts:

    "google_drive": {
      "kind": "oauth",
      "client_id": "....apps.googleusercontent.com",
      "client_secret": "...",
      "refresh_token": "...",        # --auth writes this
      "folder_id": "1BfHdRJdGlNG8XHscHIAdi4InN2eRSoe6"
    }

  Google expires the refresh token after seven days while the consent screen
  sits in Testing, so an hourly task on this route needs the screen published.

The scope defaults to drive.file, which reaches files this credential created.
The ten sidecars already up there were put up by a different client, so this
one may not see them in a listing; the local ledger below covers that. Setting
"scope": "https://www.googleapis.com/auth/drive" in the same block widens it.

TITLES match what the desk already writes: "<place-slug> — <message-id>.jpg",
or "unfiled — ..." for a photo nobody placed, and the sidecar beside it under
the same name with .json. A title already in the folder, or already in
_incoming/line/_drive-uploaded.tsv, is skipped — the ledger is seeded with the
ten sidecars of 7 and 19 Sept. --recheck ignores the ledger and trusts the
folder listing alone.

THE QUEUE. A line goes only after Drive returns an id for that file and for its
sidecar; a failure stays where it is for the next run. The rewrite re-reads the
file under a lock and removes the lines it finished, so a photo pull_line.py
appends while an upload is in flight survives. This lock is its own file and
has nothing to do with the build lock.

Writes nothing into data/, runs no build.
"""
import argparse
import base64
import fcntl
import json
import os
import random
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LINE = os.path.join(ROOT, "_incoming", "line")
QUEUE = os.path.join(LINE, "_drive-queue.txt")
LEDGER = os.path.join(LINE, "_drive-uploaded.tsv")
KEYS = os.path.expanduser("~/.config/nanobotco/keys.json")

FOLDER_ID = "1BfHdRJdGlNG8XHscHIAdi4InN2eRSoe6"
FOLDER_NAME = "Mot Dang — photos from LINE"
SCOPE = "https://www.googleapis.com/auth/drive.file"
TOKEN_URL = "https://oauth2.googleapis.com/token"
AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
API = "https://www.googleapis.com/drive/v3"
UPLOAD = "https://www.googleapis.com/upload/drive/v3/files"
CHUNK = 256 * 1024 * 16  # 4 MiB, a multiple of Drive's 256 KiB unit
DASHES = {"—": "-", "–": "-", "−": "-"}

MIME = {
    ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
    ".heic": "image/heic", ".json": "application/json", ".txt": "text/plain",
}

# Put up by the desk's MCP tool on 7 and 19 Sept, before this script existed.
# Recorded so a credential that cannot see them does not send them twice.
SEEDED_SIDECARS = [
    "630725814551839248", "630726753068778023", "630732167076905233",
    "630834503648805225", "631422317637402778", "631422318979580466",
    "631422319986475384", "631422321412276633", "631440441862521089",
    "631693100242698530",
]


# ---------------------------------------------------------------- small stuff

def norm(title):
    """Compare titles across dash styles and stray spacing."""
    t = title.strip().lower()
    for a, b in DASHES.items():
        t = t.replace(a, b)
    return " ".join(t.split())


def stem_of(path):
    return os.path.splitext(os.path.basename(path))[0]


def slug_of(path):
    slug = os.path.basename(os.path.dirname(path))
    if slug.startswith("_"):
        slug = slug[1:]
    return slug or "unfiled"


def title_for(path):
    return "%s — %s" % (slug_of(path), os.path.basename(path))


def mime_for(path):
    return MIME.get(os.path.splitext(path)[1].lower(), "application/octet-stream")


def sidecar_for(path):
    """The provenance file the bot wrote beside the photo, or None."""
    if path.lower().endswith(".json"):
        return None
    side = os.path.join(os.path.dirname(path), stem_of(path) + ".json")
    return side if os.path.exists(side) else None


def resolve(line):
    """Queue lines carry absolute paths; ~/Desktop and ~/Developer are the same
    tree through a symlink, and either spelling may be in the file."""
    p = line.strip()
    if not p:
        return None
    if os.path.exists(p):
        return p
    marker = os.sep + os.path.join("_incoming", "line") + os.sep
    i = p.find(marker)
    if i != -1:
        alt = os.path.join(LINE, p[i + len(marker):])
        if os.path.exists(alt):
            return alt
    return None


# -------------------------------------------------------------------- ledger

def ledger_titles():
    """The seeded sidecars count whether or not the file has been written yet."""
    seen = {norm("unfiled — %s.json" % m) for m in SEEDED_SIDECARS}
    if not os.path.exists(LEDGER):
        return seen
    with open(LEDGER, encoding="utf-8") as f:
        for row in f:
            if row.startswith("#") or not row.strip():
                continue
            seen.add(norm(row.split("\t")[0]))
    return seen


def ledger_seed():
    if os.path.exists(LEDGER):
        return
    with open(LEDGER, "w", encoding="utf-8") as f:
        f.write("# title\tdrive_id\tlocal_path\tuploaded\n")
        f.write("# the .json rows below went up through the desk's MCP tool on "
                "7 and 19 Sept 2026; their Drive ids were not recorded.\n")
        for mid in SEEDED_SIDECARS:
            f.write("unfiled — %s.json\t-\t-\tmcp-desk\n" % mid)


def ledger_add(title, file_id, path):
    with open(LEDGER, "a", encoding="utf-8") as f:
        f.write("%s\t%s\t%s\t%s\n"
                % (title, file_id, path, time.strftime("%Y-%m-%d %H:%M")))


# --------------------------------------------------------------- credentials

def load_keys():
    with open(KEYS, encoding="utf-8") as f:
        return json.load(f)


def save_keys(keys):
    d = os.path.dirname(KEYS)
    fd, tmp = tempfile.mkstemp(dir=d)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(keys, f, indent=2, ensure_ascii=False)
        f.write("\n")
    os.chmod(tmp, 0o600)
    os.replace(tmp, KEYS)


def cred():
    if not os.path.exists(KEYS):
        return None
    block = load_keys().get("google_drive")
    if not isinstance(block, dict):
        return None
    kind = block.get("kind")
    if kind == "service_account" and block.get("service_account"):
        return block
    if kind == "oauth" and block.get("refresh_token"):
        return block
    return block if block.get("client_id") or block.get("service_account") else None


def sign_rs256(pem, message):
    try:
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import padding
        k = serialization.load_pem_private_key(pem.encode("utf-8"), password=None)
        return k.sign(message, padding.PKCS1v15(), hashes.SHA256())
    except ImportError:
        pass
    fd, tmp = tempfile.mkstemp()
    try:
        with os.fdopen(fd, "w") as f:
            f.write(pem)
        out = subprocess.run(
            ["openssl", "dgst", "-sha256", "-sign", tmp],
            input=message, stdout=subprocess.PIPE, check=True)
        return out.stdout
    finally:
        os.unlink(tmp)


def b64url(raw):
    return base64.urlsafe_b64encode(raw).rstrip(b"=")


def post_form(url, fields):
    body = urllib.parse.urlencode(fields).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    with urllib.request.urlopen(req, timeout=45) as r:
        return json.loads(r.read().decode("utf-8"))


def access_token(block):
    scope = block.get("scope") or SCOPE
    if block.get("kind") == "service_account":
        sa = block["service_account"]
        now = int(time.time())
        head = b64url(json.dumps({"alg": "RS256", "typ": "JWT"}).encode())
        claim = {
            "iss": sa["client_email"], "scope": scope,
            "aud": TOKEN_URL, "iat": now, "exp": now + 3600,
        }
        if sa.get("subject"):
            claim["sub"] = sa["subject"]
        body = head + b"." + b64url(json.dumps(claim).encode())
        jwt = body + b"." + b64url(sign_rs256(sa["private_key"], body))
        got = post_form(TOKEN_URL, {
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "assertion": jwt.decode("ascii"),
        })
    else:
        got = post_form(TOKEN_URL, {
            "grant_type": "refresh_token",
            "client_id": block["client_id"],
            "client_secret": block["client_secret"],
            "refresh_token": block["refresh_token"],
        })
    return got["access_token"]


# ------------------------------------------------------------------ drive io

def call(method, url, token, headers=None, body=None, timeout=90):
    """Returns (status, headers, bytes). HTTP errors come back, not raised."""
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Authorization", "Bearer " + token)
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, dict(r.headers), r.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read()


def retryable(status):
    return status == 429 or 500 <= status < 600


def backoff(attempt):
    time.sleep(min(30, (2 ** attempt)) + random.random())


def folder_titles(token, folder):
    """Every title the credential can see in the folder."""
    titles, page = set(), None
    while True:
        q = {
            "q": "'%s' in parents and trashed=false" % folder,
            "fields": "nextPageToken,files(id,name)",
            "pageSize": "1000",
            "supportsAllDrives": "true",
            "includeItemsFromAllDrives": "true",
        }
        if page:
            q["pageToken"] = page
        status, _, raw = call("GET", API + "/files?" + urllib.parse.urlencode(q), token)
        if status != 200:
            raise RuntimeError("listing the folder: %s %s"
                               % (status, raw[:300].decode("utf-8", "replace")))
        got = json.loads(raw.decode("utf-8"))
        for f in got.get("files", []):
            titles.add(norm(f["name"]))
        page = got.get("nextPageToken")
        if not page:
            return titles


def upload(token, path, title, folder, message_id):
    """Resumable upload, read off disk in chunks. Returns the Drive file id."""
    size = os.path.getsize(path)
    meta = {
        "name": title,
        "parents": [folder],
        "mimeType": mime_for(path),
        "appProperties": {
            "source": "motdang-line",
            "message_id": message_id,
            "local_path": path,
        },
    }
    session = None
    for attempt in range(5):
        status, headers, raw = call(
            "POST", UPLOAD + "?uploadType=resumable&supportsAllDrives=true", token,
            headers={
                "Content-Type": "application/json; charset=UTF-8",
                "X-Upload-Content-Type": meta["mimeType"],
                "X-Upload-Content-Length": str(size),
            },
            body=json.dumps(meta).encode("utf-8"))
        if status == 200 and headers.get("Location"):
            session = headers["Location"]
            break
        if not retryable(status):
            raise RuntimeError("opening the upload: %s %s"
                               % (status, raw[:300].decode("utf-8", "replace")))
        backoff(attempt)
    if not session:
        raise RuntimeError("opening the upload: gave up after 5 tries")

    sent, stalls = 0, 0
    with open(path, "rb") as fh:
        while True:
            fh.seek(sent)
            chunk = fh.read(CHUNK)
            if not chunk and size:
                raise RuntimeError("the file ended early at byte %d" % sent)
            rng = "bytes %d-%d/%d" % (sent, sent + len(chunk) - 1, size) if size \
                else "bytes */0"
            status, headers, raw = call(
                "PUT", session, token,
                headers={"Content-Length": str(len(chunk)), "Content-Range": rng},
                body=chunk, timeout=300)
            if status in (200, 201):
                return json.loads(raw.decode("utf-8"))["id"]
            if status == 308:
                rng = headers.get("Range")
                sent = int(rng.split("-")[1]) + 1 if rng else sent + len(chunk)
                stalls = 0
                continue
            if retryable(status):
                stalls += 1
                if stalls > 5:
                    raise RuntimeError("upload stalled at byte %d: %s" % (sent, status))
                backoff(stalls)
                # Ask Drive how much of it landed, then carry on from there.
                status, headers, raw = call(
                    "PUT", session, token,
                    headers={"Content-Length": "0",
                             "Content-Range": "bytes */%d" % size}, body=b"")
                if status in (200, 201):
                    return json.loads(raw.decode("utf-8"))["id"]
                rng = headers.get("Range")
                sent = int(rng.split("-")[1]) + 1 if rng else sent
                continue
            raise RuntimeError("uploading: %s %s"
                               % (status, raw[:300].decode("utf-8", "replace")))


# -------------------------------------------------------------------- queue

def queue_read():
    if not os.path.exists(QUEUE):
        return []
    with open(QUEUE, "r", encoding="utf-8") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            return f.read().splitlines()
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)


def queue_drop(done):
    """Re-read under the lock and take out only the lines that finished."""
    if not done or not os.path.exists(QUEUE):
        return
    done = set(done)
    with open(QUEUE, "r+", encoding="utf-8") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            keep = [ln for ln in f.read().splitlines()
                    if ln.strip() and ln not in done]
            f.seek(0)
            f.truncate()
            if keep:
                f.write("\n".join(keep) + "\n")
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)


# --------------------------------------------------------------------- flows

def install_key(path):
    with open(os.path.expanduser(path), encoding="utf-8") as f:
        sa = json.load(f)
    if sa.get("type") != "service_account" or "private_key" not in sa:
        raise SystemExit("that file is not a service account key — it has no "
                         "private_key. Download the JSON key from the service "
                         "account's Keys tab.")
    keys = load_keys() if os.path.exists(KEYS) else {}
    keys["google_drive"] = {
        "kind": "service_account",
        "service_account": sa,
        "folder_id": FOLDER_ID,
        "registered": time.strftime("%Y-%m-%d"),
        "note": "Drive uploads for the LINE desk (importers/push_drive.py). "
                "Share the folder with %s as Editor." % sa["client_email"],
    }
    save_keys(keys)
    print("stored under google_drive in %s" % KEYS)
    print("now share the Drive folder \"%s\" with, as Editor:" % FOLDER_NAME)
    print("    %s" % sa["client_email"])
    print("then: python3 importers/push_drive.py --check")


def auth():
    """The OAuth route: open the consent page, catch the code on loopback."""
    import http.server
    import webbrowser
    block = (load_keys().get("google_drive") if os.path.exists(KEYS) else None) or {}
    if not block.get("client_id") or not block.get("client_secret"):
        raise SystemExit(
            "put the desktop client's id and secret into %s first:\n"
            '  "google_drive": {"kind": "oauth", "client_id": "...", '
            '"client_secret": "...", "folder_id": "%s"}' % (KEYS, FOLDER_ID))
    caught = {}

    class Catch(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            caught.update({k: v[0] for k, v in q.items()})
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write("Done. Close this tab.".encode("utf-8"))

        def log_message(self, *a):
            pass

    srv = http.server.HTTPServer(("127.0.0.1", 0), Catch)
    redirect = "http://127.0.0.1:%d" % srv.server_port
    url = AUTH_URL + "?" + urllib.parse.urlencode({
        "client_id": block["client_id"], "redirect_uri": redirect,
        "response_type": "code", "scope": block.get("scope") or SCOPE,
        "access_type": "offline", "prompt": "consent",
    })
    print("approve it here, signed in as the account that owns the folder:")
    print(url)
    webbrowser.open(url)
    srv.handle_request()
    if "code" not in caught:
        raise SystemExit("Google sent back: %s" % caught)
    got = post_form(TOKEN_URL, {
        "grant_type": "authorization_code", "code": caught["code"],
        "client_id": block["client_id"], "client_secret": block["client_secret"],
        "redirect_uri": redirect,
    })
    if "refresh_token" not in got:
        raise SystemExit("no refresh token came back — revoke the app at "
                         "myaccount.google.com/permissions and run --auth again")
    keys = load_keys()
    block.update({"kind": "oauth", "refresh_token": got["refresh_token"],
                  "folder_id": block.get("folder_id") or FOLDER_ID,
                  "registered": time.strftime("%Y-%m-%d")})
    keys["google_drive"] = block
    save_keys(keys)
    print("refresh token stored under google_drive in %s" % KEYS)


def check():
    block = cred()
    queued = [ln for ln in queue_read() if ln.strip()]
    print("queue: %d line(s) in %s" % (len(queued), QUEUE))
    if not block:
        print("credential: none under google_drive in %s" % KEYS)
        print("see the setup in _incoming/line/_drive-queue.README.txt")
        return 2
    kind = block.get("kind", "?")
    who = block.get("service_account", {}).get("client_email", block.get("client_id", ""))
    print("credential: %s — %s" % (kind, who))
    token = access_token(block)
    print("token: ok, scope %s" % (block.get("scope") or SCOPE))
    folder = block.get("folder_id") or FOLDER_ID
    status, _, raw = call("GET", API + "/files/%s?fields=id,name&supportsAllDrives=true"
                          % folder, token)
    if status == 200:
        print("folder: %s" % json.loads(raw.decode("utf-8"))["name"])
    else:
        print("folder: metadata came back %s — the scope may not reach a folder "
              "this credential did not create; uploads into it can still work" % status)
    try:
        titles = folder_titles(token, folder)
        print("folder listing: %d file(s) visible" % len(titles))
        if not titles:
            print("  nothing visible. The ten sidecars are covered by the local "
                  "ledger. To see the folder's own contents, add "
                  '"scope": "https://www.googleapis.com/auth/drive" to the block.')
    except RuntimeError as e:
        print("folder listing: %s" % e)
    print("ledger: %d title(s) in %s" % (len(ledger_titles()), LEDGER))
    return 0


def run(dry, recheck, limit):
    if not dry:
        ledger_seed()
    raw_lines = queue_read()
    lines = [ln for ln in raw_lines if ln.strip()]
    if not lines:
        print("drive queue empty.")
        return 0

    block = cred()
    if not block and not dry:
        print("%d photo(s) held: no Google credential under google_drive in %s."
              % (len(lines), KEYS))
        print("setup is in %s" % os.path.join(LINE, "_drive-queue.README.txt"))
        return 2

    folder = (block or {}).get("folder_id") or FOLDER_ID
    known = set() if recheck else ledger_titles()
    token = None
    if block:
        token = access_token(block)
        try:
            known |= folder_titles(token, folder)
        except RuntimeError as e:
            print("could not list the folder (%s) — going by the ledger alone" % e)

    sent, skipped, missing, failed, done_lines = 0, 0, 0, 0, []
    seen_line = set()
    for line in lines:
        if limit and sent >= limit:
            break
        if line in seen_line:
            done_lines.append(line)
            continue
        seen_line.add(line)
        path = resolve(line)
        if not path:
            missing += 1
            print("missing on disk, left in the queue: %s" % line.strip())
            continue

        ok = True
        for target in [p for p in (path, sidecar_for(path)) if p]:
            title = title_for(target)
            if norm(title) in known:
                skipped += 1
                continue
            if dry:
                print("would send  %s   (%s, %d bytes)"
                      % (title, mime_for(target), os.path.getsize(target)))
                sent += 1
                known.add(norm(title))
                continue
            try:
                file_id = upload(token, target, title, folder, stem_of(target))
            except Exception as e:  # noqa: BLE001 — one bad file waits, the rest go
                ok = False
                failed += 1
                print("failed, left in the queue: %s — %s" % (title, e))
                break
            ledger_add(title, file_id, target)
            known.add(norm(title))
            sent += 1
            print("sent  %s  %s" % (file_id, title))
        if ok:
            done_lines.append(line)

    if not dry:
        queue_drop(done_lines)
    left = len([ln for ln in queue_read() if ln.strip()])
    print("%s %d file(s), skipped %d already up, %d failed, %d missing, "
          "%d line(s) left in the queue."
          % ("would send" if dry else "sent", sent, skipped, failed, missing, left))
    return 1 if failed else 0


def main():
    ap = argparse.ArgumentParser(
        description="Upload the queued LINE photos to Drive, off disk.")
    ap.add_argument("--dry-run", action="store_true",
                    help="show what would go up, send nothing")
    ap.add_argument("--check", action="store_true",
                    help="credential, folder and queue, then stop")
    ap.add_argument("--install-key", metavar="FILE",
                    help="store a downloaded service account JSON in keys.json")
    ap.add_argument("--auth", action="store_true",
                    help="run the OAuth consent flow and store the refresh token")
    ap.add_argument("--recheck", action="store_true",
                    help="ignore the local ledger; go by the folder listing")
    ap.add_argument("--limit", type=int, default=0, metavar="N",
                    help="stop after N files")
    a = ap.parse_args()
    if a.install_key:
        return install_key(a.install_key) or 0
    if a.auth:
        return auth() or 0
    if a.check:
        return check()
    return run(a.dry_run, a.recheck, a.limit)


if __name__ == "__main__":
    sys.exit(main() or 0)
