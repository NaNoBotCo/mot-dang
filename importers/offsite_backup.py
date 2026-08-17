#!/usr/bin/env python3
"""Keep the repository somewhere that is not this laptop — without GitHub.

The one thing GitHub was still genuinely doing was holding a copy off the
machine. It was doing it badly: a hidden account is a backup you cannot browse,
cannot share, and cannot be certain will still be there, and two appeal memos
have gone unanswered. So the copy goes somewhere she owns outright.

`git bundle` is the right shape and is not widely known. It is one file holding
the COMPLETE repository — every commit, branch and tag — which `git clone`
opens directly:

    git clone mot-dang-2026-08-17.bundle mot-dang

That is not an export or a snapshot of the working tree. It is the repository,
in a file, in her own bucket. Lose the laptop and the history survives; lose
Cloudflare and the laptop still has it. Neither copy depends on an account
somebody else can switch off.

Credentials and the rclone plumbing are reused from publish/deploy.py rather
than reimplemented, so there is exactly one place that knows how to reach R2.

    python3 importers/offsite_backup.py            # bundle, verify, upload
    python3 importers/offsite_backup.py --check    # also prove it clones back
    python3 importers/offsite_backup.py --list     # what is already up there

SIZE: the bundle is ~600 MB because docs/ is committed, so the history carries
every built page. That is why the morning walk runs this weekly rather than
daily, and why only the last KEEP bundles are retained.
"""
import argparse
import os
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "publish"))
import deploy  # noqa: E402  — creds() + rclone_env(), the one place that knows R2

BUCKET = "mot-dang-site"
PREFIX = "backup"
KEEP = 4        # a month of weeklies


def sh(args, **kw):
    return subprocess.run(args, capture_output=True, text=True, **kw)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="prove the bundle clones back")
    ap.add_argument("--list", action="store_true", help="list bundles already in the bucket")
    args = ap.parse_args()

    env = deploy.rclone_env(deploy.creds())
    remote = f"r2:{BUCKET}/{PREFIX}"

    if args.list:
        out = sh(["rclone", "lsl", remote], env=env)
        print(out.stdout.strip() or "   (nothing up there yet)")
        return 0

    today = date.today().isoformat()
    with tempfile.TemporaryDirectory() as tmp:
        bundle = Path(tmp) / f"mot-dang-{today}.bundle"

        print("🐜 bundling the whole repository…")
        r = sh(["git", "bundle", "create", str(bundle), "--all"], cwd=ROOT)
        if r.returncode:
            print("   bundle failed:", r.stderr.strip()[-300:])
            return 1

        # A bundle that does not verify is a comfort, not a backup.
        if sh(["git", "bundle", "verify", str(bundle)], cwd=ROOT).returncode:
            print("   bundle did not verify — not uploading")
            return 1
        mb = bundle.stat().st_size / 1_000_000

        if args.check:
            print("   proving it clones back…")
            dest = Path(tmp) / "roundtrip"
            if sh(["git", "clone", "--quiet", str(bundle), str(dest)]).returncode:
                print("   ✗ would not clone — not uploading")
                return 1
            n = sh(["git", "-C", str(dest), "rev-list", "--count", "HEAD"]).stdout.strip()
            print(f"   ✓ clones clean ({n} commits)")

        print(f"🐜 uploading {mb:.0f} MB to {remote}/ …")
        r = sh(["rclone", "copyto", str(bundle), f"{remote}/{bundle.name}",
                "--s3-chunk-size", "64M"], env=env)
        if r.returncode:
            print("   upload failed:", r.stderr.strip()[-300:])
            return 1

    # Retention, after a successful upload and never before it — pruning first
    # would trade a good old backup for a failed new one.
    listing = sh(["rclone", "lsf", remote], env=env).stdout.split()
    old = sorted(f for f in listing if f.endswith(".bundle"))[:-KEEP]
    for f in old:
        sh(["rclone", "deletefile", f"{remote}/{f}"], env=env)
    if old:
        print(f"   pruned {len(old)} older bundle(s), keeping {KEEP}")

    print(f"🐜 offsite: {remote}/mot-dang-{today}.bundle")
    print(f"   restore:  git clone mot-dang-{today}.bundle mot-dang")
    return 0


if __name__ == "__main__":
    sys.exit(main())
