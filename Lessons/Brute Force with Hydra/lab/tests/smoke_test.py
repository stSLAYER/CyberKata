#!/usr/bin/env python3
"""Zero-dependency functional test for the CyberKata Hydra Lab."""

from __future__ import annotations

import http.client
import json
import socket
import subprocess
import sys
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def request(port: int, method: str, path: str, form: dict[str, str] | None = None):
    headers = {}
    body = None
    if form is not None:
        body = urllib.parse.urlencode(form)
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=4)
    connection.request(method, path, body=body, headers=headers)
    response = connection.getresponse()
    data = response.read().decode("utf-8", errors="replace")
    result = (response.status, dict(response.getheaders()), data)
    connection.close()
    return result


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    port = free_port()
    process = subprocess.Popen(
        [
            sys.executable,
            str(ROOT / "server.py"),
            "--port",
            str(port),
            "--no-browser",
        ],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    try:
        for _ in range(50):
            try:
                status, _, body = request(port, "GET", "/health")
                if status == 200 and "ready" in body:
                    break
            except OSError:
                time.sleep(0.1)
        else:
            output = process.stdout.read() if process.stdout else ""
            raise AssertionError("server did not become ready\n" + output)

        status, _, body = request(port, "GET", "/")
        require(
            status == 200
            and "HYDRA DOJO" in body
            and "HYDRA FIELD MANUAL" in body
            and "COPY-READY COMMANDS" in body,
            "homepage failed",
        )

        status, _, body = request(port, "GET", "/styles.css")
        require(status == 200 and "--pink" in body, "stylesheet failed")

        status, _, body = request(port, "GET", "/../server.py")
        require(status == 403 and "FORBIDDEN" in body, "path traversal was not blocked")

        cases = [
            ("1", "kata", "wrong", 200, "ACCESS_DENIED"),
            ("2", "wrong", "dojo-pass", 200, "UNKNOWN_OPERATOR"),
            ("3", "wrong", "wrong", 200, "INVALID_CREDENTIAL_PAIR"),
            ("4", "wrong", "wrong", 200, "AUTHENTICATION_FAILED_200"),
        ]
        for level, username, password, expected_status, marker in cases:
            status, _, body = request(
                port,
                "POST",
                f"/api/login/{level}",
                {"username": username, "password": password},
            )
            require(status == expected_status, f"level {level} failure status was {status}")
            require(marker in body, f"level {level} failure marker missing")

        valid = [
            ("1", "kata", "neonpulse", "CK{PASSWORD_HUNTER}"),
            ("2", "operator", "dojo-pass", "CK{USERNAME_FOUND}"),
            ("3", "admin", "nightshift42", "CK{PAIR_CRACKED}"),
        ]
        for level, username, password, flag in valid:
            status, _, body = request(
                port,
                "POST",
                f"/api/login/{level}",
                {"username": username, "password": password},
            )
            require(status == 200 and "ACCESS_GRANTED" in body, f"level {level} login failed")
            require(flag in body, f"level {level} flag missing")

        status, headers, body = request(
            port,
            "POST",
            "/api/login/4",
            {"username": "analyst", "password": "response302"},
        )
        require(status == 302, f"level 4 should redirect, got {status}")
        require(body == "", "level 4 redirect should have an empty body")
        location = headers.get("Location", "")
        require(location.startswith("/vault?"), "level 4 vault redirect missing")

        status, _, body = request(port, "GET", location)
        require(status == 200 and "HYDRA_DOJO_COMPLETE" in body, "vault marker missing")
        require("CK{RESPONSE_LOGIC_MASTERED}" in body, "level 4 flag missing")

        status, _, body = request(port, "GET", "/api/status")
        progress = json.loads(body)
        require(progress["completed"] == ["1", "2", "3", "4"], "progress tracking failed")

        def parallel_attempt(index: int) -> int:
            result, _, _ = request(
                port,
                "POST",
                "/api/login/3",
                {"username": f"test{index}", "password": "wrong"},
            )
            return result

        with ThreadPoolExecutor(max_workers=12) as pool:
            statuses = list(pool.map(parallel_attempt, range(36)))
        require(all(value == 200 for value in statuses), "parallel request handling failed")

        print("PASS: homepage and static files")
        print("PASS: traversal protection")
        print("PASS: four failure response patterns")
        print("PASS: four valid credential paths and flags")
        print("PASS: 302 vault redirect and success marker")
        print("PASS: Hydra-driven progress tracking")
        print("PASS: 36 concurrent attempts")
        return 0
    finally:
        process.terminate()
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            process.kill()


if __name__ == "__main__":
    raise SystemExit(main())
