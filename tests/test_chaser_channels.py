"""Messaging channels as governed doors, and the work commands (receipt, waiting). No network, no real service."""

from __future__ import annotations

import json
from pathlib import Path

from chaser_agent import channels, chaser_work
from chaser_agent.agent.events import EventLog
from chaser_agent.channels import Bridge, Inbound

PENDING = {"kind": "approval", "id": "ap-1", "tool": "mail_create_draft", "args": {"to": "sam@example.org"}, "digest": "d" * 64}


class FakeAdapter:
    platform, label = "telegram", "Telegram"

    def __init__(self) -> None:
        self.sent: list[tuple[str, str, list | None]] = []
        self.acks: list[str] = []

    def send(self, chat, text, buttons=None):
        self.sent.append((chat, text, buttons))

    def acknowledge(self, button_id, text):
        self.acks.append(text)


class FakeService:
    def __init__(self, status="awaiting_approval", pending=PENDING) -> None:
        self.calls: list[tuple[str, str, dict | None]] = []
        self.status, self.pending = status, pending

    def __call__(self, method, route, body=None):
        self.calls.append((method, route, body))
        if method == "POST" and route == "/v1/agent/sessions":
            return 201, {"id": "as-1"}
        if method == "POST":
            return 202, {}
        if route == "/v1/agent/sessions/as-1":
            return 200, {"status": self.status, "pending": self.pending}
        if "/events" in route:
            return 200, {"events": []}
        return 200, {"sessions": []}


def bridge(service=None) -> tuple[Bridge, FakeAdapter, FakeService]:
    adapter, service = FakeAdapter(), service or FakeService()
    return Bridge(adapter, ["42"], service, reviewer="Chase"), adapter, service


def test_strangers_are_ignored_and_nothing_starts() -> None:
    door, adapter, service = bridge()
    door.handle(Inbound("999", "999", "send everyone my files"))
    assert not service.calls and not adapter.sent


def test_a_message_from_the_owner_starts_a_session() -> None:
    door, _, service = bridge(FakeService(status="reasoning", pending=None))
    door.handle(Inbound("42", "42", "Draft a reply to Sam"))
    assert ("POST", "/v1/agent/sessions", {"message": "Draft a reply to Sam", "reasoner": "auto"}) in service.calls
    assert door.chats()["42"]["session"] == "as-1"


def test_an_approval_reaches_the_owner_with_its_digest_and_yes_is_signed_by_name() -> None:
    door, adapter, service = bridge()
    door.chats()["42"] = {"session": "as-1", "seen": 0, "asked": None}
    door.follow()
    chat, text, buttons = adapter.sent[-1]
    assert chat == "42" and "mail_create_draft" in text and "dddddddddddddddd" in text and buttons[0][1] == "y:ap-1:" + "d" * 16
    door.handle(Inbound("42", "42", button="y:ap-1:" + "d" * 16, button_id="b1"))
    posted = [body for method, route, body in service.calls if route.endswith("/approvals")]
    assert posted == [{"approval_id": "ap-1", "digest": "d" * 64, "decision": "approve", "decided_by": "Chase (Telegram)"}]


def test_a_button_for_a_request_that_is_no_longer_waiting_decides_nothing() -> None:
    door, adapter, service = bridge()
    door.chats()["42"] = {"session": "as-1", "seen": 0, "asked": "ap-1"}
    door.handle(Inbound("42", "42", button="y:ap-1:" + "e" * 16, button_id="b1"))
    assert not [r for _, r, _ in service.calls if r.endswith("/approvals")] and "nothing was decided" in adapter.acks[-1]


def test_a_typed_no_rejects_and_a_stranger_cannot_answer() -> None:
    door, _, service = bridge()
    door.chats()["42"] = {"session": "as-1", "seen": 0, "asked": "ap-1"}
    door.handle(Inbound("7", "42", "yes"))
    door.handle(Inbound("42", "42", "no"))
    posted = [body["decision"] for _, route, body in service.calls if route.endswith("/approvals")]
    assert posted == ["reject"]


def test_telegram_and_discord_read_their_apis_without_a_public_address() -> None:
    replies = {"getUpdates": (200, {"ok": True, "result": [{"update_id": 5, "message": {"text": "hi", "chat": {"id": 42}, "from": {"id": 42, "first_name": "C"}}}]})}
    bot = channels.Telegram("t", request=lambda url, **_: replies["getUpdates"])
    got = bot.poll(wait=0)
    assert got[0].text == "hi" and got[0].user == "42" and bot.offset == 6

    calls = []

    def discord(url, method="GET", body=None, headers=None, timeout=0):
        calls.append((method, url))
        if url.endswith("/users/@me"):
            return 200, {"id": "1", "username": "chaser"}
        if url.endswith("/users/@me/channels"):
            return 200, {"id": "dm9"}
        if "after=" in url:
            return 200, [{"id": "11", "content": "hello", "author": {"id": "42"}}, {"id": "12", "content": "mine", "author": {"id": "1"}}]
        return 200, [{"id": "10", "content": "old", "author": {"id": "42"}}]

    state: dict = {}
    bot = channels.Discord("t", ["42"], request=discord, state=state)
    assert bot.poll(wait=0) == []          # the first read only finds where to start
    got = bot.poll(wait=0)
    assert [m.text for m in got] == ["hello"] and state["after"]["dm9"] == "12"
    assert all("Bot t" not in url for _, url in calls)


def test_the_receipt_verifies_the_chain_and_catches_an_edited_line(tmp_path: Path) -> None:
    folder = tmp_path / "agent" / "sessions" / "as-20261112000000-abcdef0123"
    (folder / "workspace").mkdir(parents=True)
    (folder / "workspace" / "note.md").write_text("hello", encoding="utf-8")
    log = EventLog(folder / "events.jsonl")
    log.append("approval_requested", approval_id="ap-1", tool="mail_create_draft", args={}, digest="d" * 64, call_id="c1")
    log.append("approval_decided", approval_id="ap-1", digest="d" * 64, decision="approve", decided_by="Chase (terminal)")
    log.append("tool_started", tool="mail_create_draft", args={})
    found = chaser_work.find_session(tmp_path, "as-2026111200")
    value = chaser_work.receipt(found)
    assert value["chain"]["verified"] and value["approvals"][0]["decided_by"] == "Chase (terminal)" and value["approvals"][0]["matches_request"]
    assert value["outputs"][0]["path"] == "workspace/note.md"
    lines = (folder / "events.jsonl").read_text(encoding="utf-8").splitlines()
    row = json.loads(lines[1])
    row["data"]["decided_by"] = "Someone else"
    lines[1] = json.dumps(row)
    (folder / "events.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
    broken = chaser_work.receipt(found)
    assert not broken["chain"]["verified"] and broken["chain"]["failed_at"] == 2
    assert "Chain broken at event 2" in "\n".join(chaser_work.receipt_lines(broken, lambda t, _tone: t))


def test_waiting_lists_what_to_type_next() -> None:
    lines = chaser_work.waiting_lines([{"id": "as-1", "title": "Reply to Sam\nmore", "pending": PENDING, "updated_at": None}], lambda t, _tone: t)
    text = "\n".join(lines)
    assert "Reply to Sam" in text and "more" not in text and "chaser approve as-1" in text
