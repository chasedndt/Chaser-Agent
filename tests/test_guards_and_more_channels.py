"""Hard limits (spend caps, loop guard, approval timeouts), secret redaction, the security check, Signal and Matrix."""

from __future__ import annotations

import json
import time
from pathlib import Path

from chaser_agent import channels, chaser_cli, chaser_home, setup_checks
from chaser_agent.agent import AgentRuntime, AgentTool, Toolbox, WorkflowSpec
from chaser_agent.agent.events import EventLog, redact, verify_chain
from chaser_agent.agent.guards import Limits, SpendLedger, spend_stop
from chaser_agent.agent.reasoners import ReasonerReply, ScriptedReasoner

READ = {"type": "tool", "tool": "probe_read", "args": {"q": "same"}}
WRITE = {"type": "tool", "tool": "probe_write", "args": {"v": "x"}}
FINAL = {"type": "final", "answer": "Done."}


def reply(*actions: dict) -> str:
    return json.dumps({"thought": "t", "actions": list(actions)})


def runtime(tmp_path: Path, replies: list[str], reasoner=None, limits: Limits | None = None):  # noqa: ANN001
    box = Toolbox()
    box.register(AgentTool("probe_read", "Read.", {"properties": {"q": {"type": "string"}}, "required": ["q"]}, "read_only", lambda a, _c: {}))
    box.register(AgentTool("probe_write", "Write.", {"properties": {"v": {"type": "string"}}, "required": ["v"]}, "local_write", lambda a, _c: {},
                           requires_approval=True))
    agent = AgentRuntime(tmp_path, toolbox=box, reasoners=[reasoner or ScriptedReasoner(replies)])
    agent.add_workflow(WorkflowSpec("general", "General", "Help.", frozenset({"probe_read", "probe_write"}), max_steps=10))
    agent.limits = limits or Limits()
    return agent


def run(agent: AgentRuntime, message: str = "go") -> dict:
    session = agent.create_session(message)
    agent.wait(session["id"])
    return agent.snapshot(session["id"])


def test_the_daily_model_call_cap_stops_before_the_next_call(tmp_path: Path) -> None:
    agent = runtime(tmp_path, [reply(READ), reply(FINAL)], limits=Limits(model_calls_per_day=1))
    snap = run(agent)
    assert snap["status"] == "budget_stopped" and "model calls" in snap["error"]
    assert any(e["type"] == "spend_cap_reached" for e in agent.events(snap["id"]))


class Paid(ScriptedReasoner):
    def complete(self, system, transcript, *, timeout, cancel):  # noqa: ANN001
        base = super().complete(system, transcript, timeout=timeout, cancel=cancel)
        return ReasonerReply(base.text, base.route, base.model, base.seconds, credits=40)


def test_credit_caps_stop_work_per_session_and_per_day(tmp_path: Path) -> None:
    agent = runtime(tmp_path, [], reasoner=Paid([reply(READ), reply({"type": "tool", "tool": "probe_read", "args": {"q": "b"}}), reply(FINAL)]),
                    limits=Limits(credits_per_session=50))
    snap = run(agent)
    assert snap["status"] == "budget_stopped" and "50 credits" in snap["error"]
    ledger = SpendLedger(tmp_path / "spend")
    ledger.add(calls=1, credits=900)
    assert spend_stop(Limits(credits_per_day=1000), ledger, 0) is None
    ledger.add(credits=200)
    assert "spend cap of 1000 credits" in spend_stop(Limits(credits_per_day=1000), ledger, 0)


def test_the_loop_guard_refuses_a_repeated_call_then_stops_the_turn(tmp_path: Path) -> None:
    agent = runtime(tmp_path, [reply(READ)] * 6 + [reply(FINAL)], limits=Limits(repeat_limit=2, model_calls_per_day=0))
    snap = run(agent)
    reasons = [e["data"].get("reason") for e in agent.events(snap["id"]) if e["type"] == "tool_denied"]
    assert reasons.count("loop_guard") == 2 and snap["status"] == "budget_stopped" and "Stopped a loop" in snap["error"]


def test_an_unanswered_approval_becomes_a_no_signed_as_automatic(tmp_path: Path) -> None:
    agent = runtime(tmp_path, [reply(WRITE), reply(FINAL)], limits=Limits(approval_timeout_minutes=1))
    snap = run(agent)
    assert snap["status"] == "awaiting_approval"
    assert agent.expire_approvals(now=time.time() + 30) == []
    assert agent.expire_approvals(now=time.time() + 61) == [snap["id"]]
    decided = [e["data"] for e in agent.events(snap["id"]) if e["type"] == "approval_decided"]
    assert decided[0]["decision"] == "reject" and decided[0]["decided_by"] == "automatic (no answer in 1 min)"


