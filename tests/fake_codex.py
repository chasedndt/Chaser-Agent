"""Stands in for the Codex CLI in the route tests. FAKE_CODEX_MODE picks how it behaves.

It records the arguments and the names of the environment variables it was given, so a
test can prove the plan route hands it no API key and no ChaseOS Cloud key.
"""

import json
import os
import sys

args = sys.argv[1:]
mode = os.environ.get("FAKE_CODEX_MODE", "ok")
log = os.environ.get("FAKE_CODEX_LOG")
if log:
    with open(log, "a", encoding="utf-8") as stream:
        stream.write(json.dumps({"args": args, "env": sorted(os.environ)}) + "\n")
if args[:2] == ["login", "status"]:
    print("Logged in using an API key - sk-***" if mode == "apikey" else "Logged in using ChatGPT")
    sys.exit(0)
sys.stdin.read()
if mode == "limit":
    # What Codex prints when the plan is used up, plus a secret-looking string that must never reach a receipt.
    sys.stderr.write("ERROR: You've hit your usage limit. Try again later. session=plan-session-secret-7f3a\n")
    sys.exit(1)
if mode == "broken":
    sys.stderr.write("ERROR: something else went wrong. session=plan-session-secret-7f3a\n")
    sys.exit(1)
out = args[args.index("--output-last-message") + 1]
with open(out, "w", encoding="utf-8") as stream:
    stream.write(json.dumps({"thought": "on the plan", "actions": [{"type": "final", "answer": "Done on the ChatGPT plan."}]}))
