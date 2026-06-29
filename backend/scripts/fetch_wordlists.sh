#!/usr/bin/env bash
# Download large wordlists from SecLists into app/wordlists/.
# These are gitignored (too big to commit); common.txt ships as a fallback.
set -euo pipefail

DEST="$(cd "$(dirname "$0")/.." && pwd)/app/wordlists"
ROCKYOU_URL="https://raw.githubusercontent.com/danielmiessler/SecLists/master/Passwords/Leaked-Databases/rockyou.txt.tar.gz"

mkdir -p "$DEST"

if [ -f "$DEST/rockyou.txt" ]; then
  echo "rockyou.txt already present ($(wc -l < "$DEST/rockyou.txt") lines). Skipping."
  exit 0
fi

echo "Downloading rockyou.txt.tar.gz from SecLists..."
curl -L --fail -o "$DEST/rockyou.txt.tar.gz" "$ROCKYOU_URL"

echo "Extracting..."
tar -xzf "$DEST/rockyou.txt.tar.gz" -C "$DEST"
rm -f "$DEST/rockyou.txt.tar.gz"

echo "Done: $(wc -l < "$DEST/rockyou.txt") passwords in $DEST/rockyou.txt"
