"""The terminal side: the menu, chat, the supervisor and starting at sign-in. No real model, no registry writes."""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import pytest

from chaser_agent import agent_cli, chaser_home, gateway_service, setup_checks, terminal_ui
from chaser_agent.chaser_chat import Chat


# --- The menu ------------------------------------------------------------------

def test_the_menu_marks_the_chosen_item_and_never_waits_without_a_console() -> None:
    items = [terminal_ui.Item("c", "Chat with Chaser"), terminal_ui.Item("s", "Settings", "key, folder")]
    text = terminal_ui.render("Chaser Agent", items, 1, ["● running"], lambda t, _tone: t)
    assert "› s  Settings" in text and "  c  Chat with Chaser" in text and "key, folder" in text and "● running" in text
    assert terminal_ui.select("Chaser Agent", items, interactive=False) is None


def test_the_hud_window_is_found_by_its_short_and_old_titles() -> None:
    assert agent_cli.is_hud_title("Chaser") and agent_cli.is_hud_title("Needs your yes · Chaser")
    assert agent_cli.is_hud_title("Chaser Agent") and not agent_cli.is_hud_title("Chaser notes - Notepad")


# --- Chat ---------------------------------------------------------------------

class FakeService:
    """Answers like the service for one session that asks, then wants approval, then finishes."""

    def __init__(self) -> None:
        self.posts: list[tuple[str, dict]] = []
        self.stage = 0

    def __call__(self, method: str, path: str, body=None):
        if method == "POST":
            self.posts.append((path, body))
            if path == "/v1/agent/sessions":
                return 201, {"id": "as-1", "events": 0}
            self.stage += 1
            return 202, {}
        if "/events" in path:
            events = {0: [{"seq": 1, "type": "reasoner_reply", "data": {"thought": "Reading first."}},
                          {"seq": 2, "type": "tool_started", "data": {"tool": "read_document", "args": {"path": "brief.md"}}}],
                      2: [{"seq": 3, "type": "turn_finished", "data": {"status": "finished", "answer": "Done, nothing was sent."}}]}
            return 200, {"events": events.get(self.stage, []) if self.stage != 2 or not getattr(self, "_told", False) else []}
        if path == "/v1/agent/sessions/as-1":
            if self.stage == 0:
                return 200, {"status": "awaiting_human", "pending": {"kind": "question", "id": "q1", "question": "Which colour?", "options": ["Blue", "Green"]}}
            if self.stage == 1:
                return 200, {"status": "awaiting_approval", "pending": {"kind": "approval", "id": "a1", "tool": "mail_create_draft", "args": {"to": "sam@example.org"}, "digest": "d" * 64}}
            told, self._told = getattr(self, "_told", False), True
            return 200, {"status": "finished", "pending": None} if told else {"status": "reasoning", "pending": None}
        return 404, {}


def test_chat_answers_questions_and_signs_approvals_with_your_name() -> None:
    out, replies, service = io.StringIO(), iter(["2", "y"]), FakeService()
    chat = Chat({"reviewer": "Sam", "data_dir": "x", "port": 1}, lambda t, _tone: t, call=service, ask=lambda _p: next(replies), out=out, sleep=lambda _s: None)
    assert chat.send("Draft the reply") == "finished"
    answer, approval = service.posts[1], service.posts[2]
    assert answer == ("/v1/agent/sessions/as-1/answers", {"question_id": "q1", "answer": "Green"})
    assert approval[1] == {"approval_id": "a1", "digest": "d" * 64, "decision": "approve", "decided_by": "Sam (terminal)"}
    text = out.getvalue()
    assert "Reading first." in text and "read_document" in text and "sam@example.org" in text and "Done, nothing was sent." in text


def test_leaving_an_approval_for_later_sends_nothing() -> None:
    service = FakeService()
    service.stage = 1
    chat = Chat({"reviewer": "", "data_dir": "x", "port": 1}, lambda t, _tone: t, call=service, ask=lambda _p: "", out=io.StringIO(), sleep=lambda _s: None)
    chat.session = "as-1"
    assert chat.follow() == "awaiting_approval" and service.posts == []


