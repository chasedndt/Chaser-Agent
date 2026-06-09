# Chaser agent Research Register

The Excel workbook `Chaser_Agent_Research_Eval_Register.xlsx` is the main operator-facing research/eval register. This Markdown file is the repo-readable mirror for agents and code reviewers. If the two disagree, treat the Excel register as the working operator dashboard and update this mirror deliberately.

## Status vocabulary

- `seed`: initial research signal captured.
- `needs source review`: source or citation still needs checking.
- `accepted signal`: useful signal accepted for planning.
- `rejected signal`: not useful, unsafe, or false.
- `converted to spec`: reflected in a specification doc.
- `converted to eval`: represented by an eval case or rubric.
- `archived`: kept for provenance but inactive.

## Categories

- Memory
- Tool use
- Runtime
- Safety
- Skills
- Summary
- Dataset
- Business/product
- Learning

## Register mirror

| ID | Category | Signal | Use for Chaser agent | Required eval/spec | Status | Verification note |
|---|---|---|---|---|---|---|
| RS-001 | Memory | Dreaming-style memory synthesis points toward reviewable memory consolidation. | Memory states and review queue. | Memory carry-forward, staleness, contradiction evals. | converted to spec | Research intake; verify source details before treating as external fact. |
| RS-002 | Tool use | MCP/tool-use capability should be measurable, not just available. | Tool/MCP mini-evals. | Resource/tool selection, schema validation, forbidden-write denial. | accepted signal | Citation/source review still useful. |
| RS-003 | Safety | High-privilege local agents concentrate trust and credential risk. | Runtime safety boundaries and negative examples. | Prompt-injection, forbidden-tool, skill-quarantine tests. | accepted signal | Treat as governance signal, not product claim. |
| RS-004 | Runtime | Hermes provides lessons in persistent runtime lanes, gateways, skills, and provider fallback. | Hermes adapter notes and runtime readiness checks. | Runtime health, fallback, writeback audit evals. | converted to spec | ChaseOS remains authority boundary. |
| RS-005 | Skills | Skill files can become trainable/evaluated artifacts. | Skill lifecycle and future SkillOpt-style lane. | Skill regression and held-out validation. | converted to spec | Do not implement uncontrolled self-editing. |
| RS-006 | Tool use | MCP education material reinforces resource/tool/prompt separation. | MCP adapter notes and least-authority tests. | Resource/tool/prompt classification eval. | accepted signal | Needs source review before citation-heavy use. |
| RS-007 | Summary | Website/design tasks need taste, visual context, and human rubric checks. | Website design workflow eval. | Human visual/UX rubric. | converted to eval | Operator observation; not a public design claim. |
| RS-008 | Business/product | Trading/business research tasks need source relevance and signal hierarchy. | Trading research workflow eval. | Market-data relevance and uncertainty rubric. | converted to eval | Sensitive examples must be scrubbed. |

## How to use this mirror

1. Capture or update the detailed signal in the Excel workbook.
2. Mirror only the agent-useful summary here.
3. Mark citation-needed items as research intake, not verified truth.
4. Convert accepted signals into specs or eval rows.
5. Archive stale or rejected signals rather than deleting provenance.
