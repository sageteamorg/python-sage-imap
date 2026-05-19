#!/usr/bin/env bash
set -euo pipefail

HOST="${IMAP_HOST:-127.0.0.1}"
PORT="${IMAP_PORT:-993}"
MAX_WAIT="${IMAP_WAIT_SECONDS:-120}"

echo "Waiting for IMAP at ${HOST}:${PORT} (max ${MAX_WAIT}s)..."
for i in $(seq 1 "$MAX_WAIT"); do
  if (echo >/dev/tcp/"$HOST"/"$PORT") 2>/dev/null; then
    echo "IMAP port is open."
    exit 0
  fi
  sleep 1
done
echo "Timeout waiting for IMAP" >&2
exit 1
