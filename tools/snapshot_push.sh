#!/bin/zsh
# snapshot_push.sh — this branch to GitHub's main as one commit, through a pull request.
#
# The working branch's older commits hold lines that stay on this Mac, so GitHub
# gets snapshots: the tree of HEAD merged with origin/main, as one commit whose
# only parent is origin/main. Nothing here checks out, merges or rewrites the
# local branch. Refuses a tree that matches any line of cache/private_words.txt
# (one extended regex per line, kept on this Mac only).
#
#   tools/snapshot_push.sh ["title"]
set -eu
cd "${0:A:h}/.."
WORDS=cache/private_words.txt
[[ -s $WORDS ]] || { echo "snapshot_push: $WORDS missing — refusing" >&2; exit 4 }
CASE=$(grep -v '^#' $WORDS | paste -sd'|' -)
title=${1:-"Source as of $(date +%F)"}
git fetch -q origin main
tree=$(git merge-tree --write-tree origin/main HEAD | head -1) \
  || { echo "snapshot_push: HEAD and origin/main conflict; merge by hand" >&2; exit 3 }
[[ "$tree" == "$(git rev-parse 'origin/main^{tree}')" ]] && { echo "snapshot_push: nothing new"; exit 0 }
if git grep -q -i -E "$CASE" "$tree"; then
  echo "snapshot_push: REFUSED — the tree matches cache/private_words.txt:" >&2
  git grep -l -i -E "$CASE" "$tree" | sed 's/^[^:]*://' >&2
  exit 4
fi
body="One snapshot of the working branch (HEAD $(git rev-parse --short=10 HEAD)), merged with main.

$(git log --format='- %s' -n 30 --no-merges "$(git merge-base origin/main HEAD 2>/dev/null || echo HEAD~30)"..HEAD | head -30)

🤖 Generated with [Claude Code](https://claude.com/claude-code)"
commit=$(git commit-tree "$tree" -p origin/main -m "$title" -m "HEAD $(git rev-parse --short=10 HEAD)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>")
br="bot/$(date +%Y%m%d-%H%M%S)-source-snapshot"
git push -q origin "${commit}:refs/heads/${br}"
url=$(gh pr create --base main --head "$br" --title "$title" --body "$body")
gh pr merge "$url" --merge >/dev/null
gh api -X DELETE "repos/{owner}/{repo}/git/refs/heads/${br}" >/dev/null 2>&1 || true
git fetch -q origin main
echo "merged $url"
