"""Permission modes (ask, plan, bypass, always-allow), images as context, and the email and Slack doors."""

from __future__ import annotations

import base64
import email
import json
from pathlib import Path

import pytest

from chaser_agent import channels, chaser_inputs
from chaser_agent.agent import AgentRuntime, AgentTool, Toolbox, WorkflowSpec
from chaser_agent.agent.events import verify_chain
from chaser_agent.agent.reasoners import ScriptedReasoner
from chaser_agent.agent_http import takes_images
from chaser_agent.chaser_chat import Chat

PNG = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==")


def reply(*actions: dict) -> str:
    return json.dumps({"thought": "t", "actions": list(actions)})


WRITE = {"type": "tool", "tool": "probe_write", "args": {"v": "x"}}
READ = {"type": "tool", "tool": "probe_read", "args": {"q": "x"}}
FINAL = {"type": "final", "answer": "Done."}


class Seeing(ScriptedReasoner):
    """Records what it was shown, including images, like a vision route would receive them."""

    sees_images = True

    def __init__(self, replies: list[str]) -> None:
        super().__init__(replies)
        self.shown: list[list[Path]] = []

    def complete(self, system, transcript, *, timeout, cancel, images=None):  # noqa: ANN001
        self.shown.append(list(images or []))
        return super().complete(system, transcript, timeout=timeout, cancel=cancel)


def runtime(tmp_path: Path, replies: list[str], reasoner=None):  # noqa: ANN001
    calls: list[dict] = []
    box = Toolbox()
    box.register(AgentTool("probe_read", "Read.", {"properties": {"q": {"type": "string"}}, "required": ["q"]}, "read_only", lambda a, _c: calls.append(a) or {}))
    box.register(AgentTool("probe_write", "Write.", {"properties": {"v": {"type": "string"}}, "required": ["v"]}, "local_write",
                           lambda a, _c: calls.append(a) or {}, requires_approval=True))
    reasoner = reasoner or ScriptedReasoner(replies)
    agent = AgentRuntime(tmp_path, toolbox=box, reasoners=[reasoner])
    agent.add_workflow(WorkflowSpec("general", "General", "Help.", frozenset({"probe_read", "probe_write"}), max_steps=6))
    return agent, calls


def events(agent: AgentRuntime, session_id: str) -> list[dict]:
    return agent.events(session_id)


def test_plan_mode_runs_reads_and_refuses_anything_that_changes(tmp_path: Path) -> None:
    agent, calls = runtime(tmp_path, [reply(READ), reply(WRITE), reply(FINAL)])
    session = agent.create_session("look", permission_mode="plan", set_by="Chase")
    agent.wait(session["id"])
    kinds = [(e["type"], e["data"].get("reason")) for e in events(agent, session["id"])]
    assert calls == [{"q": "x"}] and ("tool_denied", "plan_mode") in kinds
    assert agent.snapshot(session["id"])["status"] == "finished"


def test_bypass_says_yes_itself_and_the_receipt_says_so(tmp_path: Path) -> None:
    agent, calls = runtime(tmp_path, [reply(WRITE), reply(FINAL)])
    session = agent.create_session("go", permission_mode="bypass", set_by="Chase (terminal)")
    agent.wait(session["id"])
    rows = events(agent, session["id"])
    decided = [e["data"] for e in rows if e["type"] == "approval_decided"]
    assert calls == [{"v": "x"}] and decided[0]["decided_by"] == "automatic (bypass mode)" and decided[0]["automatic"] is True
    assert rows[0]["data"]["permission_mode"] == "bypass" and rows[0]["data"]["set_by"] == "Chase (terminal)"
    assert verify_chain(tmp_path / "agent" / "sessions" / session["id"] / "events.jsonl")["verified"]


def test_an_unknown_mode_is_refused(tmp_path: Path) -> None:
    agent, _ = runtime(tmp_path, [reply(FINAL)])
    with pytest.raises(ValueError):
        agent.create_session("go", permission_mode="yolo")


