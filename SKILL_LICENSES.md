# Skill Licenses — Chaser Agent

Skills under `skills/` are first-party unless a skill declares otherwise in its own
manifest/metadata. First-party skills are covered by the repository `LICENSE` (MIT,
© 2026 ChaseOS Ltd.).

| Skill | Origin | Licence |
|---|---|---|
| first-party skills under `skills/` | ChaseOS Ltd. | MIT (repo LICENSE) |
| third-party / community skills | per-skill manifest | per-skill (must be declared) |

Rules:

- A third-party or community skill must declare its own licence in its manifest; do
  not assume the repository MIT licence covers it.
- Skills are scanned for secrets and unsafe patterns before inclusion.
- Bundled data packs inside a skill retain their own licence and must be attributed.