def test_slash_commands_switch_route_start_fresh_and_quit() -> None:
    out = io.StringIO()
    chat = Chat({"reviewer": "", "data_dir": "x", "port": 1}, lambda t, _tone: t, call=lambda *a: (200, {}), ask=lambda _p: "", out=out, sleep=lambda _s: None)
    chat.session = "as-9"
    assert chat.command("/route chaseos-cloud") and chat.route == "chaseos-cloud"
    assert chat.command("/new") and chat.session is None
    assert chat.command("/nonsense") and "Try /help" in out.getvalue()
    assert chat.command("/quit") is False


# --- The supervisor -----------------------------------------------------------

def test_the_supervisor_restarts_a_service_that_stops_and_cleans_up(tmp_path: Path) -> None:
    settings = {"data_dir": str(tmp_path), "port": 1}
    waits: list[float] = []
    restarts = gateway_service.supervise(settings, max_restarts=2, sleep=waits.append, command=[sys.executable, "-c", "import sys; sys.exit(3)"])
    log = (tmp_path / "service.log").read_text(encoding="utf-8")
    assert restarts == 2 and log.count("the service stopped (code 3)") == 3
    assert [w for w in waits if w >= 1] == [2, 5]  # waits grow while it keeps failing
    assert not any((tmp_path / name).exists() for name in (gateway_service.SUPERVISOR_PID, gateway_service.SERVICE_PID, gateway_service.STOP_FILE))


def test_a_stop_request_ends_the_supervisor_without_a_restart(tmp_path: Path) -> None:
    settings = {"data_dir": str(tmp_path), "port": 1}

    def stop_soon(_seconds: float) -> None:
        (tmp_path / gateway_service.STOP_FILE).write_text("stop", encoding="ascii")

    restarts = gateway_service.supervise(settings, sleep=stop_soon, command=[sys.executable, "-c", "import time; time.sleep(30)"])
    assert restarts == 0 and "stopped on request" in (tmp_path / "service.log").read_text(encoding="utf-8")


class FakeRegistry:
    HKEY_CURRENT_USER, KEY_SET_VALUE, REG_SZ = object(), 2, 1

    def __init__(self) -> None:
        self.values: dict[str, str] = {}

    class _Key:
        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

    def OpenKey(self, *_args):  # noqa: N802
        return self._Key()

    CreateKey = OpenKey  # noqa: N815

    def QueryValueEx(self, _key, name):  # noqa: N802
        if name not in self.values:
            raise FileNotFoundError(name)
        return self.values[name], self.REG_SZ

    def SetValueEx(self, _key, name, _reserved, _kind, value):  # noqa: N802
        self.values[name] = value

    def DeleteValue(self, _key, name):  # noqa: N802
        del self.values[name]


@pytest.mark.skipif(sys.platform != "win32", reason="starting at sign-in is set up on Windows")
def test_starting_at_sign_in_runs_the_supervisor_without_a_window(monkeypatch: pytest.MonkeyPatch) -> None:
    registry = FakeRegistry()
    monkeypatch.setitem(sys.modules, "winreg", registry)
    assert gateway_service.installed() is None
    command = gateway_service.install()
    assert command.endswith("-m chaser_agent gateway run") and registry.values[gateway_service.RUN_VALUE] == command
    assert gateway_service.installed() == command
    assert gateway_service.uninstall() and gateway_service.installed() is None and not gateway_service.uninstall()


def test_following_a_log_prints_its_end_then_new_lines(tmp_path: Path) -> None:
    log = tmp_path / "service.log"
    log.write_text("one\ntwo\nthree\n", encoding="utf-8")
    out = io.StringIO()
    calls = {"n": 0}

    def tick(_seconds: float) -> None:
        calls["n"] += 1
        if calls["n"] == 1:
            with open(log, "a", encoding="utf-8") as stream:
                stream.write("four\n")
        else:
            raise KeyboardInterrupt

    import chaser_agent.gateway_service as module

    original = module.time.sleep
    module.time.sleep = tick
    try:
        with pytest.raises(KeyboardInterrupt):
            gateway_service.follow([log], lines=2, out=out)
    finally:
        module.time.sleep = original
    assert out.getvalue() == "two\nthree\nfour\n"