def test_always_allow_covers_the_rest_of_the_session_only(tmp_path: Path) -> None:
    agent, calls = runtime(tmp_path, [reply(WRITE), reply(WRITE), reply(FINAL)])
    session = agent.create_session("go")
    agent.wait(session["id"])
    pending = agent.snapshot(session["id"])["pending"]
    agent.decide(session["id"], pending["id"], pending["digest"], "approve", "Chase (terminal)", remember=True)
    agent.wait(session["id"])
    snap = agent.snapshot(session["id"])
    assert len(calls) == 2 and snap["always_allow"] == ["probe_write"] and snap["status"] == "finished"
    signers = [e["data"]["decided_by"] for e in events(agent, session["id"]) if e["type"] == "approval_decided"]
    assert signers == ["Chase (terminal)", "automatic (always allowed this session)"]


def test_the_mode_can_change_mid_session_and_is_recorded(tmp_path: Path) -> None:
    agent, _ = runtime(tmp_path, [reply(FINAL)])
    session = agent.create_session("go")
    agent.wait(session["id"])
    assert agent.set_permission_mode(session["id"], "plan", "Chase")["permission_mode"] == "plan"
    assert any(e["type"] == "permission_mode_changed" and e["data"]["mode"] == "plan" for e in events(agent, session["id"]))


def test_an_image_is_saved_hashed_noted_and_shown_to_a_route_that_sees(tmp_path: Path) -> None:
    seeing = Seeing([reply(FINAL)])
    agent, _ = runtime(tmp_path, [], reasoner=seeing)
    image = {"name": "shot.png", "media_type": "image/png", "data": base64.b64encode(PNG).decode()}
    session = agent.create_session("what is this?", images=[image])
    agent.wait(session["id"])
    attached = [e["data"] for e in events(agent, session["id"]) if e["type"] == "image_attached"][0]
    saved = tmp_path / "agent" / "sessions" / session["id"] / attached["path"]
    assert saved.read_bytes() == PNG and attached["bytes"] == len(PNG) and len(attached["sha256"]) == 64
    assert seeing.shown[0] == [saved]


def test_images_are_checked_before_anything_is_saved(tmp_path: Path) -> None:
    agent, _ = runtime(tmp_path, [reply(FINAL)])
    with pytest.raises(ValueError):
        agent.create_session("x", images=[{"name": "a.exe", "media_type": "application/x-msdownload", "data": "AA=="}])
    with pytest.raises(ValueError):
        agent.create_session("x", images=[{"name": "big.png", "media_type": "image/png", "data": base64.b64encode(b"0" * (3 * 1024 * 1024 + 1)).decode()}])


def test_only_image_carrying_routes_get_the_larger_body_limit() -> None:
    assert takes_images("/v1/agent/sessions") and takes_images("/v1/agent/sessions/as-20261112000000-abcdef0123/messages")
    assert not takes_images("/v1/agent/sessions/as-20261112000000-abcdef0123/approvals") and not takes_images("/v1/agent/setup/key")


def test_a_dragged_image_path_attaches_and_leaves_the_words(tmp_path: Path) -> None:
    picture = tmp_path / "receipt photo.png"
    picture.write_bytes(PNG)
    text, images = chaser_inputs.split_dropped(f'what does this say "{picture}"')
    assert text == "what does this say" and images[0]["name"] == "receipt photo.png"
    with pytest.raises(ValueError):
        chaser_inputs.load_image(tmp_path / "missing.png")


def test_bypass_in_chat_needs_the_word_typed(tmp_path: Path) -> None:
    out = []
    chat = Chat({"data_dir": str(tmp_path), "port": 1, "reviewer": "Chase"}, lambda t, _tone: t, call=lambda *a, **k: (202, {}),
                ask=lambda _p: "yes", out=type("O", (), {"write": lambda self, t: out.append(t), "flush": lambda self: None})())
    chat.set_mode("bypass")
    assert chat.mode == "ask"
    chat.ask = lambda _p: "bypass"
    chat.set_mode("bypass")
    assert chat.mode == "bypass"


def _mail(sender: str, auth: str, body: str = "Please summarise my week") -> email.message.Message:
    return email.message_from_string(f"From: Chase <{sender}>\nAuthentication-Results: mx.example.net; {auth}\nSubject: hi\n\n{body}")


