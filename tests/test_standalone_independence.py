"""Enforce the Principle 1 / Principle 2 dependency rule.

The standalone-first redesign says the MIT core must run without ChaseOS and must
not import ChaseOS, a provider SDK, an MCP runtime, or a browser runtime. Before
this module that rule was documentation only: it happened to hold, but nothing
would have failed if a later pass violated it. These tests make the rule
executable.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

SRC_ROOT = Path(__file__).resolve().parents[1] / "src" / "chaser_agent"

# Packages that must never depend on ChaseOS or on live external runtimes.
CORE_PACKAGES = ("core", "workflows", "governance", "reviews", "memory", "knowledge")

# Import prefixes forbidden inside the core packages.
FORBIDDEN_CORE_IMPORTS = (
    "chaser_agent.integrations",
    "chaser_agent.providers",
    "chaseos",
    "openai",
    "anthropic",
    "ollama",
    "mcp",
    "playwright",
    "selenium",
    "torch",
    "transformers",
    "fastapi",
)


def _module_files(package: str) -> list[Path]:
    return sorted(p for p in (SRC_ROOT / package).rglob("*.py") if "__pycache__" not in p.parts)


def _imported_names(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            names.add(node.module)
    return names


@pytest.mark.parametrize("package", CORE_PACKAGES)
def test_core_packages_do_not_import_chaseos_or_live_runtimes(package: str):
    offenders: list[str] = []
    for path in _module_files(package):
        for imported in _imported_names(path):
            for forbidden in FORBIDDEN_CORE_IMPORTS:
                if imported == forbidden or imported.startswith(forbidden + "."):
                    offenders.append(f"{path.relative_to(SRC_ROOT).as_posix()} imports {imported}")
    assert not offenders, "core packages must stay ChaseOS-free and runtime-free: " + "; ".join(offenders)


def test_core_packages_import_and_run_without_chaseos_installed():
    """The standalone path must work with no ChaseOS package importable."""
    import importlib

    for package in CORE_PACKAGES:
        importlib.import_module(f"chaser_agent.{package}")

    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("chaseos")


def test_optional_chaseos_adapter_is_inactive_and_cannot_dispatch():
    from chaser_agent.integrations.chaseos.adapter import ChaseOSProposalAdapter

    adapter = ChaseOSProposalAdapter()
    assert adapter.active is False

    packet = adapter.proposal_packet("memory_promotion", {"memory_id": "memory-001"})
    assert packet["adapter_status"] == "inactive"
    assert packet["dispatch_status"] == "not_dispatched"
    assert all(value is False for value in packet["authority"].values())

    with pytest.raises(RuntimeError):
        adapter.dispatch(packet)


def test_provider_package_imports_no_provider_sdk():
    """The fake adapter must stay fake: no SDK may appear in the provider package."""
    sdk_prefixes = ("openai", "anthropic", "ollama", "httpx", "requests", "aiohttp", "urllib.request", "socket")
    offenders: list[str] = []
    for path in _module_files("providers"):
        for imported in _imported_names(path):
            for forbidden in sdk_prefixes:
                if imported == forbidden or imported.startswith(forbidden + "."):
                    offenders.append(f"{path.relative_to(SRC_ROOT).as_posix()} imports {imported}")
    assert not offenders, "provider package must make no network calls: " + "; ".join(offenders)


def test_fake_adapter_satisfies_the_provider_protocol():
    from chaser_agent.core.protocols import ProviderAdapter
    from chaser_agent.providers.fake import FakeProviderAdapter

    assert isinstance(FakeProviderAdapter(), ProviderAdapter)


def test_local_governance_never_authorizes_action_execution():
    from chaser_agent.governance.local import LocalGovernance

    governance = LocalGovernance(operator_id="chase")
    assert governance.can_action_be_executed({"action_id": "action-001", "requires_approval": True}) is False
    assert governance.policy_for("execute")["external_action_execution"] == "disabled"
