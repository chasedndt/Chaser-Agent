"""Tools that really run, behind grants the model cannot touch.

Gates, in order: registered, granted for this session, under its call budget,
arguments match the schema, target inside the tool's own scope check. Passing all
five still leaves approval: a tool that needs it pauses the turn until a person
decides on the exact arguments.

External effects are declarable but cannot be registered here. Sending mail,
publishing, paying or deploying has no route through this module; the operator
does those in the product that owns them.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from threading import Event
from typing import Any

from chaser_agent.tools.models import SideEffectClass
from chaser_agent.tools.registry import ToolDenied

RUNNABLE_SIDE_EFFECTS = frozenset({"read_only", "local_write"})
_TYPES: dict[str, tuple[type, ...]] = {
    "string": (str,),
    "integer": (int,),
    "number": (int, float),
    "boolean": (bool,),
    "array": (list,),
    "object": (dict,),
}


@dataclass
class ToolContext:
    """What a running tool may see. Grants and approvals are deliberately absent."""

    session_id: str
    turn_id: str
    call_id: str
    workspace: Path
    outputs: Path
    answers: list[dict[str, Any]]
    cancel: Event
    set_mood: Callable[[str], None] = lambda _mood: None
    set_plan: Callable[[list[dict[str, str]]], None] = lambda _plan: None
    read_only_folders: tuple[str, ...] = ()


class ToolFailure(RuntimeError):
    """A tool could not do its job. The message is shown to the model and the operator."""


Handler = Callable[[dict[str, Any], ToolContext], Any]
ScopeCheck = Callable[[dict[str, Any]], None]


@dataclass(frozen=True)
class AgentTool:
    tool_id: str
    description: str
    parameters: dict[str, Any]
    side_effect_class: SideEffectClass
    handler: Handler
    requires_approval: bool = False
    max_calls_per_session: int = 40
    check: ScopeCheck | None = None
    toolset: str = "core"

    def catalogue_entry(self) -> dict[str, Any]:
        return {
            "tool": self.tool_id,
            "description": self.description,
            "side_effect": self.side_effect_class,
            "needs_human_approval": self.requires_approval,
            "max_calls": self.max_calls_per_session,
            "args_schema": self.parameters,
        }


def _validate(value: Any, schema: dict[str, Any], path: str) -> None:
    expected = schema.get("type")
    if expected:
        kinds = _TYPES[expected]
        if not isinstance(value, kinds) or (expected in {"integer", "number"} and isinstance(value, bool)):
            raise ToolDenied("invalid_arguments", f"{path} must be {expected}")
    if "enum" in schema and value not in schema["enum"]:
        raise ToolDenied("invalid_arguments", f"{path} must be one of {schema['enum']}")
    if isinstance(value, str) and "maxLength" in schema and len(value) > schema["maxLength"]:
        raise ToolDenied("invalid_arguments", f"{path} exceeds {schema['maxLength']} characters")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            raise ToolDenied("invalid_arguments", f"{path} is below {schema['minimum']}")
        if "maximum" in schema and value > schema["maximum"]:
            raise ToolDenied("invalid_arguments", f"{path} is above {schema['maximum']}")
    if isinstance(value, list):
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            raise ToolDenied("invalid_arguments", f"{path} has more than {schema['maxItems']} items")
        for index, item in enumerate(value):
            if "items" in schema:
                _validate(item, schema["items"], f"{path}[{index}]")
    if isinstance(value, dict):
        properties = schema.get("properties", {})
        missing = [name for name in schema.get("required", []) if name not in value]
        if missing:
            raise ToolDenied("invalid_arguments", f"{path} is missing {missing}")
        if schema.get("additionalProperties") is False:
            extra = sorted(set(value) - set(properties))
            if extra:
                raise ToolDenied("invalid_arguments", f"{path} has unsupported fields {extra}")
        for name, item in value.items():
            if name in properties:
                _validate(item, properties[name], f"{path}.{name}")


def validate_arguments(schema: dict[str, Any], args: dict[str, Any]) -> None:
    """Enough JSON Schema for tool arguments, without a dependency in the core."""
    _validate(args, {"type": "object", "additionalProperties": False, **schema}, "args")


def args_digest(tool_id: str, args: dict[str, Any]) -> str:
    """The exact thing a person approves. Any change to the arguments changes it."""
    canonical = json.dumps({"tool": tool_id, "args": args}, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass
class Toolbox:
    """Declared tools. Registration is not permission; sessions carry their own grants."""

    _tools: dict[str, AgentTool] = field(default_factory=dict)

    def register(self, tool: AgentTool) -> None:
        if tool.side_effect_class not in RUNNABLE_SIDE_EFFECTS:
            raise ValueError(f"{tool.tool_id}: {tool.side_effect_class} tools have no route through the agent loop")
        if tool.tool_id in self._tools:
            raise ValueError(f"tool already registered: {tool.tool_id}")
        self._tools[tool.tool_id] = tool

    def get(self, tool_id: str) -> AgentTool | None:
        return self._tools.get(tool_id)

    def ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._tools))

    def catalogue(self, grants: frozenset[str]) -> list[dict[str, Any]]:
        return [self._tools[tool_id].catalogue_entry() for tool_id in sorted(grants) if tool_id in self._tools]

    def authorize(self, tool_id: str, args: dict[str, Any], grants: frozenset[str], counts: dict[str, int]) -> AgentTool:
        tool = self._tools.get(tool_id)
        if tool is None:
            raise ToolDenied("unregistered_tool", f"{tool_id!r} does not exist")
        if tool_id not in grants:
            raise ToolDenied("tool_not_granted", f"{tool_id!r} is not granted to this session")
        if counts.get(tool_id, 0) >= tool.max_calls_per_session:
            raise ToolDenied("call_budget_exceeded", f"{tool_id!r} used its {tool.max_calls_per_session} calls")
        validate_arguments(tool.parameters, args)
        if tool.check is not None:
            tool.check(args)
        return tool
