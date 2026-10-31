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
    raise ReplyRejected("invalid_action", "action type must be tool, ask_human or final")


def parse_reply(text: str) -> ModelReply:
    """Parse one reasoner reply, refusing anything outside the protocol."""
    value, had_preamble = _decode_object(text)
    _exact_keys(value, {"thought", "actions"}, {"thought", "actions"}, "reply")
    actions = value["actions"]
    if not isinstance(actions, list) or not actions:
        raise ReplyRejected("invalid_field", "actions must be a non-empty list")
    if len(actions) > MAX_ACTIONS_PER_STEP:
        raise ReplyRejected("too_many_actions", f"at most {MAX_ACTIONS_PER_STEP} actions per step")
    parsed = tuple(_action(item) for item in actions)
    if len(parsed) > 1 and not all(isinstance(action, ToolAction) for action in parsed):
        raise ReplyRejected("mixed_actions", "ask_human and final must be the only action in a step")
    return ModelReply(_text(value["thought"], "thought", MAX_THOUGHT_CHARS), parsed, had_preamble)
