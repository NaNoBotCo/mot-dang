#!/usr/bin/env python3
"""embed.py — the meaning half of /find (Nan, 2026-10-04: "both").

/find matches words. This embeds every page it holds (title, abstract, the
breadcrumb) with bge-m3 into the Vectorize index `motdang-find`, so the Worker
can re-rank the word matches by meaning and answer when the words find
nothing: "somewhere quiet to work" reaches a café that only says wifi.

bge-m3 because wichaa measured it (manuscript-wiki/search_index.py): it is the
Workers AI model that puts a Thai term near its English gloss. The Worker
embeds the query with the same model; a different one returns plausible
nonsense rather than failing.

The pages come from the live D1 index (motdang-search), not docs/, so a
rebuild in progress does not matter. Vector ids are sha1(url), stable across
reloads (D1 row ids are not); a page whose text has not changed since the last
run is skipped (cache/fleetsearch/embedded.tsv).

    python3 fleetsearch/embed.py --dry-run      # show documents, embed nothing
    python3 fleetsearch/embed.py --limit 500    # a first slice
    python3 fleetsearch/embed.py                # everything, resumable
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import hashlib
import json
import pathlib
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request

ACCOUNT_ID = "fe332688b1b25b543f8429d7f08292a3"
INDEX = "motdang-find"
MODEL = "@cf/baai/bge-m3"
API = "https://api.cloudflare.com/client/v4"
DB = "motdang-search"
BATCH = 50          # texts per embed call (wichaa's size)
UPSERT = 500        # vectors per upsert
PAGE = 4000         # rows per D1 read
JOBS = 6

ROOT = pathlib.Path(__file__).resolve().parent.parent
PUBLISH = ROOT / "publish"
STATE = ROOT / "cache" / "fleetsearch" / "embedded.tsv"
CRAWLER = pathlib.Path.home() / "Developer" / "claude code projects" / "manuscript-crawler"

# The site's own name rides on every title; it says nothing about the page.
CHROME = re.compile(r"\s*·\s*(มดแดง Mot Dang|มดแดง|Mot Dang|wichaa)\s*$")


def token(force_refresh: bool = False) -> str:
    sys.path.insert(0, str(CRAWLER))
    from crawler import cfauth
    return cfauth.token(force_refresh=force_refresh)


def d1(sql: str) -> list[dict]:
    out = subprocess.run(["npx", "wrangler", "d1", "execute", DB, "--remote", "--json", "--command", sql],
                         cwd=PUBLISH, capture_output=True, text=True, timeout=300)
    if out.returncode:
        raise RuntimeError(out.stderr[-600:])
    return json.loads(out.stdout)[0]["results"]


def pages(limit: int | None) -> list[dict]:
    top = d1("SELECT max(id) AS mx FROM pages")[0]["mx"] or 0
    rows: list[dict] = []
    for lo in range(0, top, PAGE):
        rows += d1(f"SELECT id, site, url, title, abstract, crumbs FROM pages "
                   f"WHERE id > {lo} AND id <= {lo + PAGE} ORDER BY id")
        print(f"  read {len(rows)}/{top}", flush=True)
        if limit and len(rows) >= limit:
            return rows[:limit]
    return rows


def document(r: dict) -> dict:
    title = CHROME.sub("", r["title"] or "").strip()
    crumbs = ""
    try:
        crumbs = " › ".join(c[0] for c in json.loads(r["crumbs"] or "[]") if c and c[0])
    except (ValueError, TypeError, IndexError):
        pass
    abstract = (r["abstract"] or "").strip()
    if abstract.startswith(title):
        abstract = abstract[len(title):].strip()
    text = " — ".join(x for x in (title, crumbs, abstract[:480]) if x)
    return {
        "id": hashlib.sha1(r["url"].encode()).hexdigest(),
        "text": text,
        "h": hashlib.sha1(text.encode()).hexdigest()[:16],
        "meta": {"u": r["url"], "s": r["site"], "t": title[:160], "a": abstract[:200]},
    }


class QuotaExhausted(RuntimeError):
    pass


def post(url: str, body: bytes, ctype: str, tok: list[str]) -> dict:
    for attempt in range(6):
        try:
            req = urllib.request.Request(url, data=body, method="POST",
                                         headers={"Authorization": f"Bearer {tok[0]}", "Content-Type": ctype})
            with urllib.request.urlopen(req, timeout=180) as r:
                d = json.load(r)
            if not d.get("success"):
                raise RuntimeError(f"{d.get('errors')}")
            return d
        except urllib.error.HTTPError as e:
            detail = e.read().decode(errors="replace")[:300]
            if e.code in (401, 403) and "quota" not in detail.lower():
                tok[0] = token(force_refresh=True)
                continue
            if e.code == 429 and "quota" in detail.lower():
                raise QuotaExhausted(detail) from e
            if attempt == 5:
                raise RuntimeError(f"HTTP {e.code}: {detail}") from e
            time.sleep(2 ** attempt)
        except (urllib.error.URLError, TimeoutError):
            if attempt == 5:
                raise
            time.sleep(2 ** attempt)
    raise RuntimeError("unreachable")


def embed(texts: list[str], tok: list[str]) -> list[list[float]]:
    d = post(f"{API}/accounts/{ACCOUNT_ID}/ai/run/{MODEL}", json.dumps({"text": texts}).encode(),
             "application/json", tok)
    return d["result"]["data"]


def upsert(vectors: list[dict], tok: list[str]) -> None:
    post(f"{API}/accounts/{ACCOUNT_ID}/vectorize/v2/indexes/{INDEX}/upsert",
         "\n".join(json.dumps(v, ensure_ascii=False) for v in vectors).encode(), "application/x-ndjson", tok)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--jobs", type=int, default=JOBS)
    a = ap.parse_args()

    done: dict[str, str] = {}
    if STATE.exists():
        for line in STATE.read_text(encoding="utf-8").splitlines():
            k, _, h = line.partition("\t")
            done[k] = h
    docs = [document(r) for r in pages(a.limit)]
    todo = [d for d in docs if done.get(d["id"]) != d["h"] and d["text"]]
    print(f"pages {len(docs)} · to embed {len(todo)} · chars {sum(len(d['text']) for d in todo):,}")
    if a.dry_run:
        for d in todo[:4]:
            print(f"\n--- {d['meta']['u']}\n{d['text']}")
        return

    tok = [token()]
    batches = [todo[i:i + BATCH] for i in range(0, len(todo), BATCH)]
    pending: list[dict] = []
    n = failed = 0
    t0 = time.time()
    STATE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE, "a", encoding="utf-8") as log, cf.ThreadPoolExecutor(a.jobs) as pool:
        def flush() -> None:
            nonlocal pending, n
            if not pending:
                return
            upsert([{"id": d["id"], "values": d["v"], "metadata": d["meta"]} for d in pending], tok)
            for d in pending:
                log.write(f"{d['id']}\t{d['h']}\n")
            log.flush()
            n += len(pending)
            pending = []
        futs = {pool.submit(embed, [d["text"] for d in b], tok): b for b in batches}
        try:
            for f in cf.as_completed(futs):
                b = futs[f]
                try:
                    vecs = f.result()
                except QuotaExhausted as e:
                    print(f"\nWorkers AI allowance reached: {e}")
                    break
                except Exception as e:  # noqa: BLE001
                    print(f"  ! embed: {e}")
                    failed += len(b)
                    continue
                for d, v in zip(b, vecs):
                    d["v"] = v
                    pending.append(d)
                if len(pending) >= UPSERT:
                    flush()
                    print(f"  {n}/{len(todo)}  {(time.time() - t0) / 60:.1f} min", flush=True)
            flush()
        finally:
            for f in futs:
                f.cancel()
    print(f"\nembedded {n}, failed {failed}, in {(time.time() - t0) / 60:.1f} min")


if __name__ == "__main__":
    main()
