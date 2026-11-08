# CyberKata Hydra Lab — Hydra Dojo

A tiny, deliberately vulnerable web lab for learning Hydra on your own computer.
It contains four progressive login challenges and requires only Python 3.

> **Legal scope:** Use this lab only on a computer you own or are explicitly
> authorised to test. The server listens on `127.0.0.1` by default so it is not
> exposed to other devices.

## What you will learn

1. Test a password list against one known username.
2. Test a username list against one known password.
3. Combine username and password wordlists.
4. Identify valid credentials from HTTP status, redirect, and response content.

The web interface also includes an expandable **Hydra Field Manual** with the
most useful beginner flags, HTTP form syntax, explanations, and copy-ready
commands that automatically use the host and port you opened.

## Requirements

- Python 3.9 or newer
- Hydra, if you want to solve the challenges from the command line
- No Docker, Flask, pip packages, database, or administrator access

## Fastest setup: Kali or Linux

Open a terminal in this folder and run:

```bash
python3 server.py
```

The lab opens at <http://127.0.0.1:8080>. Keep that terminal open and use a
second terminal for Hydra.

You can also use the launcher:

```bash
sh START-LAB.sh
```

## Windows setup

1. Install Python 3 from <https://www.python.org/downloads/>.
2. During installation, select **Add Python to PATH**.
3. Extract this ZIP.
4. Double-click `START-LAB.bat`.

The browser should open automatically. To stop the lab, return to the terminal
window and press `Ctrl+C`.

## If Hydra runs inside a Kali virtual machine

The easiest option is to run both this lab and Hydra inside Kali. If you instead
run the lab on Windows and Hydra inside a VM:

1. Double-click `START-LAB-FOR-VM.bat`.
2. Read the IP address printed beside `VM target`.
3. Use that IP instead of `127.0.0.1` in Hydra.
4. Allow Python through the private-network firewall prompt if Windows asks.
5. Stop the lab as soon as training is complete.

VM mode listens on your local network. Use it only on a trusted network.

## Included files

```text
cyberkata-hydra-lab/
├── server.py
├── START-LAB.bat
├── START-LAB-FOR-VM.bat
├── START-LAB.sh
├── START-LAB-FOR-VM.sh
├── app/
├── wordlists/
│   ├── usernames.txt
│   ├── passwords.txt
│   └── credential-pairs.txt
└── solutions/
    └── INSTRUCTOR-GUIDE.md
```

## Useful checks

Confirm the server is ready:

```bash
curl http://127.0.0.1:8080/health
```

Inspect a failed Level 4 response:

```bash
curl -i -X POST http://127.0.0.1:8080/api/login/4 \
  -d "username=test&password=test"
```

Run the complete end-to-end suite with a real Hydra installation:

```bash
bash tests/hydra_e2e.sh
```

This launches an isolated lab server, runs all four documented commands plus the
combo-list example, verifies every recovered credential, and shuts the server
down automatically.

## Troubleshooting

### Port 8080 is already in use

Run the lab on another port:

```bash
python3 server.py --port 8081
```

Then replace `8080` with `8081` in your Hydra commands.

### The browser does not open

Open <http://127.0.0.1:8080> manually.

### Hydra cannot reach a Windows-hosted lab from Kali

Stop local mode and use the VM launcher. Make sure the VM network is configured
for NAT or bridged networking and use the `VM target` address printed by the lab.

## Resetting progress

Restarting the Python server resets server-side progress. Browser completion
markers are stored locally; clear site data for `127.0.0.1` if you want a fully
clean interface.

## Solutions

Try each level before opening `solutions/INSTRUCTOR-GUIDE.md`. The guide contains
the exact commands intended for the CyberKata video and should not be your first
stop.
