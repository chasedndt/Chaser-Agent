# Chaser Agent ChaseOS-Native Review Packet V0

## Purpose

This is the first ChaseOS-native version of the Chaser Agent source-intelligence loop. It does not turn Chaser Agent into a live autonomous runtime. It wraps the existing deterministic Source Card Harness V0 in ChaseOS control-plane language so outputs can be reviewed, routed, and audited without losing the Layer 0 boundaries.

## What was learned from the repo

The repo's current truth is:

- Chaser Agent is local-first, deterministic, and review-first.
- ChaseOS remains the parent control plane and canonical truth owner.
- Source claims, Chaser Agent inferences, uncertainty labels, action candidates, and memory candidates must remain separated.
- Memory candidates and action candidates are proposals only.
- Provider calls, browser/computer-use, MCP, Hermes/OpenClaw activation, fine-tuning, public/customer actions, and canonical mutation remain closed by default.

A ChaseOS-native packet therefore needs to preserve the source-card artifacts while adding control-plane fields ChaseOS expects: runtime lane, workflow, graph links, recommended Agent-Activity slug, authority flags, blocked actions, artifact paths, and next approval/Gate step.

## CLI

From the repo root:

```bash
PYTHONPATH=. .venv/bin/python -m chaser_agent.cli chaseos-native-source-card \
  --input examples/sources/toy_website_design_note.md \
  --out logs/runs \
  --workflow hermes_review_execute \
  --runtime-lane chaser-agent
```

The command writes a unique `logs/runs/chaseos-native-source-card-.../` folder containing the normal Source Card Harness V0 artifacts plus:

- `chaseos_native_packet.json` — ChaseOS-native routing/review packet;
- `operator_handoff.md` — human-readable operator handoff with graph links and authority proof;
- `run_log.json` — run proof stamped as `command_family: chaseos-native-source-card`.

## Allowed workflow stamps

The CLI fail-closes to a small ChaseOS workflow allowlist:

- `hermes_review_execute`
- `hermes_operator_today_shadow`
- `hermes_watch`
- `chaser_agent_review_packet`

These are labels for review packet routing. They do not activate Hermes/OpenClaw, consume approvals, dispatch runtime actions, or mutate canonical docs.

## Authority boundary

Every packet records:

- `provider_call_performed: false`
- `external_api_call_performed: false`
- `runtime_dispatch_performed: false`
- `mcp_activation_performed: false`
- `browser_or_computer_use_performed: false`
- `approval_consumed: false`
- `memory_promotion_performed: false`
- `canonical_mutation_performed: false`
- `public_or_customer_action_performed: false`

The recommended Agent-Activity path is only a suggested destination if the operator later promotes the handoff through ChaseOS governance.

## Verification

```bash
PYTHONPATH=. .venv/bin/python -m pytest -q tests/test_chaseos_native_packet.py
```

Full baseline:

```bash
.venv/bin/python -m scripts.validate_jsonl evals/datasets/golden/*.jsonl
PYTHONPATH=. .venv/bin/python -m pytest -q
```
