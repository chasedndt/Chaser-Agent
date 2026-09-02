# 2026-08-12 — Tool / MCP Capability Boundary (Layer 13)

## Trigger

Chase chose option B: build the tool boundary while he performs the operator review. Layer 13 was the largest remaining structural gap and sits directly on his stated north star of being excellent at tool calling.

## Why tools are stricter than providers

A provider reply is text. A tool call touches the filesystem, network, accounts, and money, and its *result* is authored by someone else — a fetched page, a file, an MCP server response — making it the most attacker-controlled input the harness handles. The boundary therefore adds side-effect classification and scope containment on top of the provider pattern.

## Implemented

New package `src/chaser_agent/tools/`:

- `models.py` — `ToolCapability` (frozen, must declare at least one scope), `ToolRequest`, `ToolResult`, `ToolInvocationPlan`, `ToolOutcome`. `PERMITTED_SIDE_EFFECTS_P0_1 = {"read_only"}`.
- `registry.py` — `ToolRegistry` with three gates (registered, granted, in scope) plus side-effect gating and per-run call budgets; `ToolDenied` carries a reason code; `execute()` raises.
- `fake.py` — `FakeToolAdapter` and `HOSTILE_TOOL_RESULTS` (six named payloads: page injection, forged grant, scope widening, credential bait, fake approval record, claimed execution).
- `quarantine.py` — results are `untrusted_tool_output` with an all-false authority block; non-ok statuses are unusable and emptied.

`ToolRegistry` protocol added to `core/protocols.py`; `chaser_agent.tools` added to the forbidden-import list for core packages, plus a scan proving the tool package imports no `requests`, `httpx`, `socket`, `subprocess`, or `shutil`.

## Design decisions worth recording

**Registration is not permission.** Declaring a capability describes a tool; a separate explicit grant enables it. Tested directly.

**Denied calls do not consume budget.** Otherwise hostile input could exhaust a legitimate tool's allowance simply by triggering refusals.

**Scopes are normalised before comparison.** `docs/../../etc/passwd` fails a prefix check only after normalisation; URL scopes match host and path so `blog.cloudflare.com.evil.test` is refused despite the shared string prefix.

**Side-effecting tools are declarable but never authorizable.** Writing the contract now, while execution stays impossible, is the same sequencing used for providers.

## Tests

`tests/test_tool_capability_boundary.py` — 33 tests weighted toward denials. The load-bearing case is `test_hostile_tool_output_cannot_widen_a_scope`: after a result explicitly requests a wider scope, the registry still refuses the wider target and declared scopes are unchanged. Tool output cannot influence tool authority.

## Authority boundary

No execution, no real MCP client, no filesystem or network access, no credential handling, no approval path for writes or external effects, no wiring into the review pipeline, no merge to `main`.

## Verification

```bash
PYTHONPATH=src python -m pytest tests/test_tool_capability_boundary.py -q
PYTHONPATH=src .venv/bin/python -m pytest -q
```

Result: 177 passed.

## Next

Wire an authorized read-only plan into a review run so tool-sourced evidence carries provenance and a trust grade, then consider a real read-only MCP client behind the same contract. Both gated on operator approval.
