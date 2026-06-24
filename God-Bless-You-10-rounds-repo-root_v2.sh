#!/usr/bin/env bash

set -euo pipefail

# codex-10-rounds-any-repo.sh
# This script is intended to be placed and executed from the root of any Git repository.
# It automatically uses the current directory as the project root.
PROJECT="$(pwd)"
ROUNDS=10

# Verify that the current directory is a Git repository.
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "ERROR: This script must be run from inside a Git repository."
    echo "Current directory: $PROJECT"
    exit 1
fi

# Move to the real root of the repository, even if the script was launched from a subfolder.
PROJECT="$(git rev-parse --show-toplevel)"
cd "$PROJECT"

echo "======================================"
echo "Codex CLI - 10 Automatic Rounds"
echo "Project: $PROJECT"
echo "======================================"

PROMPT_TEXT=$(cat <<'PROMPT'
Continue with the development
PROMPT
)

for i in $(seq 1 "$ROUNDS"); do

    echo
    echo "======================================"
    echo "ROUND $i OF $ROUNDS"
    echo "======================================"
    echo

    codex exec \
      --sandbox workspace-write \
      "$PROMPT_TEXT"

    echo
    echo "======================================"
    echo "END OF ROUND $i"
    echo "======================================"

    echo
    git status --short || true

    echo
    echo "Waiting 5 seconds..."
    sleep 5

done

echo
echo "======================================"
echo "ALL $ROUNDS ROUNDS HAVE FINISHED"
echo "======================================"

git status
