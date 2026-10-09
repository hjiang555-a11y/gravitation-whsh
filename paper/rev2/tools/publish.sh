#!/usr/bin/env bash
# One-command publish for paper/rev2: verify -> sync Overleaf package -> commit -> push.
# Usage: tools/publish.sh "commit message"
set -euo pipefail
REV2="$(cd "$(dirname "$0")/.." && pwd)"
ROOT="$(cd "$REV2/../.." && pwd)"
MSG="${1:-}"

if [ -z "$MSG" ]; then
  echo "usage: tools/publish.sh \"commit message\"" >&2
  exit 2
fi

"$REV2/tools/check.sh"
"$REV2/tools/sync_overleaf.sh"

cd "$ROOT"
git add paper/rev2 paper/overleaf-rev2 paper/overleaf-rev2-upload.zip README.md .gitignore
if git diff --cached --quiet; then
  echo "nothing to publish"
  exit 0
fi
git commit -m "$MSG"
git push origin main
echo "Pushed $(git rev-parse --short HEAD) to origin/main"
