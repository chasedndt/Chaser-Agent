# Chaser agent Repo Boundary

```text
ChaseOS repo = parent control plane and canonical governance truth.
Chaser agent repo = focused product/runtime implementation and eval lab.
Private datasets = never committed publicly.
```

| Concern | Lives in ChaseOS | Lives in Chaser agent repo | Notes |
|---|---|---|---|
| Canonical governance | Yes | No | Chaser agent can reference boundaries but not override them. |
| Product implementation | Parent context only | Yes | Code, tests, evals, and adapter notes live here. |
| Source intelligence architecture | Canonical design | Productized components | Keep alignment through extraction manifests. |
| Memory truth | Canonical states and Gate | Candidate queues and evals | No automatic promotion. |
| Runtime authority | AOR/Gate policy | Adapter experiments | Adapter behavior must stay bounded. |
| Private datasets | Operator-controlled | Local only under ignored folders | Never commit private data or secrets. |