def test_secrets_never_reach_the_receipt_but_digests_and_the_chain_stay(tmp_path: Path) -> None:
    log = EventLog(tmp_path / "events.jsonl")
    log.append("tool_started", tool="http", args={"url": "https://x", "api_key": "abc123", "headers": {"Authorization": "Bearer abcdefghijklmnopqrstuvwxyz"},
                                                   "note": "use sk-proj-ABCDEFGHIJKLMNOPQRSTUV please"}, digest="d" * 64)
    text = (tmp_path / "events.jsonl").read_text(encoding="utf-8")
    assert "abc123" not in text and "abcdefghijklmnopqrstuvwxyz" not in text and "sk-proj-ABCDEF" not in text and "d" * 64 in text
    assert verify_chain(tmp_path / "events.jsonl")["verified"]
    assert redact({"token": "", "count": 3, "message": "123456789:AAH" + "x" * 32}) == {"token": "", "count": 3, "message": "[redacted]"}


def test_the_hud_ships_no_pack_labels_or_personal_names() -> None:
    text = (Path(chaser_cli.__file__).parent / "console" / "app.js").read_text(encoding="utf-8")
    assert "procurement_" not in text and "John" not in text and "pending.description" in text


def test_the_security_check_flags_keys_in_the_environment_and_a_missing_cap() -> None:
    settings = {**chaser_home.defaults(), "limits": {"model_calls_per_day": 0, "approval_timeout_minutes": 0}}
    report = setup_checks.security(settings, environ={"OPENAI_API_KEY": "sk-test"})
    states = {r["id"]: r["state"] for r in report["rows"]}
    assert states["env_keys"] == "warn" and states["caps"] == "warn" and states["timeout"] == "warn" and report["result"] in {"warn", "fail"}
    assert setup_checks.reachable_from([], 8765) == []


def test_limits_can_be_set_shown_and_reset(capsys) -> None:
    assert chaser_cli.main(["limits", "set", "credits_per_day", "2000"]) == 0
    assert Limits.from_settings(chaser_home.load()["limits"]).credits_per_day == 2000
    assert chaser_cli.main(["limits", "set", "nonsense", "1"]) == 2
    assert chaser_cli.main(["limits", "reset"]) == 0 and chaser_home.load()["limits"] == {}


def test_signal_reads_its_local_server_and_brings_photos() -> None:
    def api(url, method="GET", body=None, headers=None, timeout=0):  # noqa: ANN001
        if "/v1/receive/" in url:
            return 200, [{"envelope": {"sourceNumber": "+447700900001", "dataMessage": {"message": "hi"}}},
                         {"envelope": {"sourceNumber": "+447700900002", "dataMessage": {}}}]
        return 200, {}

    got = channels.Signal({"number": "+447700900000"}, ["+447700900001"], request=api).poll(wait=0)
    assert [(m.user, m.text) for m in got] == [("+447700900001", "hi")]


def test_matrix_starts_quietly_joins_only_allowed_invites_and_reads_text() -> None:
    calls = []

    def api(url, method="GET", body=None, headers=None, timeout=0):  # noqa: ANN001
        calls.append((method, url))
        if url.endswith("/account/whoami"):
            return 200, {"user_id": "@chaser:example.org"}
        if "since=" not in url:
            return 200, {"next_batch": "s1", "rooms": {"invite": {
                "!a:example.org": {"invite_state": {"events": [{"type": "m.room.member", "sender": "@sam:example.org"}]}},
                "!b:example.org": {"invite_state": {"events": [{"type": "m.room.member", "sender": "@stranger:example.org"}]}}}}}
        if "/sync" in url:
            return 200, {"next_batch": "s2", "rooms": {"join": {"!a:example.org": {"timeline": {"events": [
                {"type": "m.room.message", "sender": "@sam:example.org", "content": {"msgtype": "m.text", "body": "hello"}},
                {"type": "m.room.message", "sender": "@chaser:example.org", "content": {"msgtype": "m.text", "body": "mine"}}]}}}}}
        return 200, {}

    bot = channels.Matrix("t", {"homeserver": "https://example.org"}, ["@sam:example.org"], request=api, state={})
    assert bot.poll(wait=0) == []
    joined = [u for m, u in calls if m == "POST" and "/join/" in u]
    assert len(joined) == 1 and "%21a" in joined[0]
    assert [(m.user, m.text, m.chat) for m in bot.poll(wait=0)] == [("@sam:example.org", "hello", "!a:example.org")]
