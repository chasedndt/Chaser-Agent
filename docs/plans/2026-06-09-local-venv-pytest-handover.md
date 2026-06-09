# ChaseOS Local Venv + Pytest Handover

Date: 2026-06-09
Runtime lane: Hermes / Optimus
Workspace: `C:\Users\chaseos\Documents\chaseos_obsidian`
WSL path: `/mnt/c/Users/chaseos/Documents/chaseos_obsidian`

## Purpose

This handover is for using a separate ChatGPT study/explanation session alongside the live ChaseOS repository on this computer. It records what was configured, what was verified, what is deterministic, what still needs attention, and how to work manually through the docs without losing sync with the repository.

## What was configured on the computer

### Local Python environment

The repository already had a WSL/Linux virtual environment:

```text
/mnt/c/Users/chaseos/Documents/chaseos_obsidian/.venv
```

It points to a uv-managed CPython:

```text
Python 3.11.15
.venv/bin/python -> /home/chaseos/.local/share/uv/python/cpython-3.11-linux-x86_64-gnu/bin/python3.11
```

This is a **WSL/Linux venv**, not a Windows `Scripts\\python.exe` venv. Use it from WSL/terminal commands like:

```bash
cd /mnt/c/Users/chaseos/Documents/chaseos_obsidian
PYTHONPATH=. .venv/bin/python -m pytest <test-path> -q
```

### Installed test dependencies

Installed into `.venv` with uv:

```bash
uv pip install --python .venv/bin/python pytest pytest-cov pyyaml
```

Verified installed versions:

```text
Python: 3.11.15
pytest: 9.0.3
PyYAML: 6.0.3
pytest-cov: 7.1.0
coverage: 7.14.1
```

### Project dependency config update

`pyproject.toml` now has a `dev` optional dependency group so future setup has a stable target:

```toml
[project.optional-dependencies]
dev = [
    "pytest>=9.0.0",
    "pytest-cov>=7.0.0",
    "PyYAML>=6.0.0",
]
```

Future intended setup command:

```bash
cd /mnt/c/Users/chaseos/Documents/chaseos_obsidian
uv venv .venv --python 3.11
uv pip install --python .venv/bin/python pytest pytest-cov pyyaml
```

Use `PYTHONPATH=.` while this repo remains in local/source form and is not cleanly installed as an editable package.

## Verification results

### Pytest smoke test passed

Command:

```bash
PYTHONPATH=. .venv/bin/python -m pytest runtime/studio/test_voice_mode_main_nav.py -q
```

Result:

```text
2 passed in 3.08s
```

### Import smoke passed

The venv can import:

- `pytest`
- `yaml`
- `runtime.cli.main` when `PYTHONPATH=.` is set

### One existing regression file currently fails

Command:

```bash
PYTHONPATH=. .venv/bin/python -m pytest runtime/studio/shell/test_voice_mode_backlog_surface.py -q
```

Result:

```text
2 failed, 2 passed in 6.72s
```

Observed failure cause:

- The test expects exact strings such as `No microphone` and `Microphone capture`.
- The current UI/registry text appears to describe the same safety boundary with different wording.
- This is not a pytest installation failure. It means pytest is now working and finding real repo/test drift.

Suggested next fix pass:

1. Read `runtime/studio/shell/test_voice_mode_backlog_surface.py`.
2. Read current Voice Mode UI and registry text:
   - `runtime/studio/shell/frontend/index.html`
   - `runtime/studio/shell/panel_registry.py`
3. Decide whether the product text should restore the expected exact wording, or whether the test should be updated to match the current canonical wording.
4. Prefer keeping explicit safety wording in the UI/registry: no microphone capture, no provider calls, no runtime dispatch, no writes.
5. Re-run the focused test.

## What “deterministic” means here

In this repo/workflow, **deterministic** means: if we run the same command against the same files and same environment, we should get the same result every time.

For ChaseOS development, deterministic usually means:

1. **Pinned or declared dependencies**
   - Example: pytest is installed in `.venv`, not guessed from the global machine.
   - `pyproject.toml` declares the dev tools we expect.

2. **Repeatable commands**
   - Example:
     ```bash
     PYTHONPATH=. .venv/bin/python -m pytest runtime/studio/test_voice_mode_main_nav.py -q
     ```
   - Anyone can run that command and see whether it passes.

