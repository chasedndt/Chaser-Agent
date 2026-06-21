# Contributing — Chaser Agent

Thank you for your interest. Chaser Agent is **MIT-licensed** and developed in the
open, but it is early-stage and tightly governed.

## Current contribution status

> **External code contributions are not yet being accepted.**

Per the project governance (see `GOVERNANCE.md`), we are not merging external core
contributions until the contribution policy, CLA/DCO decision, CI/security checks,
and maintainer governance are finalised. This protects the licence boundary between
the MIT Chaser Agent and the proprietary ChaseOS Studio/Cloud/Control Kernel.

What helps right now:

- **Issues:** bug reports, reproductions, and design feedback are welcome.
- **Security:** see `SECURITY.md` (report privately).
- **Discussion:** proposals and use-cases via issues.

## When contributions open

When external contributions open, expect:

- a Developer Certificate of Origin (DCO) sign-off or a CLA;
- tests for any code change (`pytest`);
- no new runtime dependencies without discussion (this project is stdlib-leaning);
- no code that imports proprietary ChaseOS Studio/Cloud/Control Kernel modules —
  Chaser Agent must remain cleanly MIT and independently buildable.

## Local development

```bash
python -m venv .venv && . .venv/Scripts/activate   # or source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

See `START_HERE.md` and `HANDOVER.md` for orientation.
