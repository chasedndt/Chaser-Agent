"""`chaser chat`: talk to Chaser in the terminal and watch it work.

Each step streams in as Chaser takes it, from the same hash-chained event log the HUD reads. Questions
are answered inline. An approval shows the exact request and its digest, and your yes or no is signed
with your name, so the receipt says who decided. Ctrl+C stops the current task, not the chat.

Slash commands: /help /new /sessions /waiting /open /status /route /stop /checks /quit
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from typing import Any, Callable

from chaser_agent import chaser_home, setup_checks, terminal_theme

ACTIVE = {"queued", "reasoning", "running_tool"}
WAITING = {"awaiting_human", "awaiting_approval"}
DONE = {"finished", "failed", "cancelled", "budget_stopped", "interrupted"}
STATUS_WORDS = {"finished": "Finished", "failed": "Stopped", "cancelled": "Cancelled", "budget_stopped": "Used its budget", "interrupted": "Interrupted"}
HELP = [
    ("/new", "start a fresh conversation"),
    ("/sessions", "earlier work; pick one to carry on"),
    ("/waiting", "what's waiting for your answer"),
    ("/open", "open the HUD"),
    ("/status", "Chaser's service and how it thinks"),
    ("/route [name]", "how new work thinks: auto or one of the routes /status lists"),
    ("/receipt [id]", "check this session's hash chain and who approved what"),
    ("/stop", "stop the current task"),
    ("/checks", "run the pre-flight checks"),
    ("/quit", "leave the chat; Chaser keeps running"),
]


class Chat:
    def __init__(self, settings: dict[str, Any], paint: Callable[[str, str], str], *, call=None, ask=input, out=sys.stdout,
                 poll: float = 0.8, sleep: Callable[[float], None] = time.sleep) -> None:
        self.settings, self.paint, self.ask, self.out, self.poll, self.sleep = settings, paint, ask, out, poll, sleep
        self.call = call or self._service_call
        self.session: str | None = None
        self.seen = 0
        self.route = "auto"
        reviewer = (settings.get("reviewer") or "").strip()
        self.decided_by = f"{reviewer} (terminal)" if reviewer else None

    def _service_call(self, method: str, path: str, body: dict[str, Any] | None = None) -> tuple[int, Any]:
        from chaser_agent import agent_cli

        return agent_cli._call(argparse.Namespace(data_dir=str(self.settings["data_dir"]), port=int(self.settings["port"])), method, path, body)

    def say(self, text: str = "", tone: str | None = None) -> None:
        self.out.write((self.paint(text, tone) if tone else text) + "\n")
        self.out.flush()

    @property
    def colour(self) -> bool:
        return self.paint("x", "dim") != "x"

    def card(self, lines: list[str], *, title: str = "", tone: str = "line") -> None:
        """A framed block: the banner, a question or an approval."""
        import shutil

        width = min(shutil.get_terminal_size((96, 30)).columns - 4, 92)
        if not self.colour:
            for line in ([title] if title else []) + lines:
                self.say("  " + line)
            return
        for line in terminal_theme.box(lines, width, title=title, colour=True, full=terminal_theme.truecolor(), tone=tone):
            self.say("  " + line)

    # --- Showing events ---------------------------------------------------------------------

    def show(self, event: dict[str, Any]) -> None:
        data, kind = event.get("data") or {}, event.get("type")
        if kind == "reasoner_reply" and data.get("thought"):
            thought = " ".join(str(data["thought"]).split())
            self.say(f"  {self.paint('⋯', 'sage')} {self.paint(thought[:240] + ('…' if len(thought) > 240 else ''), 'dim')}")
        elif kind == "tool_started" and data.get("tool") != "update_plan":
            args = data.get("args") or {}
            hint = next((str(args[k]) for k in ("query", "path", "url", "name", "title", "id") if k in args), "")
            self.say(f"  {self.paint('●', 'teal')} {self.paint(str(data.get('tool')), 'text')}{self.paint('  ' + hint[:80], 'dim') if hint else ''}")
        elif kind == "tool_finished" and data.get("status") not in (None, "ok", "succeeded", "done"):
            self.say(f"  {self.paint('✗', 'fail')} {data.get('tool')}: {data.get('status')}")
        elif kind == "tool_denied":
            self.say(f"  {self.paint('✗ refused', 'fail')} {data.get('tool')}: {data.get('message') or data.get('reason')}")
        elif kind == "reply_rejected":
            self.say(f"  {self.paint('✗', 'fail')} A reply outside the rules ({data.get('reason')}). Nothing ran.")
        elif kind == "approval_decided":
            said = self.paint("✓ yes", "ok") if data.get("decision") == "approve" else self.paint("✗ no", "fail")
            self.say(f"  {said}  {self.paint('signed ' + str(data.get('decided_by') or 'local_operator') + ' · in the receipt', 'dim')}")
        elif kind == "turn_finished":
            if data.get("answer"):
                self.say("")
                self.say(f"  {self.paint('Chaser', 'key')}")
                for line in str(data["answer"]).splitlines() or [""]:
                    self.say(f"  {line}", "text")
            elif data.get("error"):
                self.say(f"  {data['error']}", "fail")

    def follow(self) -> str:
        """Stream the session until it finishes or needs you. Returns the status it stopped on."""
        while True:
            status, page = self.call("GET", f"/v1/agent/sessions/{self.session}/events?after={self.seen}")
            if status != 200:
                self.say(f"  Lost contact with Chaser: {self._error(page)}", "fail")
                return "lost"
            for event in page.get("events", []):
                self.seen = event["seq"]
                self.show(event)
            _, snapshot = self.call("GET", f"/v1/agent/sessions/{self.session}")
            state = snapshot.get("status")
            if state in WAITING and snapshot.get("pending"):
                if not self.answer(snapshot["pending"]):
                    return state
                continue
            if state in DONE and not page.get("events"):
                mark = "✓" if state == "finished" else "!"
                self.say(self.paint(f"  {mark} {STATUS_WORDS.get(state, state)}", "ok" if state == "finished" else "warn")
                         + self.paint(f"  · /receipt shows the proof", "dim"))
                return state
            self.sleep(self.poll)

    def answer(self, pending: dict[str, Any]) -> bool:
        """Answer a question or approval inline. False if you'd rather leave it for later."""
        if pending.get("kind") == "question":
            self.say("")
            options = pending.get("options") or []
            self.card([self.paint(str(pending.get("question")), "head"), *(f"{self.paint(str(n), 'key')}  {o}" for n, o in enumerate(options, 1))],
                      title=self.paint("Chaser asks", "warn"), tone="warn")
            reply = self.ask(self.paint("  ❯ ", "warn") + self.paint("your answer, a number, or Enter for later  ", "dim")).strip()
            if not reply:
                return False
            if reply.isdecimal() and 1 <= int(reply) <= len(options):
                reply = options[int(reply) - 1]
            status, value = self.call("POST", f"/v1/agent/sessions/{self.session}/answers", {"question_id": pending["id"], "answer": reply})
        else:
            self.say("")
            args = json.dumps(pending.get("args") or {}, ensure_ascii=False, indent=1).splitlines()
            body = [f"wants to run {self.paint(str(pending.get('tool')), 'head')} with exactly this:", *(self.paint("  " + line[:84], "dim") for line in args[:20])]
            if len(args) > 20:
                body.append(self.paint(f"  … {len(args) - 20} more lines in the HUD", "dim"))
            signed = self.decided_by or "local_operator (set your name: chaser setup name)"
            body += ["", self.paint(f"digest {str(pending.get('digest'))[:24]}…   signed {signed}", "dim")]
            self.card(body, title=self.paint("Needs your yes", "warn"), tone="warn")
            reply = self.ask(self.paint("  ❯ ", "warn") + self.paint("y", "key") + self.paint(" yes   ", "dim") + self.paint("n", "key")
                             + self.paint(" no   ", "dim") + self.paint("enter", "key") + self.paint(" later  ", "dim")).strip().lower()
            if reply not in {"y", "yes", "n", "no"}:
                return False
            body = {"approval_id": pending["id"], "digest": pending["digest"], "decision": "approve" if reply.startswith("y") else "reject"}
            if self.decided_by:
                body["decided_by"] = self.decided_by
            status, value = self.call("POST", f"/v1/agent/sessions/{self.session}/approvals", body)
        if status != 202:
            self.say(f"  That didn't go through: {self._error(value)}", "fail")
            return False
        return True

    @staticmethod
    def _error(value: Any) -> str:
        return ((value or {}).get("error") or {}).get("message") or "no answer" if isinstance(value, dict) else str(value)

    # --- Sending and commands ---------------------------------------------------------------------

    def send(self, message: str) -> str:
        if self.session:
            status, value = self.call("POST", f"/v1/agent/sessions/{self.session}/messages", {"message": message})
            if status == 409:
                self.say("  Chaser is still on the last task. Answer it, or /stop first.", "warn")
                return "busy"
        else:
            status, value = self.call("POST", "/v1/agent/sessions", {"message": message, "reasoner": self.route})
            if status == 201:
                self.session, self.seen = value["id"], 0
        if status not in {201, 202}:
            self.say(f"  Chaser couldn't start that: {self._error(value)}", "fail")
            return "error"
        try:
            return self.follow()
        except KeyboardInterrupt:
            self.say("")
            self.stop()
            return "cancelled"

    def stop(self) -> None:
        if not self.session:
            self.say("  Nothing is running.", "dim")
            return
        status, _ = self.call("POST", f"/v1/agent/sessions/{self.session}/cancel", {})
        self.say("  Stopped Chaser's task. The chat is still open." if status == 202 else "  Nothing to stop.", "warn")

    def pick(self, sessions: list[dict[str, Any]]) -> None:
        if not sessions:
            self.say("  Nothing yet.", "dim")
            return
        for number, row in enumerate(sessions[:12], 1):
            self.say(f"  {number:>2}. {row.get('title')}  {self.paint(row.get('status', ''), 'dim')}")
        choice = self.ask("  carry on with which? (Enter for none) › ").strip()
        if choice.isdecimal() and 1 <= int(choice) <= min(len(sessions), 12):
            chosen = sessions[int(choice) - 1]
            _, snapshot = self.call("GET", f"/v1/agent/sessions/{chosen['id']}")
            self.session, self.seen = chosen["id"], max(0, int(snapshot.get("events") or 0) - 1)
            self.say(f"  Carrying on with: {chosen.get('title')}", "teal")
            if snapshot.get("pending") or snapshot.get("status") in ACTIVE:
                self.follow()

    def command(self, line: str) -> bool:
        """Run a slash command. False means leave the chat."""
        name, _, rest = line[1:].partition(" ")
        name = name.lower()
        if name in {"quit", "exit", "q"}:
            return False
        if name in {"help", "?"}:
            for command, text in HELP:
                self.say(f"  {self.paint(f'{command:<16}', 'teal')} {text}")
        elif name == "new":
            self.session, self.seen = None, 0
            self.say("  Fresh conversation. Say what you need.", "dim")
        elif name in {"sessions", "recent"}:
            _, value = self.call("GET", "/v1/agent/sessions")
            self.pick((value or {}).get("sessions") or [])
        elif name == "waiting":
            _, value = self.call("GET", "/v1/agent/sessions")
            self.pick([row for row in (value or {}).get("sessions") or [] if row.get("status") in WAITING])
        elif name == "open":
            from chaser_agent import agent_cli

            agent_cli.run_open(argparse.Namespace(data_dir=str(self.settings["data_dir"]), port=int(self.settings["port"])))
        elif name == "status":
            _, value = self.call("GET", "/v1/agent/status")
            if not ((value or {}).get("reasoners") or {}).get("routes"):
                self.sleep(2)  # routes are checked in the background the first time anyone asks
                _, value = self.call("GET", "/v1/agent/status")
            for route in ((value or {}).get("reasoners") or {}).get("routes") or []:
                ready = route.get("available") and route.get("connected", True) is not False
                self.say(f"  {self.paint('✓' if ready else '·', 'ok' if ready else 'dim')} {route.get('label')}: {'ready' if ready else route.get('reason') or 'not available'}")
            self.say(f"  New work thinks with: {self.route}", "dim")
        elif name == "route":
            choice = rest.strip()
            if choice:
                self.route = choice
            if not choice:
                _, value = self.call("GET", "/v1/agent/status")
                names = [r.get("id") for r in ((value or {}).get("reasoners") or {}).get("routes") or [] if r.get("id")]
                self.say(f"  New work thinks with: {self.route}. Choose with /route " + ", ".join(["auto", *names]), "dim")
            else:
                self.say(f"  New work thinks with: {self.route}", "dim")
        elif name == "receipt":
            from chaser_agent import chaser_work
            from pathlib import Path

            folder = chaser_work.find_session(Path(self.settings["data_dir"]), rest.strip() or self.session)
            if folder is None:
                self.say("  No session yet. Ask Chaser something first, or name one: /receipt as-…", "dim")
            else:
                for line in chaser_work.receipt_lines(chaser_work.receipt(folder), self.paint):
                    self.say(line)
        elif name == "stop":
            self.stop()
        elif name in {"checks", "doctor"}:
            for row in setup_checks.run(self.settings)["rows"]:
                self.say(f"  {row['title']}: {row['detail']}")
        else:
            self.say(f"  No command /{name}. Try /help.", "dim")
        return True

    def run(self, first: str | None = None) -> int:
        from chaser_agent import terminal_art

        from chaser_agent import model_providers

        thinks = model_providers.describe(self.settings) if self.settings.get("provider") else "picked automatically"
        words = [terminal_theme.wordmark(colour=self.colour, full=terminal_theme.truecolor()) + self.paint("  chat", "dim"), "",
                 self.paint(f"{'Thinks with':<12}", "dim") + self.paint(thinks, "text"),
                 self.paint(f"{'Signs as':<12}", "dim") + self.paint(self.decided_by or "local_operator", "text"), "",
                 self.paint("/help", "teal") + self.paint(" commands   ", "dim") + self.paint("ctrl+c", "teal") + self.paint(" stops the task   ", "dim")
                 + self.paint("/quit", "teal") + self.paint(" leaves", "dim")]
        self.card(terminal_art.beside(words, self.colour) if terminal_art.enabled(self.colour) else words)
        if not self.decided_by:
            self.say("  Approvals will be signed local_operator. Set your name with: chaser setup name", "dim")
        if first:
            self.say(f"{self.paint('❯', 'teal')} {first}")
            self.send(first)
        while True:
            try:
                line = self.ask("\n" + self.paint("❯ ", "teal")).strip()
            except (EOFError, KeyboardInterrupt):
                self.say("")
                return 0
            if not line:
                continue
            if line.startswith("/"):
                if not self.command(line):
                    return 0
                continue
            self.send(line)


def run(args: argparse.Namespace, paint: Callable[[str, str], str]) -> int:
    settings = chaser_home.load()
    health = setup_checks.gateway_health(int(settings["port"]))
    if not (health and health.get("service") == "chaser-agent" and health.get("agent") == "ready"):
        print("Chaser isn't running. Start it with: chaser gateway")
        return 1
    chat = Chat(settings, paint)
    if getattr(args, "route", None):
        chat.route = args.route
    if getattr(args, "session", None):
        chat.session = args.session
        _, snapshot = chat.call("GET", f"/v1/agent/sessions/{args.session}")
        chat.seen = max(0, int((snapshot or {}).get("events") or 0) - 1)
    first = " ".join(getattr(args, "message", None) or []) or None
    return chat.run(first)
