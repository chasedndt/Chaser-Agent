# Chaser agent Memory Consolidation

Chaser agent uses a Dreaming-style but governed memory review system:
```text
raw context
candidate memory
reviewed memory
promoted memory
stale memory
disputed memory
archived memory
rejected memory
```
Raw context is evidence, not memory. Candidate memory is a proposed durable fact. Reviewed memory has human or evaluator review. Promoted memory becomes active only through approved governance. Stale, disputed, archived, and rejected states prevent old or bad memories from silently controlling future behavior.

No automatic canonical mutation.
