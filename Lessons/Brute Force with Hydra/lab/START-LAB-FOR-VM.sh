#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")"

printf '%s\n' "WARNING: VM mode exposes the training lab to your local network."
printf '%s\n' "Use it only on a trusted network and stop it when training is complete."
printf '%s' "Continue? [y/N] "
read -r answer
case "$answer" in
    y|Y|yes|YES) ;;
    *) exit 0 ;;
esac

if command -v python3 >/dev/null 2>&1; then
    exec python3 server.py --host 0.0.0.0
fi

if command -v python >/dev/null 2>&1; then
    exec python server.py --host 0.0.0.0
fi

printf '%s\n' "Python 3 was not found. Install Python 3 and run this script again."
exit 1
