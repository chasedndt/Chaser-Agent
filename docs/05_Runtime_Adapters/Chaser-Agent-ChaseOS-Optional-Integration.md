# Chaser Agent — ChaseOS Optional Integration

**Layer:** 16 (Governance / Approval) · **Status:** adapter exists and is deliberately inactive in P0.1 · **Code:** `src/chaser_agent/integrations/chaseos/`

## The rule

Chaser Agent is **standalone-first and ChaseOS-enhanced**. The MIT-licensed core must run, review, remember, and build a knowledge map with no ChaseOS installed. ChaseOS is an optional adapter and deployment mode, never a dependency.

```text
Chaser Agent core
    ↓ depends only on protocols
Local standalone adapters   |   Optional ChaseOS adapters
```

### Forbidden dependencies

```text
core -> ChaseOS
core -> live provider SDK
core -> MCP runtime
core -> browser runtime
```

**This is enforced, not merely documented.** `tests/test_standalone_independence.py` parses the AST of every module in `core`, `workflows`, `governance`, `reviews`, `memory`, and `knowledge` and fails if any forbidden import appears — including `chaser_agent.integrations`, so the core cannot reach the ChaseOS adapter even indirectly. The test suite also asserts that `import chaseos` raises `ModuleNotFoundError`, proving the standalone path runs without ChaseOS present.

## Two deployment modes

| Concern | Standalone | ChaseOS-integrated |
|---|---|---|
| Approval authority | Human operator via local governance | ChaseOS Gate |
| Durable truth | Approved durable local state | ChaseOS-governed shared canonical state |
| Memory | Local SQLite, user-owned | May sync with shared ChaseOS memory |
| Policy / permissions | Local configuration | ChaseOS policy and permission model |
| Routing | None (CLI only) | ChaseOS runtime routing and orchestration |
| Graph | Local provenance map | Cross-project graph intelligence |

Invariant in **both** modes:

```text
generated output   != canonical truth
memory candidate   != memory
action candidate   != action
review packet      != approval
integration packet != dispatch
agent confidence   != authority
```

## The adapter

`ChaseOSProposalAdapter` (`integrations/chaseos/adapter.py`) converts a Chaser Agent proposal into a ChaseOS-shaped packet **without dispatching anything**:

- `active = False`;
- every packet is stamped `adapter_status: "inactive"` and `dispatch_status: "not_dispatched"`;
- the packet's `authority` block is all-`False`: `execute`, `promote_memory`, `mutate_canonical_state`, `call_provider`, `call_external_tool`;
- `gate_consumption` documents where a future ChaseOS Gate would consume the packet;
- `dispatch()` raises `RuntimeError` — calling it is a programming error in P0.1, not a silent no-op.

A packet is a *proposal shape*, not a request. Producing one has no effect anywhere.

## Related existing surface

The older `chaseos-native-source-card` CLI command produces a ChaseOS-shaped review packet plus an operator handoff, stamped with an allowlisted workflow label mirroring the active Hermes-family entries in ChaseOS's canonical workflow registry. It likewise dispatches nothing and consumes no approvals. See [ChaseOS-Native Review Packet](Chaser-Agent-ChaseOS-Native-Review-Packet.md).

## What integration would add later

Shared governance and the Gate approval path · cross-runtime orchestration · shared canonical state · policy enforcement · agent routing · cross-project memory · enterprise-style coordination. All additive; none may become load-bearing for the standalone core.

## Open operator decisions

- **§24.15** synchronisation semantics between standalone memory and ChaseOS memory;
- **§24.16** conflict resolution when standalone and ChaseOS memory disagree;
- **§24.7** whether locally promoted memory is publicly called "canonical memory" or "approved durable memory".

Until these are decided, the adapter stays inactive. Live Gate consumption, approval consumption, and runtime dispatch are explicitly out of scope for P0.1.
