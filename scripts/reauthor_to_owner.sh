#!/usr/bin/env bash
# Rewrite Cursor/bot commit authors to Bogdan Shcherbinin (blessed-bless).
# Requires temporary ability to force-push master (branch protection off or bypass).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

OWNER_NAME="Bogdan Shcherbinin"
OWNER_EMAIL="blessed-bless@users.noreply.github.com"
BOT_EMAIL='206951365+cursor[bot]@users.noreply.github.com'

git config user.name "$OWNER_NAME"
git config user.email "$OWNER_EMAIL"

export FILTER_BRANCH_SQUELCH_WARNING=1
git checkout master
git pull origin master

git filter-branch -f --env-filter "
OWNER_NAME='$OWNER_NAME'
OWNER_EMAIL='$OWNER_EMAIL'
BOT_EMAIL='$BOT_EMAIL'
rewrite() {
  local side=\$1
  local name_var=GIT_\${side}_NAME
  local email_var=GIT_\${side}_EMAIL
  local email=\${!email_var}
  if [ \"\$email\" = 'cursoragent@cursor.com' ] || [ \"\$email\" = \"\$BOT_EMAIL\" ] || [ \"\$email\" = 'cursor@cursor.com' ] || [ \"\$email\" = 'phungngocvuzyuh69739@gmail.com' ]; then
    export GIT_\${side}_NAME=\"\$OWNER_NAME\"
    export GIT_\${side}_EMAIL=\"\$OWNER_EMAIL\"
  fi
}
rewrite AUTHOR
rewrite COMMITTER
" master

TIP="$(git rev-parse master)"
git tag -d v0.1.0 2>/dev/null || true
GIT_COMMITTER_NAME="$OWNER_NAME" GIT_COMMITTER_EMAIL="$OWNER_EMAIL" \
  git tag -a v0.1.0 -m "FleetKit 0.1.0" "$TIP"

rm -rf .git/refs/original/
git reflog expire --expire=now --all
git gc --prune=now --quiet

echo "Rewritten. Authors now:"
git log master --format='%an <%ae>' | sort | uniq -c

echo
echo "Force-push when branch protection allows:"
echo "  git push --force-with-lease origin master"
echo "  git push --force origin v0.1.0"
