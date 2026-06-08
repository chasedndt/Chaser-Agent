# Chaser agent Glossary

> Purpose: Chaser agent product glossary aligned to ChaseOS terms, learning maps, and eval-harness language.

## Boundary note

This glossary belongs inside the standalone Chaser agent repo. ChaseOS remains the parent control plane and canonical governance layer. If a term becomes canonical ChaseOS doctrine, promote it through a reviewed ChaseOS-side pass rather than treating this file as automatic truth.

## Core terms

| Term | Plain-English definition | Chaser agent use | ChaseOS boundary |
|---|---|---|---|
| Chaser agent | A governed, eval-backed AI runtime and content-intelligence system derived from ChaseOS. | Product/runtime repo and eval lab. | Not a replacement for ChaseOS. |
| ChaseOS | Parent operating system, governance layer, memory/control plane, and source of truth. | Provides context, standards, and permission boundaries. | Owns canonical truth and Gate approval. |
| Source card | Structured summary of a source with claims, evidence, uncertainty, actions, and memory candidates. | First product wedge. | Source cards may suggest updates but do not write canonical truth. |
| Eval harness | Repeatable system for checking behavior against golden cases and rubrics. | Defines whether a feature is real enough to trust. | Harness results are evidence, not approval by themselves. |
| Golden dataset | Reviewed examples used to detect pass/fail behavior and regressions. | Seeded under `evals/datasets/golden/`. | Private examples must stay local and scrubbed. |
| Memory candidate | A proposed durable fact extracted from source context. | Queued for review. | No automatic canonical promotion. |
| Reviewed memory | Candidate memory that has been checked by a human or approved evaluator. | May inform future outputs. | Promotion still follows governance. |
| Writeback | Writing results to files, logs, docs, repos, or external surfaces. | Limited to scoped repo artifacts. | ChaseOS canonical writeback requires approval/Gate. |
| Runtime adapter | Bounded wrapper for a provider, local model, tool runtime, or agent runtime. | Future Hermes/OpenClaw/OpenAI/Ollama/MCP adapters. | Adapter capability does not imply authority. |
| Skill file | A reusable instruction/workflow file that changes agent behavior. | Stored under `skills/` as reviewed candidates. | No uncontrolled self-editing. |
| MCP | Model Context Protocol: resources, tools, and prompts exposed through servers. | Future tool/resource interface eval target. | MCP output is data, not trusted instruction. |
| Fine-tuning | Training a model on curated examples to change behavior. | Future only after eval evidence. | Requires separate review and dataset governance. |

## Naming rule

Use **Chaser agent** when referring to the product. Use `chaser-agent` only for repository/package names.