3. **No hidden manual state**
   - A test should not depend on “I clicked this earlier” or “a random browser was open”.
   - If a setup step is required, write it down.

4. **Stable proof instead of vibes**
   - “It works” is not enough.
   - A deterministic result is: `2 passed in 3.08s` or `2 failed, 2 passed` with a specific failure trace.

5. **Safe automation boundaries**
   - If a feature is only a read-only surface, tests should prove it does not secretly write files, call providers, consume approvals, or mutate canonical knowledge.

Plain English: deterministic means ChaseOS can become an operating system instead of a pile of one-off manual steps. Every important behavior gets a repeatable command, repeatable test, or repeatable document trail.

## Should you now read the docs manually from the start?

Yes — but not as a rewrite-from-zero exercise.

Recommended manual workflow:

1. Start with the top-level orientation docs:
   - `README.md`
   - `PROJECT_FOUNDATION.md`
   - `ROADMAP.md`
   - `CORE_MANIFEST.md`

2. While reading, keep a note with three columns:
   - **This is true now**
   - **This sounds stale or overclaimed**
   - **This needs a test/proof command**

3. Do not manually edit large sections immediately.
   - Mark issues first.
   - Then make one small pass at a time.
   - After each pass, run focused tests/searches.

4. For anything product-facing, ask:
   - Is this built, partial, planned, or blocked?
   - Is this safe to claim publicly?
   - Is this a read-only surface or an execution surface?
   - Does this need approval/Gate authority?

5. For anything runtime-facing, ask:
   - Is it Hermes, OpenClaw, Claude/Archon, Codex, or generic?
   - Is it active, shadow-only, proposed, or reference-only?
   - Is there an Agent-Activity/build-log trail?

This lets your separate ChatGPT study session help you understand the docs while Hermes/Optimus keeps the computer-side repo work grounded in files and tests.

## How to work hand-in-hand with a study ChatGPT session

Use this pattern when asking the study chat for help:

```text
I am working in the local ChaseOS repository at:
C:\Users\chaseos\Documents\chaseos_obsidian

Current WSL path:
/mnt/c/Users/chaseos/Documents/chaseos_obsidian

The local WSL venv is:
.venv/bin/python

Pytest command shape:
PYTHONPATH=. .venv/bin/python -m pytest <test-path> -q

Please help me understand this file/section conceptually. Do not invent repo state. If you suggest a change, label whether it is documentation-only, test-only, product UI, runtime behavior, or authority-changing.
```

When the study chat gives advice, bring it back to Hermes/Optimus as one of:

- “Audit this claim against the repo.”
- “Turn this into a small plan.”
- “Write the failing test first.”
- “Patch only this section.”
- “Run the verification command.”

## Current known repo/git state from this session

At the time this handover was created:

- Workspace path: `/mnt/c/Users/chaseos/Documents/chaseos_obsidian`
- Git branch reported earlier: `codex/2026-06-09-voice-mode-panel-under-main`
- There was no commit yet and no remote configured in this repo from WSL.
- The repository has many untracked files, so push/commit flow needs deliberate setup before publishing.

Do not assume GitHub has this state until a remote is configured, a commit exists, and push succeeds.

## Immediate next practical steps

1. Keep using the local venv:
   ```bash
   cd /mnt/c/Users/chaseos/Documents/chaseos_obsidian
   PYTHONPATH=. .venv/bin/python -m pytest runtime/studio/test_voice_mode_main_nav.py -q
   ```

2. Fix or re-baseline the current Voice Mode backlog regression:
   ```bash
   PYTHONPATH=. .venv/bin/python -m pytest runtime/studio/shell/test_voice_mode_backlog_surface.py -q
   ```

3. Continue manual README/Foundation review from the beginning, but record issues first before editing.

4. Once Studio Runtime Control Plane is ready, this handoff pattern should move into Studio as:
   - local repo state
   - current test command
   - active failing tests
   - read-only handover summary
   - next approval-safe action

## Summary

The local test environment is now usable from WSL. Pytest is installed and verified. A focused test passes, and another focused test now exposes real text-contract drift in the Voice Mode safety surface. The repo is ready for iterative, deterministic development: read docs, mark claims, write/adjust tests, patch narrowly, verify with commands, and keep handovers like this synchronized with the separate study chat until ChaseOS Studio can own that control-plane workflow directly.
