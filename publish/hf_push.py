#!/usr/bin/env python3
"""One door to Hugging Face, so four builders do not grow four dialects.

The token is the one Nan sent on 2026-09-08 and lives where the hub library
already looks (~/.cache/huggingface/token). It belongs to the account
NaNoBotCo — a user, not an organisation — which is why every repo id below
starts with that and not with an org that does not exist.

Pushing is a separate step from building on purpose. Each make_hf_*.py writes
a complete repo folder and stops; this uploads one when asked. A build that
pushed by itself would put a half-measured number in public the first time a
run went wrong.

    python3 publish/hf_push.py <folder> <repo_id> [--space] [--sdk static]
"""

import sys
from pathlib import Path

from huggingface_hub import HfApi


def push(folder, repo_id, repo_type="dataset", private=False, sdk=None):
    api = HfApi()
    kw = {"repo_id": repo_id, "repo_type": repo_type,
          "exist_ok": True, "private": private}
    if sdk:
        kw["space_sdk"] = sdk
    api.create_repo(**kw)
    api.upload_folder(folder_path=str(folder), repo_id=repo_id,
                      repo_type=repo_type,
                      commit_message="build from motdang publish/")
    kind = "spaces" if repo_type == "space" else "datasets"
    return f"https://huggingface.co/{kind}/{repo_id}"


if __name__ == "__main__":
    argv = sys.argv[1:]
    space = "--space" in argv
    sdk = "static"
    if "--sdk" in argv:
        sdk = argv[argv.index("--sdk") + 1]
        argv = [a for i, a in enumerate(argv)
                if i not in (argv.index("--sdk"), argv.index("--sdk") + 1)]
    args = [a for a in argv if not a.startswith("--")]
    folder, repo_id = Path(args[0]), args[1]
    print(push(folder, repo_id,
               repo_type="space" if space else "dataset",
               sdk=sdk if space else None))
