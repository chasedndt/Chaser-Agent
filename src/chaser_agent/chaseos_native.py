from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

from chaser_agent.run_artifacts import current_repo_commit, write_json
from chaser_agent.source_card import PROMOTION_WARNING

ALLOWED_CHASEOS_WORKFLOWS = {
    "hermes_review_execute",
    "hermes_operator_today_shadow",
    "hermes_watch",
    "chaser_agent_review_packet",
}

DEFAULT_CHASEOS_GRAPH_LINKS = ["[[HERMES]]", "[[Hermes-Runtime-Profile]]", "[[Agent-Activity-Index]]"]


def validate_chaseos_workflow(workflow: str) -> None:
    if workflow not in ALLOWED_CHASEOS_WORKFLOWS:
        allowed = ", ".join(sorted(ALLOWED_CHASEOS_WORKFLOWS))
        raise ValueError(f"unsupported ChaseOS workflow: {workflow}; allowed: {allowed}")


def _safe_slug(value: str, *, fallback: str = "source") -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or fallback


def recommended_agent_activity_slug(*, source_id: str, created_at: str) -> str:
    stamp = created_at[:10].replace("-", "")
    digest = hashlib.sha256(f"{source_id}:{created_at}".encode("utf-8")).hexdigest()[:8]
    return f"hermes-optimus-chaser-agent-native-{stamp}-{_safe_slug(source_id)[:40]}-{digest}"


def build_chaseos_native_packet(
    *,
    source_card: dict[str, Any],
    human_review_packet: dict[str, Any],
    run_id: str,
    created_at: str,
    runtime_lane: str,
    workflow: str,
    output_dir: Path,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    validate_chaseos_workflow(workflow)
    source_id = str(source_card.get("source_id") or human_review_packet.get("source_id") or run_id)
    claims = source_card.get("source_claims") or []
    actions = source_card.get("action_candidates") or []
    memories = source_card.get("memory_candidates") or []
    uncertainties = source_card.get("uncertainty_labels") or []
    activity_slug = recommended_agent_activity_slug(source_id=source_id, created_at=created_at)
    return {
        "surface_id": "chaser_agent_chaseos_native_source_card_v0",
        "run_id": run_id,
        "created_at": created_at,
        "repo_commit": current_repo_commit(repo_root),
        "runtime_lane": runtime_lane,
        "workflow": workflow,
        "chaseos_graph_links": DEFAULT_CHASEOS_GRAPH_LINKS,
        "recommended_agent_activity_slug": activity_slug,
        "recommended_agent_activity_path": f"07_LOGS/Agent-Activity/{activity_slug}.md",
        "source_id": source_id,
        "source_title": source_card.get("source_title"),
        "source_origin": source_card.get("source_origin"),
        "privacy_class": source_card.get("privacy_class"),
        "trust_state": source_card.get("trust_state"),
        "review_status": "pending_operator_review",
        "promotion_status": "not_promoted",
        "summary": {
            "source_claim_count": len(claims),
            "uncertainty_count": len(uncertainties),
            "action_candidate_count": len(actions),
            "memory_candidate_count": len(memories),
            "human_review_decision": human_review_packet.get("pass_fail_decision"),
        },
        "artifact_paths": {
            "run_folder": output_dir.as_posix(),
            "source_card": (output_dir / "source_card.json").as_posix(),
            "human_review_packet": (output_dir / "human_review_packet.json").as_posix(),
            "chaseos_native_packet": (output_dir / "chaseos_native_packet.json").as_posix(),
            "operator_handoff": (output_dir / "operator_handoff.md").as_posix(),
        },
        "authority": {
            "write_scope": "local_repo_review_artifacts_only",
            "provider_call_performed": False,
            "external_api_call_performed": False,
            "runtime_dispatch_performed": False,
            "mcp_activation_performed": False,
            "browser_or_computer_use_performed": False,
            "approval_consumed": False,
            "memory_promotion_performed": False,
            "canonical_mutation_performed": False,
            "public_or_customer_action_performed": False,
        },
        "blocked_actions": [
            "No ChaseOS canonical truth mutation was performed.",
            "No memory candidate was promoted.",
            "No provider/API/runtime/MCP/browser action was performed.",
            "No approval record was consumed.",
            "No public, customer, credential, payment, or deployment action was performed.",
        ],
        "required_next_step": "operator_review_then_chaseos_gate_if_any_output_should_be_promoted",
        "canonical_promotion_warning": PROMOTION_WARNING,
    }


def build_operator_handoff(packet: dict[str, Any]) -> str:
    links = " · ".join(packet["chaseos_graph_links"])
    artifact_paths = packet["artifact_paths"]
    authority = packet["authority"]
    blocked = "\n".join(f"- {item}" for item in packet["blocked_actions"])
    return f"""# Chaser Agent ChaseOS-Native Source Card Handoff

Runtime lane: `{packet['runtime_lane']}`
Workflow: `{packet['workflow']}`
Run ID: `{packet['run_id']}`
Graph links: {links}

## Verdict

`pending_operator_review` — Chaser Agent produced a ChaseOS-native review packet, not canonical truth.

## Source

- Source ID: `{packet['source_id']}`
- Source title: `{packet.get('source_title')}`
- Source origin: `{packet.get('source_origin')}`
- Privacy class: `{packet.get('privacy_class')}`

## Review counts

- Source claims: {packet['summary']['source_claim_count']}
- Uncertainty labels: {packet['summary']['uncertainty_count']}
- Action candidates: {packet['summary']['action_candidate_count']}
- Memory candidates: {packet['summary']['memory_candidate_count']}

## Artifacts

- Run folder: `{artifact_paths['run_folder']}`
- Source card: `{artifact_paths['source_card']}`
- Human review packet: `{artifact_paths['human_review_packet']}`
- ChaseOS-native packet: `{artifact_paths['chaseos_native_packet']}`
- Recommended Agent-Activity path if promoted after review: `{packet['recommended_agent_activity_path']}`

## Authority proof

- Provider calls: none
- External API calls: none
- Runtime dispatch: {authority['runtime_dispatch_performed']}
- Approval consumed: {authority['approval_consumed']}
- Canonical mutation: {authority['canonical_mutation_performed']}

## Blocked actions

{blocked}

## Next operator step

Review the packet. If anything should become durable ChaseOS truth, memory, roadmap, tasking, skill policy, or public/product claim, route it through the appropriate ChaseOS Gate/operator approval path.
"""


def build_chaseos_native_run_log(
    *,
    run_id: str,
    created_at: str,
    command: str,
    output_paths: list[Path],
    repo_root: Path | None = None,
) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "created_at": created_at,
        "command": command,
        "command_family": "chaseos-native-source-card",
        "repo_commit": current_repo_commit(repo_root),
        "outputs": [path.as_posix() for path in output_paths],
        "provider_calls": "none",
        "external_api_calls": "none",
        "runtime_adapters": "none",
        "mcp_activation": "none",
        "browser_or_computer_use": "none",
        "fine_tuning_or_training": "none",
        "approval_consumed": False,
        "canonical_mutation_performed": False,
        "review_required": True,
        "notes": "Deterministic local ChaseOS-native Chaser Agent review packet. No external authority activated.",
    }


def write_chaseos_native_run(run_folder: Path, artifacts: dict[str, Any], operator_handoff: str, run_log: dict[str, Any]) -> None:
    run_folder.mkdir(parents=True, exist_ok=False)
    for filename, payload in artifacts.items():
        write_json(run_folder / filename, payload)
    (run_folder / "operator_handoff.md").write_text(operator_handoff, encoding="utf-8")
    write_json(run_folder / "run_log.json", run_log)
