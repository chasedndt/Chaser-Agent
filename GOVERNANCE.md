# Governance — Chaser Agent

## Status

Chaser Agent is an early-stage, **founder-led** open-source project, MIT-licensed
and developed by ChaseOS Ltd. as the first-party runtime harness derived from the
ChaseOS control plane.

## Ownership & decision-making

- ChaseOS Ltd. owns the project IP and is the canonical maintainer.
- Roadmap and merge decisions are made by the ChaseOS Ltd. maintainers.
- The proprietary ChaseOS Studio, ChaseOS Cloud, and Control Kernel are **separate**
  products and are governed independently; Chaser Agent must remain cleanly MIT and
  must not take a compile-time dependency on those proprietary layers.

## Licence boundary

This repository is MIT. Contributions and forks must preserve that boundary:

- no proprietary ChaseOS Studio/Cloud/Control-Kernel code may be merged here;
- no code that imports those proprietary modules at build/import time.

## Contributions

External code contributions are **not yet accepted** (see `CONTRIBUTING.md`). Before
opening contributions, ChaseOS Ltd. will finalise: a CLA/DCO decision, CI + security
checks, and a maintainer policy. Issues, reproductions, and design feedback are
welcome now.

## Changes to governance

This document may evolve as the project matures. Material changes will be recorded in
the changelog and announced in the repository.
