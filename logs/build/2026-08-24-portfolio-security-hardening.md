# Build Log — Portfolio Security Hardening

**Date:** 2026-08-24

**Branch:** `codex/2026-08-24-chaser-url-scope-hardening`

**Base:** `89777ffd1374b18d6c139c0fb1359e59ed47ba46`

## Repo-truth delta

- The newer architecture/eval branch was clean and ahead of the remotely tracked standalone branch.
- Provider and tool execution remain absent, with default-deny/static independence tests already present.
- URL scopes compared the host then used a raw path prefix; scheme downgrade, non-boundary prefix and encoded traversal were not all refused.
- Clean Windows worktrees exposed three reproducibility issues: child CLI imports, manifest path keys and unexpanded JSONL globs.

## Changes

- Require exact HTTP scheme, hostname and effective port; reject URL userinfo and invalid ports.
- Repeatedly decode and canonicalise URL paths, reject backslash/NUL confusion and require exact path-segment containment.
- Add downgrade, port, userinfo, sibling-prefix, encoded traversal and valid-descendant tests.
- Correct `SECURITY.md`: P0.1 has no provider credential reader.
- Give test subprocesses the clean-checkout `src` path, make research config keys OS-independent and expand JSONL globs inside the validator.

## Verification

- Targeted tool/independence: 52/52.
- Targeted changed surfaces: 49/49.
- Full suite: 212/212.
- Nine JSONL datasets validated: 21 golden/smoke rows, 30 contract rows and 1 public-pending workflow episode.

## Boundaries

No provider SDK/call, credential read, tool execution, MCP/browser runtime, publication, spend, deployment, memory promotion, training or ChaseOS canonical mutation occurred. The dirty primary mascot work remained untouched.
