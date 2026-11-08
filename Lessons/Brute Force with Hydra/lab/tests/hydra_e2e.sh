#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
QA_DIR="$(mktemp -d /tmp/cyberkata-hydra-qa.XXXXXX)"
PORT="${CYBERKATA_QA_PORT:-8080}"
SERVER_PID=""

cleanup() {
  if [[ -n "$SERVER_PID" ]]; then
    kill "$SERVER_PID" 2>/dev/null || true
    wait "$SERVER_PID" 2>/dev/null || true
  fi
  rm -rf "$QA_DIR"
}
trap cleanup EXIT

cd "$ROOT"
python3 server.py --port "$PORT" --no-browser >"$QA_DIR/server.log" 2>&1 &
SERVER_PID=$!

READY=0
for _ in $(seq 1 50); do
  if curl -fsS "http://127.0.0.1:$PORT/health" >"$QA_DIR/health.json"; then
    READY=1
    break
  fi
  sleep 0.1
done

if [[ "$READY" -ne 1 ]]; then
  printf 'FAIL: Python server did not become ready\n' >&2
  cat "$QA_DIR/server.log" >&2
  exit 1
fi

printf 'PASS: server %s\n' "$(cat "$QA_DIR/health.json")"
hydra -h >"$QA_DIR/hydra-version.log" 2>&1 || true
grep -m1 'Hydra v' "$QA_DIR/hydra-version.log"

run_and_assert() {
  local label="$1"
  local expected_regex="$2"
  shift 2

  "$@" >"$QA_DIR/$label.log" 2>&1
  if ! grep -Eq "$expected_regex" "$QA_DIR/$label.log"; then
    printf 'FAIL: %s did not find the expected credential\n' "$label" >&2
    tail -n 30 "$QA_DIR/$label.log" >&2
    exit 1
  fi

  printf 'PASS: %s -> ' "$label"
  grep -E "$expected_regex" "$QA_DIR/$label.log" | tail -n 1
}

run_and_assert \
  level-1 \
  'login: kata[[:space:]]+password: neonpulse' \
  hydra -l kata -P wordlists/passwords.txt 127.0.0.1 -s "$PORT" \
    http-post-form '/api/login/1:username=^USER^&password=^PASS^:F=ACCESS_DENIED' \
    -t 4 -f -V

run_and_assert \
  level-2 \
  'login: operator[[:space:]]+password: dojo-pass' \
  hydra -L wordlists/usernames.txt -p dojo-pass 127.0.0.1 -s "$PORT" \
    http-post-form '/api/login/2:username=^USER^&password=^PASS^:F=UNKNOWN_OPERATOR' \
    -t 4 -f -V

run_and_assert \
  level-3 \
  'login: admin[[:space:]]+password: nightshift42' \
  hydra -L wordlists/usernames.txt -P wordlists/passwords.txt 127.0.0.1 -s "$PORT" \
    http-post-form '/api/login/3:username=^USER^&password=^PASS^:F=INVALID_CREDENTIAL_PAIR' \
    -t 4 -f -V

run_and_assert \
  level-4 \
  'login: analyst[[:space:]]+password: response302' \
  hydra -L wordlists/usernames.txt -P wordlists/passwords.txt 127.0.0.1 -s "$PORT" \
    http-post-form '/api/login/4:username=^USER^&password=^PASS^:S=HYDRA_DOJO_COMPLETE' \
    -t 4 -f -V

run_and_assert \
  combo-list \
  'login: admin[[:space:]]+password: nightshift42' \
  hydra -C wordlists/credential-pairs.txt 127.0.0.1 -s "$PORT" \
    http-post-form '/api/login/3:username=^USER^&password=^PASS^:F=INVALID_CREDENTIAL_PAIR' \
    -t 4 -f -V

STATUS="$(curl -fsS "http://127.0.0.1:$PORT/api/status")"
if [[ "$STATUS" != *'"completed":["1","2","3","4"]'* ]]; then
  printf 'FAIL: completion tracking mismatch: %s\n' "$STATUS" >&2
  exit 1
fi
printf 'PASS: progress tracking -> %s\n' "$STATUS"
printf 'PASS: all real Hydra end-to-end tests completed\n'
