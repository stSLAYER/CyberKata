#!/usr/bin/env python3
"""CyberKata Hydra Lab - a deliberately vulnerable local training server.

This application is intentionally insecure. It is designed only for local,
authorised practice with Hydra and binds to 127.0.0.1 by default.
"""

from __future__ import annotations

import argparse
import hmac
import json
import mimetypes
import socket
import sys
import threading
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


VERSION = "1.0.0"
ROOT = Path(__file__).resolve().parent
APP_DIR = ROOT / "app"

LEVELS = {
    "1": {
        "username": "kata",
        "password": "neonpulse",
        "failure": "ACCESS_DENIED",
        "flag": "CK{PASSWORD_HUNTER}",
    },
    "2": {
        "username": "operator",
        "password": "dojo-pass",
        "failure": "UNKNOWN_OPERATOR",
        "flag": "CK{USERNAME_FOUND}",
    },
    "3": {
        "username": "admin",
        "password": "nightshift42",
        "failure": "INVALID_CREDENTIAL_PAIR",
        "flag": "CK{PAIR_CRACKED}",
    },
    "4": {
        "username": "analyst",
        "password": "response302",
        "failure": "AUTHENTICATION_FAILED_200",
        "flag": "CK{RESPONSE_LOGIC_MASTERED}",
        "token": "cyberkata-local-vault",
    },
}


def secure_equal(left: str, right: str) -> bool:
    return hmac.compare_digest(left.encode("utf-8"), right.encode("utf-8"))


