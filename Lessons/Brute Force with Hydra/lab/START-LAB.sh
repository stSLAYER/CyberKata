#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")"

if command -v python3 >/dev/null 2>&1; then
    exec python3 server.py
fi

if command -v python >/dev/null 2>&1; then
    exec python server.py
fi

printf '%s\n' "Python 3 was not found. Install Python 3 and run this script again."
exit 1
