"""Build a runtime for the local service: built-in tools, routes, and operator packs.

A pack is a Python file the operator names at startup. It can add tools, reasoners
and workflows that are not part of this open-source core, such as private business
workflows or links to a parent system. Nothing is discovered automatically.
"""

from __future__ import annotations

import hashlib
import importlib.util
import sys
from pathlib import Path
from typing import Any

from chaser_agent.agent.builtin import register_builtin_tools
from chaser_agent.agent.reasoners import BridgeReasoner, ChaseOSCloudReasoner, ClaudeCliReasoner
from chaser_agent.agent.runtime import AgentRuntime
from chaser_agent.agent.tooling import Toolbox
from chaser_agent.agent.workflow import WorkflowSpec

BASE_GRANTS = frozenset({"recall_output", "workspace_write", "workspace_read", "workspace_list", "update_plan", "memory_search", "memory_propose"})
GENERAL = WorkflowSpec(
    workflow_id="general",
    title="General",
    instructions="Help the operator with what they ask, using the tools you have. If you have no tool that can do it, say so plainly and say what would be needed.",
    grants=BASE_GRANTS,
    max_steps=24,
)


def load_pack(path: Path, runtime: AgentRuntime) -> dict[str, Any]:
    """Run one operator-named pack's register(runtime). Its hash goes in the receipt."""
    if not path.is_file():
        raise ValueError(f"Pack not found: {path}")
    name = "chaser_pack_" + hashlib.sha256(str(path).encode("utf-8")).hexdigest()[:12]
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ValueError(f"Pack cannot be loaded: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    register = getattr(module, "register", None)
    if register is None:
        raise ValueError(f"Pack has no register(runtime): {path}")
    register(runtime)
    return {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def build_runtime(data_dir: Path, *, packs: tuple[Path, ...] = (), claude_model: str = "sonnet") -> AgentRuntime:
    toolbox = Toolbox()
    register_builtin_tools(toolbox, memory_database=data_dir / "agent" / "memory.db")
    # ChaseOS Cloud comes first: it is the route allowed to run unattended work. Consumer logins come after it.
    reasoners = [ChaseOSCloudReasoner.from_environment(), ClaudeCliReasoner(model=claude_model), BridgeReasoner()]
    runtime = AgentRuntime(data_dir, toolbox=toolbox, reasoners=reasoners)
    runtime.add_workflow(GENERAL)
    runtime.loaded_packs = [load_pack(path, runtime) for path in packs]
    return runtime
