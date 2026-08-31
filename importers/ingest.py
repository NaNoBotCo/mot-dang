#!/usr/bin/env python3
"""The write discipline every fetcher obeys. WO-41 Phase 2. Stdlib only.

WHY THIS EXISTS, IN ONE MEASURED SENTENCE: on 2026-08-24 the events harvest
finished with zero rows and wrote the empty basket over 69 good events, and
nothing in the pipeline could afterwards tell "fresh data that happens to be
identical" from "a dead feed's last words" — because the only thing on disk
was the data file itself.

So a fetcher no longer writes its own file. It hands the document here, and
five rules apply that no script can skip:

  1. VALIDATE BEFORE WRITE — a document with fewer than `min_rows` rows is
     refused. Refused, not written: the previous good file stays exactly as
     it was, byte for byte.
  2. ATOMIC WRITE — a temporary file in the same directory, then rename().
     A killed process never leaves a half-written JSON behind, which is the
     one corruption a reader cannot detect.
  3. NEVER DESTRUCTIVE ON FAILURE — refuse() and record_failure() touch the
     meta file only. Yesterday's good data outranks today's empty basket
     every time.
  4. SIDECAR METADATA, ALWAYS — data/events.json gets data/events.meta.json,
     written on success AND on failure. `consecutive_failures` and
     `last_success_at` are what turn a silent stall into something a build
     gate, a status page or a person can act on.
  5. QUORUM — a multi-source feed passes its per-source outcomes in, and the
     batch is refused when fewer than `quorum` sources answered. One dead
     source is a fact to record, not a reason to lose a whole feed.

BYTE-IDENTICAL WRITES DO NOT TOUCH THE DATA FILE. make_lottery.py established
this: a re-fetch that finds the same draw must leave the file alone, because
the standing walk's change gate reads content and an unchanged fact is not
news. The meta file still records that we looked (`checked_at`), so silence
and success stay distinguishable.

THE META FILES AND THE CHANGE GATE. A meta file is rewritten every run, so
its timestamps would rebuild the whole site every twenty minutes if they were
hashed — the exact failure importers/walk_fingerprint.py's docstring warns
about. Its snake_case stamps are therefore listed in that file's
VOLATILE_KEYS, so what gets hashed is what a meta file MEANS (row counts,
which sources answered, how many runs have failed) and not when it was
written. They are also gitignored: this is per-machine operational state,
regenerated on every run like cache/last-published.json, and a fresh clone
with no meta at all is a supported state — read_meta() returns {} and every
consumer must treat that as "not known yet", never as "failing".

    from ingest import write, refuse, read_meta
"""
import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _now():
    """UTC, seconds, with the Z — one shape for every stamp this file writes."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def meta_path(data_path):
    p = Path(data_path)
    return p.with_name(p.stem + ".meta.json")


def read_meta(data_path):
    """The sidecar, or {} when there is none. An absent meta file is normal —
    a fresh clone, or a feed that has not run since this discipline landed —
    and must never read as a failure."""
    p = meta_path(data_path)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text())
    except ValueError:
        return {}


def _dump(doc):
    return json.dumps(doc, ensure_ascii=False, indent=1)


def _hash(text):
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def _atomic_write(path, text):
    """Same directory, then rename — a cross-device rename is not atomic, and
    a temp file in /tmp would be exactly that."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix="." + path.name + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _write_meta(data_path, **fields):
    prev = read_meta(data_path)
    meta = {
        "file": Path(data_path).name,
        "checked_at": _now(),
        "fetched_at": prev.get("fetched_at"),
        "last_success_at": prev.get("last_success_at"),
        "consecutive_failures": prev.get("consecutive_failures", 0),
        "row_count": prev.get("row_count"),
        "content_hash": prev.get("content_hash"),
        "sources_ok": prev.get("sources_ok", []),
        "sources_failed": prev.get("sources_failed", []),
        "source_published_at": prev.get("source_published_at"),
        "last_error": prev.get("last_error"),
    }
    meta.update(fields)
    _atomic_write(meta_path(data_path), _dump(meta))
    return meta


def refuse(data_path, reason, sources_ok=(), sources_failed=()):
    """This run brought nothing usable. The data file is not touched; the
    meta file counts the failure and keeps the last success where it is.

    Returns False, so a caller can `return ingest.refuse(...)` and read as
    what it does."""
    meta = _write_meta(
        data_path,
        consecutive_failures=read_meta(data_path).get("consecutive_failures", 0) + 1,
        last_error=str(reason)[:400],
        sources_ok=list(sources_ok),
        sources_failed=[list(x) if isinstance(x, tuple) else x for x in sources_failed],
    )
    print(f"⚠  {Path(data_path).name} kept — {reason} "
          f"(failure {meta['consecutive_failures']})")
    return False


def write(data_path, doc, count=None, min_rows=1, sources_ok=(), sources_failed=(),
          quorum=None, source_published_at=None, label=None):
    """Validate, then write atomically, then record. Returns True if the data
    file now holds this document (including when it already did, byte for
    byte), False if the document was refused and the previous file stands.

    `count` is the caller's own row count — every feed knows the shape of its
    own payload better than a generic dotted-path walker does, and a wrong
    guess here would silently disable the guard.
    """
    name = label or Path(data_path).name
    if count is None:
        count = len(doc) if isinstance(doc, (list, tuple)) else None

    ok, failed = list(sources_ok), list(sources_failed)
    if quorum is not None and len(ok) < quorum:
        return refuse(data_path,
                      f"quorum not met — {len(ok)} of {quorum} source(s) answered "
                      f"(failed: {[f[0] if isinstance(f, (list, tuple)) else f for f in failed]})",
                      ok, failed)
    if count is not None and count < min_rows:
        return refuse(data_path,
                      f"{count} row(s), expected at least {min_rows}", ok, failed)

    text = _dump(doc)
    digest = _hash(text)
    p = Path(data_path)
    unchanged = p.exists() and read_meta(data_path).get("content_hash") == digest
    if not unchanged:
        _atomic_write(p, text)
    _write_meta(data_path,
                fetched_at=_now(),
                last_success_at=_now(),
                consecutive_failures=0,
                row_count=count,
                content_hash=digest,
                sources_ok=ok,
                sources_failed=[list(x) if isinstance(x, tuple) else x for x in failed],
                source_published_at=source_published_at,
                last_error=None)
    if failed:
        print(f"   {name}: {len(failed)} source(s) failed, "
              f"{len(ok)} answered — recorded, not swallowed")
    print(f"🐜 {name}: {count if count is not None else '?'} row(s)"
          f"{' (unchanged)' if unchanged else ''} -> {p}")
    return True
