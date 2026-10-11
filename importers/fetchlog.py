#!/usr/bin/env python3
"""Verify-before-believe fetches with a ledger — the WO-25/WO-55 manners.

  fetch(job, key, url, expect)  → (record, text)
    snapshot-first into cache/lens/<job>/<key>.html; the page counts as the
    institution's own only when its text carries one of `expect` (ok=True);
    every attempt — reachable or not — is appended to cache/lens/<job>/
    manifest.json with url · fetched · ok · note, so the note can print the
    attempts instead of a guess.
  text(html)   → visible text, scripts and styles stripped, whitespace folded
  grep(text, pattern, n, w) → up to n context snippets around matches

Stdlib only; a pause between fetches; an identified User-Agent; the path
percent-encoded so a Thai URL does not crash the run (the WO-54 lesson).
"""
import datetime
import html as _html
import json
import re
import ssl
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UA = "Mozilla/5.0 (mot-dang reader; +https://motdang.net)"
PAUSE = 1.0
_CTX = ssl.create_default_context()
_CTX.check_hostname = False
_CTX.verify_mode = ssl.CERT_NONE


def text(raw):
    s = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", "", raw, flags=re.S)
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", _html.unescape(s)).strip()


def grep(t, pattern, n=6, w=150):
    out, seen = [], set()
    for m in re.finditer(pattern, t, re.I):
        frag = t[max(0, m.start() - w):m.end() + w]
        k = frag[w - 40:w + 40]
        if any(k[:30] in s for s in seen):
            continue
        seen.add(k)
        out.append(frag)
        if len(out) >= n:
            break
    return out


def _safe(url):
    sp = urllib.parse.urlsplit(url)
    return urllib.parse.urlunsplit((sp.scheme, sp.netloc, urllib.parse.quote(sp.path, safe="/%"),
                                    urllib.parse.quote(sp.query, safe="=&%"), ""))


def fetch(job, key, url, expect, refresh=False):
    d = ROOT / "cache" / "lens" / job
    d.mkdir(parents=True, exist_ok=True)
    mf = d / "manifest.json"
    man = json.loads(mf.read_text(encoding="utf-8")) if mf.exists() else {"entries": []}
    f = d / f"{key}.html"
    rec = {"key": key, "url": url, "fetched": datetime.date.today().isoformat()}
    if f.exists() and not refresh:
        raw = f.read_text(encoding="utf-8", errors="ignore")
        t = text(raw)
        rec.update(ok=any(e.lower() in t.lower() for e in expect), note="cached", file=str(f.relative_to(ROOT)))
        return rec, t
    try:
        req = urllib.request.Request(_safe(url), headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=30, context=_CTX) as r:
            body = r.read(3_000_000)
            final = r.geturl()
        raw = body.decode("utf-8", "ignore")
        f.write_bytes(body)
        t = text(raw)
        ok = any(e.lower() in t.lower() for e in expect)
        title = re.search(r"<title[^>]*>(.*?)</title>", raw, re.S | re.I)
        rec.update(ok=ok, final=final, bytes=len(body),
                   title=(_html.unescape(re.sub(r"\s+", " ", title.group(1))).strip()[:100] if title else ""),
                   file=str(f.relative_to(ROOT)),
                   note="VERIFIED" if ok else "fetched but expected name NOT found — not read as the institution")
    except Exception as e:  # noqa: BLE001 — printed, not swallowed
        rec.update(ok=False, note=f"unreachable ({type(e).__name__}: {str(e)[:80]})")
        t = ""
    man["entries"] = [e for e in man["entries"] if e.get("key") != key] + [rec]
    man["run"] = datetime.datetime.now().isoformat(timespec="seconds")
    mf.write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
    time.sleep(PAUSE)
    return rec, t


def run(job, targets, pattern, n=6, w=150):
    """Fetch a list of (key, url, expect[, pattern]) and print the snippets."""
    for item in targets:
        key, url, expect = item[0], item[1], item[2]
        pat = item[3] if len(item) > 3 else pattern
        rec, t = fetch(job, key, url, expect)
        print(f"\n### {key} · {rec.get('note')} · {len(t)} chars · {url}")
        if not t:
            continue
        for frag in grep(t, pat, n, w):
            print("   …" + frag + "…")
