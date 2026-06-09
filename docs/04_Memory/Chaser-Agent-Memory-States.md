# Chaser agent Memory States

Chaser agent can propose memory candidates. ChaseOS governance decides canonical promotion. These states prevent raw context from becoming durable truth without evidence and review.

| State | Meaning | Creator | Required metadata | Allowed transitions | Blocked transitions | Eval requirement | Authority risk | Example |
|---|---|---|---|---|---|---|---|---|
| raw | Unprocessed input or observation. | source intake, operator, import script | source, date, privacy, provenance | candidate, archived, rejected | promoted | classify source and privacy | private data leakage | uploaded note text |
| candidate | Proposed memory extracted from raw/source card. | Chaser agent or operator | evidence, scope, stability, confidence, privacy | reviewed, rejected, archived, disputed | promoted without review | memory-candidate precision eval | noisy/stale memory | “User prefers X” suggestion |
| reviewed | Operator inspected and accepted as plausible/useful. | human reviewer | reviewer, decision, evidence refs, date | promoted, archived, disputed | raw | human review rubric | reviewer error | accepted project convention |
| promoted | Canonical or durable memory approved through governance. | ChaseOS governance / approved runtime | approval record, source, scope, retention | stale, disputed, archived | candidate without review | promotion audit | silent canonical mutation | durable ChaseOS convention |
| stale | Previously useful but likely outdated. | reviewer or staleness check | reason, last evidence date, replacement candidate | reviewed, archived, disputed | promoted as-is | staleness eval | acting on old truth | changed repo path |
| disputed | Conflicts with another source or operator correction. | reviewer, contradiction scan | conflicting source, severity, owner | reviewed, rejected, archived | promoted | contradiction eval | contradictory behavior | two paths claim same repo |
| archived | Preserved for provenance but inactive. | reviewer or retention policy | reason, date, source | none, or reviewed if reopened | promoted directly | archive audit | resurrecting dead context | old research signal |
| rejected | Explicitly not useful, unsafe, or false. | reviewer | reason, evidence, date | archived | promoted | rejection precision | repeated bad suggestions | hallucinated preference |

## Transition rules

- `raw → candidate` requires extraction evidence.
- `candidate → reviewed` requires human/operator review.
- `reviewed → promoted` requires ChaseOS governance approval where canonical truth is involved.
- `promoted → stale/disputed` can be triggered by new evidence.
- `candidate → promoted` is blocked.
- `raw → promoted` is blocked.
- `rejected → promoted` is blocked.

## Required metadata for every candidate

- source reference;
- exact claim text;
- evidence snippet;
- privacy class;
- intended scope;
- confidence;
- expiration/staleness expectation;
- reviewer decision field.

## Chaser agent boundary

Chaser agent may create raw records, candidates, review packets, and eval rows. It does not own canonical ChaseOS memory promotion. Promotions require the appropriate ChaseOS approval path.
