# Chaser Agent v1.0.0 release verification

Verification date: 2026-09-02

## Release scope

- Canon/Core model and transparent production renders.
- Operator-approved ten-state Runtime Format Pack pass 02.
- Deterministic public identity exports for GitHub, documentation, social, X, and Discord.
- Browser-local P0.1 one-time run workspace.
- ChaseOS and ChaseInTech discovery integrations.

## Verified locally

- Chaser Agent test suite: 200 tests passed.
- Runtime workspace: 12 tests passed and the Sites production bundle built successfully.
- ChaseOS Web: production Vite compilation and 64-route prerender completed successfully.
- ChaseInTech: Astro production build completed with 115 HTML pages and zero noncanonical internal links.
- Runtime workspace desktop and mobile layouts were inspected in the in-app browser.
- ChaseInTech desktop and mobile project surfaces were inspected in the in-app browser.
- The real run generated the complete eight-artifact family and preserved copy-on-write human review.

## Boundaries and remaining verification

- Live deployment and public URL readback are separate from local verification and must be recorded after release.
- ChaseOS production-client verification still depends on its hosted Clerk public configuration; no credential was read or copied into this release worktree.
- ChaseInTech's repository-wide Astro type check retains pre-existing unrelated errors; the release-critical production build passed.
- Expressive character rigging, body motion, audio mixing, and full provenance VFX remain later production phases.
- No social account was modified and no marketing post was published by this release.

Visual evidence is retained in the operator-controlled Chaser Agent visual-QA registry and is not part of the public asset contract.
