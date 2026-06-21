# Third-Party Notices — Chaser Agent

Chaser Agent (MIT, © 2026 ChaseOS Ltd.) uses third-party components, each under its
own licence. The upstream MIT licence of a runtime does not automatically cover
every bundled model, skill, asset, or dependency — these are attributed separately.

## Independent upstream runtimes (out-of-process, not vendored)

| Component | Relationship | Licence |
|---|---|---|
| Hermes Agent | governed adapter / out-of-process runtime | third-party MIT (upstream) |
| OpenClaw | governed adapter / out-of-process runtime | third-party MIT (upstream) |

These are independent upstream projects. Chaser Agent integrates with them via
governed adapter glue (original ChaseOS code); it does not vendor their source.
Confirm the exact upstream repository, version, and SPDX identifier before
redistributing or offering managed hosting of either runtime.

## Python dependencies

Runtime and development dependencies are declared in `pyproject.toml`. Each retains
its own licence. Generate a full SBOM (e.g. `SBOM.spdx.json`) before any public
release; this file is a human-readable summary, not a substitute for the SBOM.

## Bundled assets

- Models: see `MODEL_LICENSES.md`.
- Skills: see `SKILL_LICENSES.md`.