def test_email_counts_a_sender_only_when_their_server_vouches() -> None:
    assert channels.sender_vouched(_mail("chase@example.org", "dkim=pass header.d=example.org"), "chase@example.org")
    assert channels.sender_vouched(_mail("chase@example.org", "spf=pass smtp.mailfrom=chase@example.org"), "chase@example.org")
    assert not channels.sender_vouched(_mail("chase@example.org", "dkim=pass header.d=attacker.net"), "chase@example.org")
    assert not channels.sender_vouched(_mail("chase@example.org", "spf=fail smtp.mailfrom=chase@example.org"), "chase@example.org")


def test_an_email_approval_must_name_the_request() -> None:
    from tests.test_chaser_channels import FakeService  # noqa: PLC0415

    class Mail:
        platform, label = "email", "Email"

        def __init__(self):
            self.sent = []

        def send(self, chat, text, buttons=None):
            self.sent.append(text)

        def acknowledge(self, *_a):
            return None

    adapter, service = Mail(), FakeService()
    door = channels.Bridge(adapter, ["chase@example.org"], service, reviewer="Chase")
    door.chats()["chase@example.org"] = {"session": "as-1", "seen": 0, "asked": "ap-1"}
    door.handle(channels.Inbound("chase@example.org", "chase@example.org", "yes"))
    assert not [r for _, r, _ in service.calls if r.endswith("/approvals")] and "yes dddddddd" in adapter.sent[-1]
    door.handle(channels.Inbound("chase@example.org", "chase@example.org", "yes dddddddd"))
    posted = [b for _, r, b in service.calls if r.endswith("/approvals")]
    assert posted and posted[0]["decided_by"] == "Chase (Email)"
    door.handle(channels.Inbound("unverified:chase@example.org", "chase@example.org", "send it all"))
    assert len([r for _, r, _ in service.calls if r.endswith("/approvals")]) == 1


def test_slack_reads_only_the_allowed_persons_new_messages() -> None:
    def api(url, method="GET", body=None, headers=None, timeout=0):  # noqa: ANN001
        if url.endswith("auth.test"):
            return 200, {"ok": True, "user_id": "UBOT", "user": "chaser", "team": "T"}
        if url.endswith("conversations.open"):
            return 200, {"ok": True, "channel": {"id": "D1"}}
        if "oldest=" in url:
            return 200, {"ok": True, "messages": [{"ts": "2.0", "user": "U42", "text": "hi"}, {"ts": "3.0", "user": "UBOT", "bot_id": "B", "text": "me"}]}
        return 200, {"ok": True, "messages": [{"ts": "1.0", "user": "U42", "text": "old"}]}

    bot = channels.Slack("xoxb-test", ["U42"], request=api, state={})
    assert bot.poll(wait=0) == []
    assert [m.text for m in bot.poll(wait=0)] == ["hi"]


def test_a_photo_from_telegram_arrives_as_an_image(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(channels, "_download", lambda url, headers=None: PNG)
    update = {"update_id": 1, "message": {"photo": [{"file_id": "s"}, {"file_id": "big"}], "caption": "what is this", "chat": {"id": 42}, "from": {"id": 42}}}

    def api(url, **_):  # noqa: ANN001
        return (200, {"ok": True, "result": {"file_path": "photos/a.jpg"}}) if "getFile" in url else (200, {"ok": True, "result": [update]})

    got = channels.Telegram("t", request=api).poll(wait=0)
    assert got[0].text == "what is this" and got[0].images[0]["media_type"] == "image/jpeg"


def test_the_kill_switch_cancels_only_working_or_waiting_sessions() -> None:
    from chaser_agent.chaser_work import stop_everything

    calls = []

    def service(method, route, body=None):  # noqa: ANN001
        calls.append((method, route))
        if method == "GET":
            return 200, {"sessions": [{"id": "a", "status": "running_tool"}, {"id": "b", "status": "awaiting_approval"}, {"id": "c", "status": "finished"}]}
        return 202, {}

    assert stop_everything(service) == ["a", "b"] and ("POST", "/v1/agent/sessions/c/cancel") not in calls