def local_ip() -> str:
    """Return a useful LAN address without sending any network traffic."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("192.0.2.1", 80))
        return sock.getsockname()[0]
    except OSError:
        try:
            return socket.gethostbyname(socket.gethostname())
        except OSError:
            return "<your-computer-ip>"
    finally:
        sock.close()


class LabServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        self.completed: set[str] = set()
        self.progress_lock = threading.Lock()


class LabHandler(BaseHTTPRequestHandler):
    server_version = "CyberKataLab/1.0"

    def log_message(self, _format: str, *_args: object) -> None:
        # Hydra can generate hundreds of requests. Keep the beginner-facing
        # terminal readable instead of printing one line per attempt.
        return

    def _security_headers(self) -> None:
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; img-src 'self'; style-src 'self'; "
            "script-src 'self'; connect-src 'self'; base-uri 'none'; frame-ancestors 'none'",
        )
        self.send_header("Cache-Control", "no-store")

    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self._security_headers()
        self.end_headers()
        if self.command != "HEAD":
            try:
                self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError):
                pass

    def _text(self, status: int, text: str) -> None:
        self._send(status, text.encode("utf-8"), "text/plain; charset=utf-8")

    def _json(self, status: int, value: object) -> None:
        data = json.dumps(value, separators=(",", ":")).encode("utf-8")
        self._send(status, data, "application/json; charset=utf-8")

    def _serve_static(self, request_path: str) -> None:
        relative = "index.html" if request_path == "/" else request_path.lstrip("/")
        candidate = (APP_DIR / urllib.parse.unquote(relative)).resolve()
        try:
            candidate.relative_to(APP_DIR.resolve())
        except ValueError:
            self._text(403, "FORBIDDEN")
            return

        if not candidate.is_file():
            self._text(404, "NOT_FOUND")
            return

        content_type = mimetypes.guess_type(candidate.name)[0] or "application/octet-stream"
        if content_type.startswith("text/") or content_type in {
            "application/javascript",
            "application/json",
        }:
            content_type += "; charset=utf-8"
        self._send(200, candidate.read_bytes(), content_type)

    def do_HEAD(self) -> None:  # noqa: N802
        self.do_GET()

    def do_GET(self) -> None:  # noqa: N802
        parsed = urllib.parse.urlsplit(self.path)
        if parsed.path == "/health":
            self._json(200, {"status": "ready", "version": VERSION})
            return
        if parsed.path == "/api/status":
            with self.server.progress_lock:
                completed = sorted(self.server.completed)
            self._json(
                200,
                {
                    "name": "CyberKata Hydra Lab",
                    "version": VERSION,
                    "levels": 4,
                    "completed": completed,
                    "scope": "local-authorised-training-only",
                },
            )
            return
        if parsed.path == "/vault":
            query = urllib.parse.parse_qs(parsed.query)
            token = query.get("token", [""])[0]
            expected = LEVELS["4"]["token"]
            if not secure_equal(token, expected):
                self._text(403, "VAULT_ACCESS_DENIED")
                return
            self._text(
                200,
                "HYDRA_DOJO_COMPLETE\nLEVEL=4\nFLAG=" + LEVELS["4"]["flag"] + "\n",
            )
            return
        self._serve_static(parsed.path)

    def do_POST(self) -> None:  # noqa: N802
        parsed = urllib.parse.urlsplit(self.path)
        prefix = "/api/login/"
        if not parsed.path.startswith(prefix):
            self._text(404, "NOT_FOUND")
            return

        level_id = parsed.path[len(prefix) :]
        if level_id not in LEVELS:
            self._text(404, "UNKNOWN_LEVEL")
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._text(400, "INVALID_CONTENT_LENGTH")
            return
        if length > 16_384:
            self._text(413, "REQUEST_TOO_LARGE")
            return

        raw = self.rfile.read(length).decode("utf-8", errors="replace")
        form = urllib.parse.parse_qs(raw, keep_blank_values=True)
        username = form.get("username", [""])[0]
        password = form.get("password", [""])[0]
        level = LEVELS[level_id]
        valid = secure_equal(username, level["username"]) and secure_equal(
            password, level["password"]
        )

        if not valid:
            self._text(200, level["failure"] + "\nLEVEL=" + level_id + "\n")
            return

        with self.server.progress_lock:
            self.server.completed.add(level_id)

        if level_id == "4":
            location = "/vault?level=4&token=" + urllib.parse.quote(level["token"])
            self.send_response(302)
            self.send_header("Location", location)
            self.send_header("Content-Length", "0")
            self._security_headers()
            self.end_headers()
            return

        self._text(
            200,
            "ACCESS_GRANTED\nLEVEL=" + level_id + "\nFLAG=" + level["flag"] + "\n",
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the deliberately vulnerable CyberKata Hydra practice lab."
    )
    parser.add_argument("--host", default="127.0.0.1", help="address to bind")
    parser.add_argument("--port", type=int, default=8080, help="port to bind")
    parser.add_argument(
        "--no-browser", action="store_true", help="do not open the lab automatically"
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        server = LabServer((args.host, args.port), LabHandler)
    except OSError as exc:
        print("\n[!] CyberKata could not start the lab:", exc)
        print(f"[!] Port {args.port} may already be in use.\n")
        return 1

    safe_mode = args.host in {"127.0.0.1", "localhost"}
    browser_host = "127.0.0.1" if args.host == "0.0.0.0" else args.host
    browser_url = f"http://{browser_host}:{args.port}/"

    print("\n" + "=" * 64)
    print("  CYBERKATA HYDRA LAB // HYDRA DOJO")
    print("=" * 64)
    print(f"  Version : {VERSION}")
    print(f"  Browser : {browser_url}")
    if safe_mode:
        print("  Target  : 127.0.0.1")
        print("  Mode    : LOCAL SAFE MODE")
    else:
        print(f"  VM target: {local_ip()}:{args.port}")
        print("  Mode     : VM/LAN MODE - stop the lab when training is complete")
    print("  Stop    : Press Ctrl+C")
    print("=" * 64 + "\n")

    if not args.no_browser:
        threading.Timer(0.8, lambda: webbrowser.open(browser_url)).start()

    try:
        server.serve_forever(poll_interval=0.2)
    except KeyboardInterrupt:
        print("\n[+] Hydra Dojo stopped. Nice work, operator.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
