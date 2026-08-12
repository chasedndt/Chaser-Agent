"""Quarantine tool results.

A tool result is content written by someone else - a web page, a file, an MCP
server. It is the most attacker-controlled input the harness handles, so it
carries no authority at all: it cannot grant tool access, widen a scope, approve
an action, promote memory, or claim that work was done.
"""

from __future__ import annotations

import re

from chaser_agent.tools.models import ToolOutcome, ToolResult

UNTRUSTED = "untrusted_tool_output"

INJECTION_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("instruction_injection", re.compile(r"(?i)ignore\s+(?:your\s+)?(?:previous\s+)?(?:instructions|rules|governance)")),
    ("forged_grant", re.compile(r"(?i)requires_approval\s*[:=]\s*false|granted\s+approval|has\s+been\s+upgraded\s+to")),
    ("scope_widening", re.compile(r"(?i)re-?run\s+this\s+(?:read\s+)?against|\.\./\.\./|grant\s+yourself")),
    ("credential_bait", re.compile(r"(?i)supply\s+the\s+value\s+of|paste\s+the\s+(?:deployment\s+)?secret|api[_-]?key")),
    ("forged_approval", re.compile(r"(?i)approval\s+recorded|approval_consumed\s*[:=]\s*true|gate\s*[:=]\s*bypassed")),
    ("claims_execution", re.compile(r"(?i)i\s+have\s+(?:already\s+)?(?:deleted|pushed|deployed|posted|executed)")),
    ("claims_promotion", re.compile(r"(?i)mark\s+every\s+memory\s+candidate\s+promoted|memory\s+candidate[s]?\s+promoted")),
)


def detect_injection_signals(content: str) -> list[str]:
    return sorted({name for name, pattern in INJECTION_PATTERNS if pattern.search(content)})


def quarantine_tool_result(result: ToolResult) -> ToolOutcome:
    reasons: list[str] = []
    if result.status != "ok":
        reasons.append(f"tool status {result.status!r} is not a usable result")
    if result.executed:
        reasons.append("result reported execution, which is not permitted in P0.1")

    signals = detect_injection_signals(result.content)
    if signals:
        reasons.append("result attempted to assert authority or widen scope")

    return ToolOutcome(
        tool_id=result.tool_id,
        request_hash=result.request_hash,
        status=result.status,
        trust_state=UNTRUSTED,
        usable=not reasons,
        content=result.content if result.status == "ok" else "",
        rejection_reasons=tuple(reasons),
        injection_signals=tuple(signals),
    )
