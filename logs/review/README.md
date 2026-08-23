# Review log

Durable home for operator review packets and session handovers.

Files here are **tracked**, unlike `logs/runs/` (git-ignored run artifacts).
A handover or review packet that lives only in a working tree is one
`git clean` away from being lost, and one deleted-at-root diff away from
being invisible to the next session.

## Contents

- `2026-08-23-operator-floor-walk.md` — score-ready manual worksheet for the three representative source-review runs and the next MarginFlip workflow-episode review.

- `*-operator-review-packet.md` — per-batch review material: the runs to score,
  what to check in each artifact, and the exact `chaser-agent review` command.
- `CODEX_HANDOVER_*.md` — session handovers written for the next runtime.

## Rules

- Public-safe content only. No credentials, private source material, or
  operator-private data.
- Run folders referenced from these documents live under `logs/runs/` and are
  local-only; a reader on another machine will not have them.
- Do not delete a handover to "tidy up". Supersede it with a newer one and say
  so in the new document.
