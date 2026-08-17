#!/usr/bin/env python3
"""Keep every repository somewhere that is not this laptop — without GitHub.

The one thing GitHub was still genuinely doing was holding a copy off the
machine, and it was doing it badly: a hidden account is a backup you cannot
browse, cannot share, and cannot be sure will still be there. Two appeal memos
have gone unanswered. So the copies go somewhere she owns outright.

`git bundle` is the right shape and is not widely known. One file holds the
COMPLETE repository — every commit, branch and tag — and `git clone` opens it
directly:

    git clone mot-dang-2026-08-17.bundle mot-dang

That is not an export or a snapshot of a working tree. It is the repository, in
a file, in her own bucket. Lose the laptop and the history survives; lose
Cloudflare and the laptop still has it. Neither copy depends on an account
somebody else can switch off.

A SEPARATE BUCKET, AND WHY IT IS NOT NEGOTIABLE
-----------------------------------------------
The first version of this wrote into mot-dang-site/backup/. That bucket is the
published site, and publish/deploy.py syncs docs/ onto it — and `rclone sync`
deletes whatever is in the destination and not in the source. So the backup
uploaded cleanly, reported success, and was erased by the next deploy a few
minutes later. A backup living in a bucket something else syncs is not a backup;
it is a countdown. Hence nanobotco-backup, which nothing syncs onto.

    python3 importers/offsite_backup.py                 # this repo
    python3 importers/offsite_backup.py --all           # every repo in the fleet
    python3 importers/offsite_backup.py --check         # prove each clones back
    python3 importers/offsite_backup.py --list          # what is already up there
"""
import argparse
import os
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FLEET = ROOT.parent                       # ~/Developer/claude code projects
sys.path.insert(0, str(ROOT / "publish"))
import deploy  # noqa: E402  — creds() + rclone_env(), the one place that knows R2

# NOT mot-dang-site. See the note above; that bucket is swept by every deploy.
BUCKET = "nanobotco-backup"
KEEP = 3        # bundles retained per repo


def sh(args, env=None, **kw):
    return subprocess.run(args, capture_output=True, text=True, env=env, **kw)


# Repositories that must never leave this machine, whoever is asking and
# however private the destination. Medical and court material: the standing
# rule is LOCAL ONLY, and "her own bucket" is not an exemption from it.
#
# This list exists because the first --all run swept every .git directory it
# could find and shipped tel (seizure telemetry), khwan (the posterity vault)
# and michael-go-court off the laptop. They were purged, but a denylist alone
# is a promise; the origin test below is the structure.
NEVER_LEAVES = {"tel", "khwan", "michael-go-court", "corpus"}
NEVER_SUBSTRINGS = ("legal", "court", "medical", "seizure")


def local_only(d):
    n = d.name.lower()
    if n in NEVER_LEAVES or any(k in n for k in NEVER_SUBSTRINGS):
        return "named local-only"
    # A repo somebody deliberately never gave a remote is a repo that was
    # never meant to travel. The point of this script is to replace the
    # offsite copy GitHub used to hold — so a repo that never had one is out
    # of scope, and opting it in is her decision, not a default.
    r = sh(["git", "-C", str(d), "remote", "get-url", "origin"]).stdout.strip()
    if not r:
        return "no remote — never left this machine"
    return None


def repos(all_of_them):
    if not all_of_them:
        return [ROOT]
    out, skipped = [], []
    for d in sorted(FLEET.iterdir()):
        if not (d / ".git").is_dir():
            continue
        why = local_only(d)
        (skipped if why else out).append((d, why))
    for d, why in skipped:
        print(f"  {d.name:28} skipped — {why}")
    return [d for d, _ in out]


def bundle_one(repo, env, today, check):
    """Bundle one repository, verify it, upload it, prune old copies.

    Returns (name, megabytes) on success, or (name, None) if it was skipped or
    failed — the caller keeps going either way, because one broken repo must
    not cost the other forty-three their backup.
    """
    name = repo.name
    if not sh(["git", "-C", str(repo), "rev-parse", "HEAD"]).stdout.strip():
        print(f"  {name:28} no commits yet — nothing to bundle")
        return name, None

    with tempfile.TemporaryDirectory() as tmp:
        bundle = Path(tmp) / f"{name}-{today}.bundle"
        if sh(["git", "bundle", "create", str(bundle), "--all"], cwd=repo).returncode:
            print(f"  {name:28} bundle FAILED")
            return name, None
        if sh(["git", "bundle", "verify", str(bundle)], cwd=repo).returncode:
            print(f"  {name:28} bundle did not verify — not uploading")
            return name, None
        mb = bundle.stat().st_size / 1_000_000

        if check:
            dest = Path(tmp) / "roundtrip"
            if sh(["git", "clone", "--quiet", str(bundle), str(dest)]).returncode:
                print(f"  {name:28} would NOT clone back — not uploading")
                return name, None

        r = sh(["rclone", "copyto", str(bundle), f"r2:{BUCKET}/{name}/{bundle.name}",
                "--s3-chunk-size", "64M"], env=env)
        if r.returncode:
            print(f"  {name:28} upload FAILED: {r.stderr.strip()[-120:]}")
            return name, None

    # Retention runs only after a successful upload — pruning first would trade
    # a good old backup for a failed new one.
    listing = sh(["rclone", "lsf", f"r2:{BUCKET}/{name}"], env=env).stdout.split()
    for old in sorted(f for f in listing if f.endswith(".bundle"))[:-KEEP]:
        sh(["rclone", "deletefile", f"r2:{BUCKET}/{name}/{old}"], env=env)

    print(f"  {name:28} ✓ {mb:>8.1f} MB")
    return name, mb


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true", help="every repo in the fleet")
    ap.add_argument("--check", action="store_true", help="prove each bundle clones back")
    ap.add_argument("--list", action="store_true", help="what is already in the bucket")
    args = ap.parse_args()

    env = deploy.rclone_env(deploy.creds())

    if args.list:
        out = sh(["rclone", "ls", f"r2:{BUCKET}"], env=env)
        lines = [l for l in out.stdout.splitlines() if l.strip()]
        total = sum(int(l.split()[0]) for l in lines) / 1_000_000_000 if lines else 0
        print("\n".join("  " + l for l in lines) or "  (nothing up there yet)")
        print(f"\n  {len(lines)} bundle(s), {total:.2f} GB")
        return 0

    today = date.today().isoformat()
    todo = repos(args.all)
    print(f"🐜 bundling {len(todo)} repositor{'ies' if len(todo) > 1 else 'y'} "
          f"-> r2:{BUCKET}/")
    done = [bundle_one(r, env, today, args.check) for r in todo]
    ok = [(n, m) for n, m in done if m is not None]
    failed = [n for n, m in done if m is None]
    print(f"\n🐜 {len(ok)} bundled, {sum(m for _, m in ok) / 1000:.2f} GB total"
          + (f" · {len(failed)} skipped: {', '.join(failed)}" if failed else ""))
    print(f"   restore any of them:  git clone <name>-{today}.bundle <name>")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
