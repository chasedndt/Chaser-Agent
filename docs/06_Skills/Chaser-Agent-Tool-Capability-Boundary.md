# Chaser agent Tool / MCP Capability Boundary

**Layer:** 13 (Tool / MCP) · **Status:** contract, registry, and fake implemented — no execution · **Code:** `src/chaser_agent/tools/`

## Why tools get stricter treatment than providers

A provider reply is text. A tool call touches the filesystem, the network, accounts, and money — and its *result* is written by someone else. A fetched page, a file, or an MCP server response is the most attacker-controlled input the harness handles.

So the tool boundary adds two things the provider boundary did not need: **side-effect classification** (what a call can change in the world) and **scope containment** (which concrete targets it may touch).

## Three gates, all of which must pass

```text
registered  ->  granted  ->  in scope  ->  authorized (still not executed)
```

1. **Registered.** The tool has a declared `ToolCapability`.
2. **Granted.** The tool was explicitly enabled for this run. **Registration is not permission** — declaring a capability describes a tool, it does not turn it on. This is the single most important line in the design, and `test_registration_alone_is_not_permission` enforces it.
3. **In scope.** The concrete target falls inside the capability's declared scopes.

Default is deny at every gate.

## The capability declaration

```text
tool_id · display_name · purpose
side_effect_class   read_only | local_write | external_effect
allowed_scopes      path prefixes and/or URL prefixes
max_calls_per_run · requires_approval · reversible
```

`ToolCapability` is a frozen dataclass, so authority cannot be widened in place — there is a test asserting exactly that. It must declare at least one scope; a capability with no scope is a contradiction and raises.

### Side-effect gating

`PERMITTED_SIDE_EFFECTS_P0_1 = {"read_only"}`. Local writes and external effects are *declarable* — so contracts can be written and tested now — but can never be authorized until an operator-approved grant path exists. Attempting either raises `side_effect_not_permitted`, proven for both classes.

### Scope containment

Path scopes are normalised before comparison, which is what stops `docs/../../etc/passwd` from passing a naive prefix check. URL scopes match on host **and** path prefix, so `https://blog.cloudflare.com.evil.test/` is refused despite sharing a prefix as a plain string. Six escape shapes are covered by parametrised denial tests.

### Call budget

Each capability declares `max_calls_per_run`. Exceeding it yields `call_budget_exceeded`. Denied calls deliberately do **not** consume budget — otherwise a hostile input could exhaust a legitimate tool's allowance by triggering refusals.

## Authorization is not execution

`ToolRegistry.plan()` returns a `ToolInvocationPlan` stamped `executed: False` with an all-false authority block. `ToolRegistry.execute()` raises `execution_not_implemented`. There is no code path in P0.1 that runs a tool — the boundary is being proven before the capability exists, exactly as the provider boundary was.

## Denial reason codes

`unregistered_tool` · `tool_not_granted` · `scope_violation` · `side_effect_not_permitted` · `call_budget_exceeded` · `execution_not_implemented`

Every denial names its reason, so a refusal is diagnosable rather than a silent no.

## Hostile tool output

`HOSTILE_TOOL_RESULTS` seeds the adversarial corpus with six shapes:

| Payload | What it attempts |
|---|---|
| `page_instruction_injection` | HTML comment telling the agent to ignore governance |
| `forged_grant` | Claims the tool was upgraded and approval granted |
| `scope_widening` | Asks for a re-run against `../../` and an internal host |
| `credential_bait` | Requests an API key and deployment secret |
| `fake_approval_record` | Fabricates an operator approval record |
| `result_claiming_execution` | Claims files were deleted and changes pushed |

`quarantine_tool_result()` marks every result `untrusted_tool_output` with an all-false authority block — it cannot grant further tool access, widen a scope, approve an action, promote memory, or mutate governance. Non-`ok` statuses are never usable and their content is emptied.

The load-bearing test is `test_hostile_tool_output_cannot_widen_a_scope`: after a result explicitly asks for a wider scope, the registry still refuses the wider target and the declared scopes are unchanged. **Tool output cannot influence tool authority.**

## Dependency rule

`ToolRegistry` lives as a protocol in `core/protocols.py`; the implementation lives in `tools/`. `chaser_agent.tools` is on the forbidden-import list for every core package, and the tool package is scanned to prove it imports no `requests`, `httpx`, `socket`, `subprocess`, or `shutil` — the fake cannot quietly become real.

## Test coverage

`tests/test_tool_capability_boundary.py` — 33 tests, weighted toward denials: default deny, grant/revoke, six scope-escape shapes, both side-effect classes, budget enforcement, no-execution, and every hostile payload.

## What this does not do

No execution, no real MCP client, no filesystem or network access, no credential handling, no approval path for writes or external effects, and no wiring into the source-review pipeline. Those are later passes, each gated on operator approval.

## Next step for this layer

Wire an authorized read-only plan into a review run so tool-sourced evidence carries provenance and a trust grade — then, and only then, consider a real read-only MCP client behind the same contract.
