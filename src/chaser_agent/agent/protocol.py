"""What a reasoner may say, and nothing else.

Every model answer is parsed here before anything happens. Unknown keys are
refused rather than ignored: a reply carrying `owner_approved` or `executed` has
no field to land in, so it can never be read as authority. Any provider that can
return text can drive the loop, which keeps the harness provider-neutral.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

MAX_ACTIONS_PER_STEP = 4
MAX_THOUGHT_CHARS = 2_000
MAX_ANSWER_CHARS = 40_000
MAX_QUESTION_CHARS = 2_000
MAX_PREAMBLE_CHARS = 2_000
QUESTION_KINDS = ("missing_information", "preference", "approval")
_TOOL_NAME = re.compile(r"[a-z][a-z0-9_]{1,119}")


class ReplyRejected(ValueError):
    """The reply did not meet the protocol. Counted separately from tool denials."""

    def __init__(self, reason_code: str, message: str) -> None:
        super().__init__(f"{reason_code}: {message}")
        self.reason_code = reason_code
        self.message = message


@dataclass(frozen=True)
class ToolAction:
    tool: str
    args: dict[str, Any]


@dataclass(frozen=True)
class AskHuman:
    question: str
    kind: str
    options: tuple[str, ...] = ()


@dataclass(frozen=True)
class Finish:
    answer: str


Action = ToolAction | AskHuman | Finish


@dataclass(frozen=True)
class ModelReply:
    thought: str
    actions: tuple[Action, ...]
    had_preamble: bool = False
    set_aside_final: bool = False


def _no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ReplyRejected("duplicate_key", f"key {key!r} appears twice")
        result[key] = value
    return result


_DECODER = json.JSONDecoder(object_pairs_hook=_no_duplicates)


def _decode_object(text: str) -> tuple[dict[str, Any], bool]:
    stripped = text.strip()
    fence = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", stripped, re.DOTALL)
    if fence:
        stripped = fence.group(1).strip()
    start = stripped.find("{")
    if start < 0:
        raise ReplyRejected("no_json_object", "the reply contains no JSON object")
    if start > MAX_PREAMBLE_CHARS:
        raise ReplyRejected("preamble_too_long", "text before the JSON object is too long")
    try:
        value, end = _DECODER.raw_decode(stripped[start:])
    except json.JSONDecodeError as exc:
        raise ReplyRejected("invalid_json", f"not valid JSON: {exc.msg}") from exc
    if stripped[start + end :].strip():
        raise ReplyRejected("trailing_text", "text follows the JSON object")
    if not isinstance(value, dict):
        raise ReplyRejected("not_an_object", "the reply must be one JSON object")
    return value, start > 0


def _text(value: Any, field: str, limit: int) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ReplyRejected("invalid_field", f"{field} must be non-empty text")
    if len(value) > limit:
        raise ReplyRejected("field_too_long", f"{field} exceeds {limit} characters")
    return value.strip()


def _exact_keys(item: dict[str, Any], allowed: set[str], required: set[str], label: str) -> None:
    extra = set(item) - allowed
    if extra:
        raise ReplyRejected("unknown_field", f"{label} has unsupported fields: {sorted(extra)}")
    missing = required - set(item)
    if missing:
        raise ReplyRejected("missing_field", f"{label} is missing: {sorted(missing)}")


def _action(item: Any) -> Action:
    if not isinstance(item, dict):
        raise ReplyRejected("invalid_action", "each action must be an object")
    kind = item.get("type")
    if kind == "tool":
        _exact_keys(item, {"type", "tool", "args"}, {"type", "tool"}, "tool action")
        args = item.get("args", {})
        if not isinstance(args, dict):
            raise ReplyRejected("invalid_field", "tool args must be an object")
        return ToolAction(_text(item["tool"], "tool", 120), args)
    if kind == "ask_human":
        _exact_keys(item, {"type", "question", "kind", "options"}, {"type", "question", "kind"}, "question")
        if item["kind"] not in QUESTION_KINDS:
            raise ReplyRejected("invalid_field", f"question kind must be one of {QUESTION_KINDS}")
        options = item.get("options", [])
        if not isinstance(options, list) or len(options) > 6 or not all(isinstance(o, str) and o.strip() for o in options):
            raise ReplyRejected("invalid_field", "options must be up to six short strings")
        return AskHuman(_text(item["question"], "question", MAX_QUESTION_CHARS), item["kind"], tuple(options))
    if kind == "final":
        _exact_keys(item, {"type", "answer"}, {"type", "answer"}, "final action")
        return Finish(_text(item["answer"], "answer", MAX_ANSWER_CHARS))
    # 12 Nov 2026: ChaseOS Cloud's models often name the tool in "type", as {"type": "graph_search", "args": {...}},
    # and repeat it after being refused, so a card failed with "kept replying outside the protocol". That shape has one
    # meaning, so it is read as the tool call; whether the tool may run is still decided by the session's grants.
    # The same models also often send {"type": "graph_search", "tool": "graph_search", "args": {...}}, and each refusal
    # cost a model turn. The name given twice, the same both times, has the same one meaning; different names in the
    # two fields are still refused.
    if (isinstance(kind, str) and _TOOL_NAME.fullmatch(kind) and set(item) <= {"type", "tool", "args"}
            and item.get("tool", kind) == kind):
        args = item.get("args", {})
        if not isinstance(args, dict):
            raise ReplyRejected("invalid_field", "tool args must be an object")
        return ToolAction(kind, args)
    raise ReplyRejected("invalid_action", 'action type must be tool, ask_human or final; a tool call is '
                                          '{"type": "tool", "tool": "<name>", "args": {...}}')


def parse_reply(text: str) -> ModelReply:
    """Parse one reasoner reply, refusing anything outside the protocol."""
    value, had_preamble = _decode_object(text)
    # A final answer sent in its own top-level "final" field beside tool calls is the same premature answer as a final
    # action after them (below): the tools run and the answer is set aside. With no tool calls it is still refused.
    early_final = "final" in value and isinstance(value.get("actions"), list) and bool(value["actions"])
    _exact_keys(value, {"thought", "actions", "final"} if early_final else {"thought", "actions"}, {"thought", "actions"}, "reply")
    actions = value["actions"]
    if not isinstance(actions, list) or not actions:
        raise ReplyRejected("invalid_field", "actions must be a non-empty list")
    if len(actions) > MAX_ACTIONS_PER_STEP:
        raise ReplyRejected("too_many_actions", f"at most {MAX_ACTIONS_PER_STEP} actions per step")
    parsed = tuple(_action(item) for item in actions)
    set_aside = False
    # 12 Nov 2026: after the objective check asked for a missing read, a model replied with the tool call and a final
    # answer in one step, twice, and the turn failed as "outside the protocol".
    # Tool calls followed by one final at the end have one safe reading: run the tools and set the final aside, because
    # it was written before the tools' results existed. The model answers again once it has seen them. A final or a
    # question anywhere else in a multi-action step is still refused.
    if (len(parsed) > 1 and isinstance(parsed[-1], Finish)
            and all(isinstance(action, ToolAction) for action in parsed[:-1])):
        parsed, set_aside = parsed[:-1], True
    if early_final:
        if not all(isinstance(action, ToolAction) for action in parsed):
            raise ReplyRejected("unknown_field", 'a top-level "final" field is only set aside beside tool calls')
        set_aside = True
    if len(parsed) > 1 and not all(isinstance(action, ToolAction) for action in parsed):
        raise ReplyRejected("mixed_actions", "ask_human and final must be the only action in a step")
    return ModelReply(_text(value["thought"], "thought", MAX_THOUGHT_CHARS), parsed, had_preamble, set_aside)
