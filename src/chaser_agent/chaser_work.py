"""`chaser waiting`, `sessions`, `approve`, `reject` and `receipt`: the work and the proof, from a terminal.

`receipt` reads the session's event log straight from disk and re-derives every hash, so it doesn't
trust the running service: an edited line shows up as a broken chain. It lists each approval with who
signed it and the digest of the exact request they saw, and hashes what the session wrote.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from chaser_agent.agent.events import verify_chain
from chaser_agent.terminal_theme import pad


def first_line(text: Any) -> str:
    return (str(text or "").strip().splitlines() or [""])[0]

WAITING = {"awaiting_human", "awaiting_approval"}
TONE = {"finished": "ok", "failed": "fail", "cancelled": "dim", "budget_stopped": "warn", "interrupted": "warn",
        "awaiting_human": "warn", "awaiting_approval": "warn", "queued": "teal", "reasoning": "teal", "running_tool": "teal"}
WORDS = {"awaiting_human": "asks you something", "awaiting_approval": "needs your yes", "running_tool": "working",
         "reasoning": "thinking", "budget_stopped": "used its budget"}


def age(stamp: str | None, now: datetime | None = None) -> str:
    """'4 min', '3 h', '2 d' since an ISO time."""
    if not stamp:
        return ""
    try:
        then = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    except ValueError:
        return ""
    seconds = ((now or datetime.now(timezone.utc)) - then).total_seconds()
    for size, unit in ((86400, "d"), (3600, "h"), (60, "min")):
        if seconds >= size:
            return f"{int(seconds // size)} {unit}"
    return "now"


def sessions_table(rows: list[dict[str, Any]], paint: Callable[[str, str], str], *, limit: int = 15) -> list[str]:
    if not rows:
        return [paint("  Nothing yet. Start with: chaser chat", "dim")]
    width = min(48, max(len(first_line(r.get("title"))) for r in rows[:limit]))
    out = []
    for row in rows[:limit]:
        status = row.get("status", "")
        title = first_line(row.get("title"))[:width]
        state = pad(paint(WORDS.get(status, status.replace("_", " ")), TONE.get(status, "dim")), 18)
        out.append(f"  {paint('●', TONE.get(status, 'dim'))} {title:<{width}}  {state}{paint(age(row.get('updated_at')).rjust(7), 'dim')}  {paint(row['id'], 'dim')}")
    return out


def waiting_lines(details: list[dict[str, Any]], paint: Callable[[str, str], str]) -> list[str]:
    """One block per session that needs you: what it asks, how long it has waited, how to answer."""
    if not details:
        return [f"  {paint('✓', 'ok')} Nothing is waiting for you."]
    out = []
    for snap in sorted(details, key=lambda s: s.get("updated_at") or ""):
        pending = snap.get("pending") or {}
        out.append(f"  {paint('●', 'warn')} {first_line(snap.get('title'))}  {paint('· waiting ' + age(snap.get('updated_at')), 'dim')}")
        if pending.get("kind") == "approval":
            out.append(f"    needs your yes for {paint(str(pending.get('tool')), 'head')}  {paint('digest ' + str(pending.get('digest'))[:12] + '…', 'dim')}")
            out.append(paint(f"    chaser approve {snap['id']}   or   chaser reject {snap['id']}", "teal"))
        else:
            out.append(f"    asks: {pending.get('question')}")
            out.append(paint(f"    chaser chat --session {snap['id']}", "teal"))
    return out


def find_session(data_dir: Path, session_id: str | None) -> Path | None:
    """The session's folder: by id, by an id's unique start, or the newest when no id is given."""
    root = Path(data_dir) / "agent" / "sessions"
    if not root.is_dir():
        return None
    folders = [p for p in root.iterdir() if (p / "events.jsonl").is_file()]
    if session_id:
        matches = [p for p in folders if p.name == session_id] or [p for p in folders if p.name.startswith(session_id)]
        return matches[0] if len(matches) == 1 else None
    return max(folders, key=lambda p: p.name, default=None)


def receipt(folder: Path) -> dict[str, Any]:
    """Everything the receipt shows, from disk only."""
    chain = verify_chain(folder / "events.jsonl")
    rows = [json.loads(line) for line in (folder / "events.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    session = {}
    try:
        session = json.loads((folder / "session.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        pass
    asked = {r["data"].get("approval_id"): r for r in rows if r.get("type") == "approval_requested"}
    approvals = []
    for row in rows:
        if row.get("type") == "approval_decided":
            data = row["data"]
            request = asked.get(data.get("approval_id"), {}).get("data", {})
            approvals.append({"decision": data.get("decision"), "decided_by": data.get("decided_by") or "local_operator",
                              "tool": request.get("tool"), "digest": data.get("digest"), "at": row.get("at"),
                              "matches_request": data.get("digest") == request.get("digest")})
    tools: dict[str, int] = {}
    for row in rows:
        if row.get("type") == "tool_started":
            tools[row["data"].get("tool")] = tools.get(row["data"].get("tool"), 0) + 1
    outputs = []
    workspace = folder / "workspace"
    if workspace.is_dir():
        for path in sorted(p for p in workspace.rglob("*") if p.is_file()):
            outputs.append({"path": path.relative_to(folder).as_posix(), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    return {"id": folder.name, "title": session.get("title"), "status": session.get("status"), "chain": chain,
            "started": rows[0]["at"] if rows else None, "ended": rows[-1]["at"] if rows else None,
            "approvals": approvals, "tools": tools, "outputs": outputs}


def receipt_lines(value: dict[str, Any], paint: Callable[[str, str], str]) -> list[str]:
    chain = value["chain"]
    title = first_line(value.get("title")) or value["id"]
    out = [paint(f"  Receipt · {title[:70] + ('…' if len(title) > 70 else '')}", "head"), paint(f"  {value['id']} · {value.get('status') or ''}", "dim"), ""]
    if chain.get("verified"):
        out.append(f"  {paint('✓', 'ok')} Chain verified: {chain['events']} events, each linked to the one before  {paint('head ' + chain['head'][:16] + '…', 'dim')}")
    else:
        out.append(f"  {paint('✗', 'fail')} Chain broken at event {chain.get('failed_at')}: the log was changed after it was written.")
    out.append(paint(f"    {(value.get('started') or '')[:16].replace('T', ' ')} → {(value.get('ended') or '')[:16].replace('T', ' ')} UTC", "dim"))
    out += ["", paint("  APPROVALS", "dim")]
    if not value["approvals"]:
        out.append(paint("    none asked for", "dim"))
    for item in value["approvals"]:
        word = paint("yes", "ok") if item["decision"] == "approve" else paint("no ", "fail")
        bound = paint("bound to the request", "dim") if item["matches_request"] else paint("digest differs from the request", "fail")
        out.append(f"    {word}  {str(item['tool']):<24} signed {paint(item['decided_by'], 'head')}  {paint(str(item['digest'])[:12] + '…', 'dim')}  {bound}")
    out += ["", paint("  TOOLS RUN", "dim")]
    import textwrap

    used = ", ".join(f"{name} ×{count}" for name, count in value["tools"].items())
    out += [f"    {line}" for line in textwrap.wrap(used, 88)] if used else [paint("    none", "dim")]
    out += ["", paint("  WHAT IT WROTE", "dim")]
    if not value["outputs"]:
        out.append(paint("    nothing", "dim"))
    for item in value["outputs"][:20]:
        shown = item["path"] if len(item["path"]) <= 52 else "…" + item["path"][-51:]
        out.append(f"    {shown:<52} {paint('sha256 ' + item['sha256'][:16] + '…', 'dim')}")
    if len(value["outputs"]) > 20:
        out.append(paint(f"    … and {len(value['outputs']) - 20} more (chaser receipt --json lists them all)", "dim"))
    return out
