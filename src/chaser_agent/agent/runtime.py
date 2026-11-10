"""Sessions and the observe-act loop.

Each step asks the reasoner for one reply, runs what it permits, records what
happened and shows the result back. A step that needs a person ends the thread and
saves state: the question or approval survives a restart, and the answer resumes
the loop from the saved transcript. Nothing about a turn lives only in memory.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import secrets
import threading
import time
import traceback
from pathlib import Path
from threading import Event
from typing import Any

from chaser_agent.agent.context import MAX_CONTEXT_CHARS, build_system_prompt, render_transcript
from chaser_agent.agent.events import EventLog, utc_now, with_io_retry
from chaser_agent.agent.protocol import AskHuman, Finish, ReplyRejected, ToolAction, parse_reply
from chaser_agent.agent.reasoners import Reasoner, ReasonerUnavailable
from chaser_agent.agent.tooling import AgentTool, Toolbox, ToolContext, ToolFailure, args_digest
from chaser_agent.agent.workflow import WorkflowSpec
from chaser_agent.tools.quarantine import detect_injection_signals
from chaser_agent.tools.registry import ToolDenied

SESSION_ID = re.compile(r"^as-[0-9]{14}-[0-9a-f]{10}$")
REASONER_TIMEOUT_SECONDS = 600
MAX_INVALID_REPLIES = 3
MAX_MESSAGE_CHARS = 20_000
ACTIVE_STATES = frozenset({"queued", "reasoning", "running_tool"})
RESUMABLE_STATES = frozenset({"finished", "failed", "cancelled", "budget_stopped", "interrupted"})
# Which approved 3D motion shows for each state. These illustrate state; they are not evidence of work.
MOTION_BY_STATE = {
    "queued": "tracking",
    "reasoning": "compiling",
    "running_tool": "tracking",
    "awaiting_human": "awaiting-approval",
    "awaiting_approval": "awaiting-approval",
    "finished": "complete",
    "failed": "blocked",
    "budget_stopped": "blocked",
    "cancelled": "dormant",
    "interrupted": "uncertain",
}
MOODS = frozenset({"approved", "blocked", "contradiction", "correction", "uncertain"})


class NotFound(LookupError):
    pass


class Conflict(RuntimeError):
    pass


def _atomic_json(path: Path, value: Any) -> None:
    staging = path.with_name(path.name + f".{secrets.token_hex(4)}.tmp")
    text = json.dumps(value, ensure_ascii=False, indent=1)
    with_io_retry(lambda: staging.write_text(text, encoding="utf-8", newline="\n"))
    with_io_retry(lambda: os.replace(staging, path))


def _write_text(path: Path, text: str) -> None:
    with_io_retry(lambda: path.write_text(text, encoding="utf-8"))


def _read_text(path: Path) -> str:
    return with_io_retry(lambda: path.read_text(encoding="utf-8"))


class AgentRuntime:
    def __init__(self, data_dir: Path, *, toolbox: Toolbox | None = None, reasoners: list[Reasoner] | None = None) -> None:
        self.root = data_dir / "agent" / "sessions"
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.data_dir = data_dir
        self.toolbox = toolbox or Toolbox()
        self.reasoners: dict[str, Reasoner] = {r.reasoner_id: r for r in reasoners or []}
        self.workflows: dict[str, WorkflowSpec] = {}
        self.default_workflow = "general"
        self.parent_link: dict[str, str] | None = None
        # Workspace folders a pack's own tools keep records in. workspace_write can't touch them.
        self.read_only_workspace_folders: tuple[str, ...] = ()
        self._lock = threading.RLock()
        self._sessions: dict[str, dict[str, Any]] = {}
        self._logs: dict[str, EventLog] = {}
        self._threads: dict[str, threading.Thread] = {}
        self._cancels: dict[str, Event] = {}
        self._status_cache: dict[str, Any] = {"checked_at": None, "routes": []}
        self._status_refreshing = False
        self._load_existing()

    # --- setup ---------------------------------------------------------------

    def add_reasoner(self, reasoner: Reasoner) -> None:
        self.reasoners[reasoner.reasoner_id] = reasoner

    def add_workflow(self, workflow: WorkflowSpec) -> None:
        self.workflows[workflow.workflow_id] = workflow

    def _load_existing(self) -> None:
        for folder in sorted(self.root.iterdir()):
            path = folder / "session.json"
            if not SESSION_ID.fullmatch(folder.name) or not path.is_file():
                continue
            session = json.loads(_read_text(path))
            self._sessions[session["id"]] = session
            self._logs[session["id"]] = EventLog(folder / "events.jsonl")
            if session["status"] in ACTIVE_STATES:
                session["status"] = "interrupted"
                self._logs[session["id"]].append("interrupted", reason="the service restarted during this step")
                self._save(session)

    # --- session paths and state --------------------------------------------

    def _folder(self, session_id: str) -> Path:
        return self.root / session_id

    def _save(self, session: dict[str, Any]) -> None:
        session["updated_at"] = utc_now()
        _atomic_json(self._folder(session["id"]) / "session.json", session)

    def _get(self, session_id: str) -> dict[str, Any]:
        session = self._sessions.get(session_id)
        if session is None:
            raise NotFound(session_id)
        return session

    def _workflow(self, session: dict[str, Any]) -> WorkflowSpec:
        return self.workflows[session["workflow_id"]]

    def route_workflow(self, message: str) -> WorkflowSpec:
        for workflow in self.workflows.values():
            if workflow.matches(message):
                return workflow
        return self.workflows[self.default_workflow]

    # --- public operations ---------------------------------------------------

    def create_session(
        self,
        message: str,
        *,
        workflow_id: str | None = None,
        reasoner_id: str = "auto",
        title: str | None = None,
        withhold_tools: frozenset[str] = frozenset(),
        start: bool = True,
    ) -> dict[str, Any]:
        message = self._clean_message(message)
        workflow = self.workflows.get(workflow_id or "") or self.route_workflow(message)
        if workflow_id and workflow.workflow_id != workflow_id:
            raise NotFound(f"workflow {workflow_id}")
        if reasoner_id != "auto" and reasoner_id not in self.reasoners:
            raise NotFound(f"reasoner {reasoner_id}")
        stamp = time.strftime("%Y%m%d%H%M%S", time.gmtime())
        session_id = f"as-{stamp}-{secrets.token_hex(5)}"
        folder = self._folder(session_id)
        for child in ("outputs", "reasoner", "workspace"):
            (folder / child).mkdir(parents=True, exist_ok=True, mode=0o700)
        grants = sorted((workflow.grants & frozenset(self.toolbox.ids())) - withhold_tools)
        session: dict[str, Any] = {
            "id": session_id,
            "title": (title or message)[:120],
            "workflow_id": workflow.workflow_id,
            "workflow_title": workflow.title,
            "reasoner_id": reasoner_id,
            "reasoner_used": None,
            "created_at": utc_now(),
            "updated_at": utc_now(),
            "status": "queued",
            "mood": None,
            "goal": message,
            "grants": grants,
            "transcript": [{"role": "user", "text": message}],
            "turn": 1,
            "steps_used": 0,
            "steps_total": 0,
            "active_seconds": 0.0,
            "tool_counts": {},
            "invalid_replies": 0,
            "denied_calls": 0,
            "tool_failures": 0,
            "elided_observations": 0,
            "pending": None,
            "answers": [],
            "plan": [],
            "final_answer": None,
            "error": None,
        }
        with self._lock:
            self._sessions[session_id] = session
            self._logs[session_id] = EventLog(folder / "events.jsonl")
            self._logs[session_id].append(
                "session_created", workflow=workflow.workflow_id, reasoner=reasoner_id, grants=grants, goal=message,
            )
            self._save(session)
        if start:
            self._start(session_id)
        return self.snapshot(session_id)

    def send_message(self, session_id: str, message: str) -> dict[str, Any]:
        message = self._clean_message(message)
        with self._lock:
            session = self._get(session_id)
            if session["status"] not in RESUMABLE_STATES or session["pending"]:
                raise Conflict("This session is busy or waiting for an answer")
            session["transcript"].append({"role": "user", "text": message})
            session.update(goal=message, turn=session["turn"] + 1, steps_used=0, active_seconds=0.0, status="queued", final_answer=None, error=None, mood=None)
            self._logs[session_id].append("message", text=message, turn=session["turn"])
            self._save(session)
        self._start(session_id)
        return self.snapshot(session_id)

    def answer(self, session_id: str, question_id: str, text: str) -> dict[str, Any]:
        text = self._clean_message(text)
        with self._lock:
            session = self._get(session_id)
            pending = session["pending"]
            if not pending or pending["kind"] != "question" or pending["id"] != question_id:
                raise Conflict("That question is no longer waiting for an answer")
            answer_id = f"ans-{secrets.token_hex(6)}"
            row = {"answer_id": answer_id, "question_id": question_id, "question": pending["question"], "text": text, "at": utc_now()}
            session["answers"].append(row)
            session["transcript"].append({"role": "human_answer", "answer_id": answer_id, "question_id": question_id, "text": text})
            session.update(pending=None, status="queued")
            self._logs[session_id].append("question_answered", question_id=question_id, answer_id=answer_id, text=text)
            self._save(session)
        self._start(session_id)
        return self.snapshot(session_id)

    def decide(self, session_id: str, approval_id: str, digest: str, decision: str, decided_by: str = "local_operator") -> dict[str, Any]:
        if decision not in {"approve", "reject"}:
            raise Conflict("Decision must be approve or reject")
        with self._lock:
            session = self._get(session_id)
            pending = session["pending"]
            if not pending or pending["kind"] != "approval" or pending["id"] != approval_id:
                raise Conflict("That approval is no longer waiting")
            if not hmac.compare_digest(pending["digest"], digest):
                raise Conflict("The approval digest does not match the pending request")
            session.update(pending=None, status="queued")
            self._logs[session_id].append(
                "approval_decided", approval_id=approval_id, digest=digest, decision=decision, decided_by=decided_by,
            )
            self._save(session)
        tool = self.toolbox.get(pending["tool"])
        if decision == "approve" and tool is not None:
            session["mood"] = "approved"
            self._execute(session, tool, pending["args"], pending["call_id"])
        else:
            self._observe(
                session, pending["tool"], pending["call_id"], "denied",
                "The operator rejected this exact request. Do not retry it in the same form.",
            )
        with self._lock:
            self._save(session)
        self._start(session_id)
        return self.snapshot(session_id)

    def cancel(self, session_id: str) -> dict[str, Any]:
        with self._lock:
            session = self._get(session_id)
            event = self._cancels.get(session_id)
            if event is not None:
                event.set()
            if session["status"] not in ACTIVE_STATES:
                if session["status"] in {"awaiting_human", "awaiting_approval"}:
                    session.update(status="cancelled", pending=None)
                    self._logs[session_id].append("cancelled", reason="operator")
                    self._save(session)
        return self.snapshot(session_id)

    def wait(self, session_id: str, timeout: float = 30.0) -> None:
        thread = self._threads.get(session_id)
        if thread is not None:
            thread.join(timeout)

    # --- reads ---------------------------------------------------------------

    def snapshot(self, session_id: str) -> dict[str, Any]:
        with self._lock:
            session = self._get(session_id)
            workflow = self.workflows.get(session["workflow_id"])
            pending = dict(session["pending"]) if session["pending"] else None
            return {
                "id": session["id"],
                "title": session["title"],
                "status": session["status"],
                "motion": self._motion(session),
                "goal": session["goal"],
                "workflow": session["workflow_id"],
                "workflow_title": session["workflow_title"],
                "reasoner": session["reasoner_used"] or session["reasoner_id"],
                "grants": list(session["grants"]),
                "turn": session["turn"],
                "steps_used": session["steps_used"],
                "steps_total": session["steps_total"],
                "max_steps": workflow.max_steps if workflow else None,
                "tool_counts": dict(session["tool_counts"]),
                "invalid_replies": session["invalid_replies"],
                "denied_calls": session["denied_calls"],
                "tool_failures": session["tool_failures"],
                "pending": pending,
                "plan": list(session["plan"]),
                "final_answer": session["final_answer"],
                "error": session["error"],
                "created_at": session["created_at"],
                "updated_at": session["updated_at"],
                "events": len(self._logs[session_id]),
            }

    def list_sessions(self, limit: int = 40) -> list[dict[str, Any]]:
        with self._lock:
            rows = sorted(self._sessions.values(), key=lambda row: row["created_at"], reverse=True)[:limit]
            return [
                {key: row[key] for key in ("id", "title", "status", "workflow_id", "created_at", "updated_at")} | {"motion": self._motion(row)}
                for row in rows
            ]

    def events(self, session_id: str, after: int = 0, limit: int = 500) -> list[dict[str, Any]]:
        self._get(session_id)
        return self._logs[session_id].after(max(0, after), max(1, min(limit, 1000)))

    def artifacts(self, session_id: str) -> list[dict[str, Any]]:
        self._get(session_id)
        workspace = self._folder(session_id) / "workspace"
        rows = []
        for path in sorted(workspace.rglob("*")):
            if path.is_file() and not path.is_symlink():
                rows.append({
                    "name": path.relative_to(workspace).as_posix(),
                    "bytes": path.stat().st_size,
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                })
            if len(rows) >= 200:
                break
        return rows

    def artifact_path(self, session_id: str, name: str) -> Path:
        self._get(session_id)
        workspace = (self._folder(session_id) / "workspace").resolve()
        target = (workspace / name).resolve()
        if not target.is_relative_to(workspace) or target.is_symlink() or not target.is_file():
            raise NotFound(name)
        return target

    def output_text(self, session_id: str, call_id: str, limit: int = 40_000) -> dict[str, Any]:
        self._get(session_id)
        if not re.fullmatch(r"c[0-9]{4}-[0-9]+", call_id):
            raise NotFound(call_id)
        path = self._folder(session_id) / "outputs" / f"{call_id}.txt"
        if not path.is_file():
            raise NotFound(call_id)
        text = _read_text(path)
        return {"call_id": call_id, "total_chars": len(text), "text": text[:limit]}

    def status(self) -> dict[str, Any]:
        self._refresh_reasoner_status()
        with self._lock:
            active = [row["id"] for row in self._sessions.values() if row["status"] in ACTIVE_STATES]
            waiting = [row["id"] for row in self._sessions.values() if row["status"] in {"awaiting_human", "awaiting_approval"}]
            return {
                "tools": [self.toolbox.get(tool_id).catalogue_entry() for tool_id in self.toolbox.ids()],
                "workflows": [{"id": w.workflow_id, "title": w.title, "max_steps": w.max_steps} for w in self.workflows.values()],
                "examples": [example for w in self.workflows.values() for example in w.examples][:4],
                "reasoners": self._live_routes(),
                "sessions": len(self._sessions),
                "active_sessions": active,
                "waiting_for_operator": waiting,
                "motion": "tracking" if active else ("awaiting-approval" if waiting else "dormant"),
                "parent": self.parent_link,
            }

    def _live_routes(self) -> dict[str, Any]:
        """Other routes are slow to check, so they're cached. The bridge is cheap and changes the moment a program attaches."""
        bridge = self.reasoners.get("bridge")
        routes = [bridge.status() if bridge is not None and row["id"] == "bridge" else row for row in self._status_cache["routes"]]
        return {**self._status_cache, "routes": routes}

    def _refresh_reasoner_status(self) -> None:
        with self._lock:
            checked = self._status_cache["checked_at"]
            if self._status_refreshing or (checked and time.time() - checked < 120):
                return
            self._status_refreshing = True

        def refresh() -> None:
            routes = []
            for reasoner in list(self.reasoners.values()):
                try:
                    routes.append(reasoner.status())
                except Exception as exc:  # A broken route must not stop the status page.
                    routes.append({"id": reasoner.reasoner_id, "label": reasoner.label, "available": False, "reason": type(exc).__name__})
            with self._lock:
                self._status_cache = {"checked_at": time.time(), "routes": routes}
                self._status_refreshing = False

        threading.Thread(target=refresh, daemon=True).start()

    # --- the loop ------------------------------------------------------------

    @staticmethod
    def _clean_message(message: str) -> str:
        if not isinstance(message, str) or not message.strip() or len(message) > MAX_MESSAGE_CHARS:
            raise ValueError(f"A message of 1 to {MAX_MESSAGE_CHARS} characters is required")
        return message.strip()

    @staticmethod
    def _motion(session: dict[str, Any]) -> str:
        if session["status"] == "finished" and session.get("mood") in MOODS:
            return session["mood"].replace("_", "-")
        if session["status"] in {"queued", "reasoning", "running_tool"} and session.get("mood") == "approved":
            return "approved"
        return MOTION_BY_STATE.get(session["status"], "dormant")

    def _start(self, session_id: str) -> None:
        with self._lock:
            existing = self._threads.get(session_id)
            if existing is not None and existing.is_alive() and existing is not threading.current_thread():
                raise Conflict("This session is already running")
            self._cancels[session_id] = Event()
            thread = threading.Thread(target=self._drive_guarded, args=(session_id,), daemon=True, name=f"chaser-{session_id}")
            self._threads[session_id] = thread
            thread.start()

    def _drive_guarded(self, session_id: str) -> None:
        session = self._get(session_id)
        try:
            self._drive(session)
        except Exception as exc:  # Keep the failure visible rather than dying silently.
            (self._folder(session_id) / "loop-error.txt").write_text(traceback.format_exc(), encoding="utf-8")
            self._finish(session, "failed", error=f"The agent loop stopped: {type(exc).__name__}. Details are in loop-error.txt.")

    def _resolve_reasoner(self, session: dict[str, Any]) -> Reasoner:
        requested = session["reasoner_id"]
        if requested != "auto":
            return self.reasoners[requested]
        reasons = []
        for reasoner in self.reasoners.values():
            if reasoner.reasoner_id == "bridge":
                continue
            state = reasoner.status()
            if state.get("available"):
                return reasoner
            reasons.append(f"{reasoner.label}: {state.get('reason')}")
        # Last, and only if another program is really answering it: left waiting, work would just hang.
        bridge = self.reasoners.get("bridge")
        if bridge is not None and bridge.status().get("connected"):
            return bridge
        raise ReasonerUnavailable("no_route", "No AI model is connected, so this can't start. " + " | ".join(reasons))

    def _finish(self, session: dict[str, Any], status: str, *, answer: str | None = None, error: str | None = None) -> None:
        with self._lock:
            session.update(status=status, final_answer=answer, error=error)
            self._logs[session["id"]].append("turn_finished", status=status, answer=answer, error=error, steps=session["steps_used"])
            self._save(session)

    def _drive(self, session: dict[str, Any]) -> None:
        session_id = session["id"]
        workflow = self._workflow(session)
        cancel = self._cancels[session_id]
        try:
            reasoner = self._resolve_reasoner(session)
        except ReasonerUnavailable as exc:
            self._finish(session, "failed", error=exc.message)
            return
        with self._lock:
            session["reasoner_used"] = reasoner.reasoner_id
        grants = frozenset(session["grants"])
        system = build_system_prompt(
            catalogue=self.toolbox.catalogue(grants), workflow_title=workflow.title, instructions=workflow.instructions,
        )
        limit = getattr(reasoner, "max_context_chars", MAX_CONTEXT_CHARS) - len(system)
        started = time.monotonic()
        base_seconds = session["active_seconds"]
        while True:
            if cancel.is_set():
                self._finish(session, "cancelled")
                return
            session["active_seconds"] = round(base_seconds + time.monotonic() - started, 3)
            if session["steps_used"] >= workflow.max_steps or session["active_seconds"] >= workflow.max_seconds:
                self._finish(session, "budget_stopped", error="This turn used its step or time budget. Send a message to continue it.")
                return
            transcript, elided = render_transcript(
                session["transcript"], goal=session["goal"], steps_left=workflow.max_steps - session["steps_used"], max_chars=limit,
            )
            with self._lock:
                session.update(status="reasoning", elided_observations=elided)
                session["steps_used"] += 1
                session["steps_total"] += 1
                step = session["steps_total"]
                self._save(session)
            reasoner_folder = self._folder(session_id) / "reasoner"
            _write_text(reasoner_folder / f"{step:04d}.prompt.txt", system + "\n\n=====\n\n" + transcript)
            self._logs[session_id].append(
                "reasoner_request", step=step, route=reasoner.reasoner_id,
                prompt_sha256=hashlib.sha256((system + transcript).encode("utf-8")).hexdigest(), prompt_chars=len(system) + len(transcript), elided_observations=elided,
            )
            try:
                reply = reasoner.complete(system, transcript, timeout=REASONER_TIMEOUT_SECONDS, cancel=cancel)
            except ReasonerUnavailable as exc:
                if exc.code == "cancelled":
                    self._finish(session, "cancelled")
                else:
                    self._finish(session, "failed", error=f"{reasoner.label} did not answer: {exc.message}")
                return
            _write_text(reasoner_folder / f"{step:04d}.reply.txt", reply.text)
            reply_sha = hashlib.sha256(reply.text.encode("utf-8")).hexdigest()
            try:
                parsed = parse_reply(reply.text)
            except ReplyRejected as exc:
                self._reject_reply(session, step, reply.text, reply_sha, exc)
                if session["invalid_replies"] >= MAX_INVALID_REPLIES:
                    self._finish(session, "failed", error="The reasoner kept replying outside the protocol.")
                    return
                continue
            self._logs[session_id].append(
                "reasoner_reply", step=step, route=reply.route, model=reply.model, seconds=reply.seconds, credits=reply.credits,
                reply_sha256=reply_sha, thought=parsed.thought, actions=[type(a).__name__ for a in parsed.actions],
            )
            with self._lock:
                session["transcript"].append({"role": "assistant", "text": reply.text})
            if self._apply_actions(session, parsed.actions, grants, step):
                return
            with self._lock:
                self._save(session)

    def _reject_reply(self, session: dict[str, Any], step: int, text: str, sha: str, exc: ReplyRejected) -> None:
        with self._lock:
            session["invalid_replies"] += 1
            session["transcript"].append({"role": "assistant", "text": text[:4000]})
            session["transcript"].append({
                "role": "note",
                "text": f"Your last reply was refused ({exc.reason_code}): {exc.message}. Nothing ran. Reply with one JSON object following the protocol.",
            })
            self._logs[session["id"]].append("reply_rejected", step=step, reason=exc.reason_code, reply_sha256=sha)
            self._save(session)

    def _apply_actions(self, session: dict[str, Any], actions: tuple[Any, ...], grants: frozenset[str], step: int) -> bool:
        """Returns True when the thread should stop: finished or waiting for a person."""
        session_id = session["id"]
        for index, action in enumerate(actions):
            if isinstance(action, Finish):
                self._finish(session, "finished", answer=action.answer)
                return True
            if isinstance(action, AskHuman):
                question_id = f"q-{secrets.token_hex(6)}"
                with self._lock:
                    session.update(status="awaiting_human", pending={
                        "kind": "question", "id": question_id, "question": action.question,
                        "question_kind": action.kind, "options": list(action.options), "at": utc_now(),
                    })
                    self._logs[session_id].append("question_asked", question_id=question_id, question=action.question, kind=action.kind, options=list(action.options))
                    self._save(session)
                return True
            assert isinstance(action, ToolAction)
            call_id = f"c{step:04d}-{index + 1}"
            try:
                tool = self.toolbox.authorize(action.tool, action.args, grants, session["tool_counts"])
            except ToolDenied as denial:
                with self._lock:
                    session["denied_calls"] += 1
                self._logs[session_id].append("tool_denied", call_id=call_id, tool=action.tool, reason=denial.reason_code, message=denial.message)
                self._observe(session, action.tool, call_id, "denied", f"Refused ({denial.reason_code}): {denial.message}. Nothing ran.", record=False)
                continue
            with self._lock:
                session["tool_counts"][tool.tool_id] = session["tool_counts"].get(tool.tool_id, 0) + 1
            if tool.requires_approval:
                digest = args_digest(tool.tool_id, action.args)
                approval_id = f"ap-{secrets.token_hex(6)}"
                with self._lock:
                    session.update(status="awaiting_approval", pending={
                        "kind": "approval", "id": approval_id, "tool": tool.tool_id, "args": action.args,
                        "digest": digest, "call_id": call_id, "description": tool.description, "at": utc_now(),
                    })
                    self._logs[session_id].append("approval_requested", approval_id=approval_id, tool=tool.tool_id, args=action.args, digest=digest, call_id=call_id)
                    dropped = [a.tool for a in actions[index + 1 :] if isinstance(a, ToolAction)]
                    if dropped:
                        session["transcript"].append({"role": "note", "text": f"These calls in the same reply did not run while approval is pending: {dropped}."})
                    self._save(session)
                return True
            self._execute(session, tool, action.args, call_id)
        return False

    def _execute(self, session: dict[str, Any], tool: AgentTool, args: dict[str, Any], call_id: str) -> None:
        session_id = session["id"]
        with self._lock:
            session["status"] = "running_tool"
            self._save(session)
        self._logs[session_id].append("tool_started", call_id=call_id, tool=tool.tool_id, side_effect=tool.side_effect_class, args=args)

        def set_mood(mood: str) -> None:
            if mood in MOODS:
                session["mood"] = mood

        def set_plan(plan: list[dict[str, str]]) -> None:
            session["plan"] = plan

        context = ToolContext(
            session_id=session_id, turn_id=str(session["turn"]), call_id=call_id,
            workspace=self._folder(session_id) / "workspace", outputs=self._folder(session_id) / "outputs",
            answers=list(session["answers"]), cancel=self._cancels.get(session_id) or Event(),
            set_mood=set_mood, set_plan=set_plan, read_only_folders=self.read_only_workspace_folders,
        )
        started = time.monotonic()
        try:
            value = tool.handler(args, context)
            status = "ok"
            text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, indent=1)
        except ToolDenied as denial:
            status, text = "denied", f"Refused ({denial.reason_code}): {denial.message}"
            with self._lock:
                session["denied_calls"] += 1
        except ToolFailure as failure:
            status, text = "error", f"Tool failed: {failure}"
            with self._lock:
                session["tool_failures"] += 1
        except Exception as exc:  # A tool's internals stay out of the model's context.
            status, text = "error", f"Tool failed unexpectedly: {type(exc).__name__}"
            with self._lock:
                session["tool_failures"] += 1
        self._observe(session, tool.tool_id, call_id, status, text, seconds=round(time.monotonic() - started, 3))

    def _observe(self, session: dict[str, Any], tool_id: str, call_id: str, status: str, text: str, *, seconds: float = 0.0, record: bool = True) -> None:
        session_id = session["id"]
        sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
        _write_text(self._folder(session_id) / "outputs" / f"{call_id}.txt", text)
        signals = detect_injection_signals(text)
        with self._lock:
            session["transcript"].append({
                "role": "observation", "tool": tool_id, "call_id": call_id, "status": status, "sha256": sha, "text": text, "signals": signals,
            })
        if record:
            self._logs[session_id].append(
                "tool_finished", call_id=call_id, tool=tool_id, status=status, output_sha256=sha,
                output_chars=len(text), seconds=seconds, injection_signals=signals,
                preview=text[:400] if status != "ok" else None,
            )