# --- ChaseOS, if this computer has it -----------------------------------------

def test_an_existing_chaseos_setup_is_found_and_offered(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "operations").mkdir()
    (tmp_path / "operations" / "chaser-agent-service.json").write_text(json.dumps(
        {"data_dir": "D:\\chaser", "port": 8765, "pack": "D:\\pack.py", "memory_limit_mb_per_process": 1500}), encoding="utf-8")
    monkeypatch.setenv("CHASEOS_ROOT", str(tmp_path))
    found = chaser_home.detect_chaseos()
    assert found["data_dir"] == "D:\\chaser" and found["packs"] == ["D:\\pack.py"] and found["port"] == 8765


def test_the_checks_use_the_services_own_sign_in_check(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(setup_checks.shutil, "which", lambda _name: "C:\\claude.exe")
    routes = [{"id": "claude-cli", "available": False, "reason": "This machine's claude CLI is not logged in."},
              {"id": "chaseos-cloud", "available": False}]
    rows = {r["id"]: r for r in setup_checks.run(chaser_home.load(), environ={}, routes=routes)["rows"]}
    assert rows["claude_code"]["state"] == "warn" and "not logged in" in rows["claude_code"]["detail"]
    assert rows["routes"]["state"] == "fail"


def test_a_key_held_by_the_running_service_counts_as_added() -> None:
    routes = [{"id": "chaseos-cloud", "available": True}, {"id": "claude-cli", "available": False, "reason": "not logged in"}]
    rows = {r["id"]: r for r in setup_checks.run(chaser_home.load(), environ={}, routes=routes)["rows"]}
    assert rows["cloud_key"]["state"] == "ok" and rows["cloud_key"]["detail"] == "In use by the running Chaser"
    assert rows["routes"]["detail"] == "ChaseOS Cloud"


# --- Chaser in pixels -----------------------------------------------------------

def test_the_pixel_art_comes_from_the_approved_avatar_export() -> None:
    import hashlib

    from chaser_agent import chaser_art

    source = Path(__file__).resolve().parents[1] / chaser_art.SOURCE
    assert "canon-core" in chaser_art.SOURCE and hashlib.sha256(source.read_bytes()).hexdigest() == chaser_art.SOURCE_SHA256
    assert len({len(row) for row in chaser_art.PIXELS}) == 1 and all(c == "." or int(c, 36) < len(chaser_art.PALETTE) for row in chaser_art.PIXELS for c in row)


def test_the_art_draws_two_pixels_a_character_and_steps_aside_without_colour(monkeypatch: pytest.MonkeyPatch) -> None:
    import re

    from chaser_agent import chaser_art, terminal_art

    lines = terminal_art.mascot()
    visible = [re.sub(r"\x1b\[[0-9;]*m", "", line) for line in lines]
    assert len(lines) == (len(chaser_art.PIXELS) + 1) // 2 and {len(v) for v in visible} == {terminal_art.width()}
    assert "\x1b[38;2;" in "".join(lines) and set("".join(visible)) <= {"▀", "▄", " "}
    monkeypatch.setattr(terminal_art.shutil, "get_terminal_size", lambda *_: __import__("os").terminal_size((120, 40)))
    beside = terminal_art.beside(["Chaser Agent", "status"], colour=True)
    assert len(beside) == len(lines) and any("Chaser Agent" in line for line in beside)
    assert terminal_art.beside(["Chaser Agent"], colour=False) == ["Chaser Agent"]
    monkeypatch.setenv("CHASER_NO_ART", "1")
    assert terminal_art.beside(["Chaser Agent"], colour=True) == ["Chaser Agent"]
