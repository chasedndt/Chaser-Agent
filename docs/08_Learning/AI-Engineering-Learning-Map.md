# AI Engineering Learning Map

This ladder starts from practical systems work and only reaches evals/fine-tuning after Chaser agent behavior is defined.

| Step | What it is | Why it matters | Chaser agent feature it supports | First exercise |
|---|---|---|---|---|
| 1. Terminal / shell / Git / repo hygiene | Navigating files, running commands, branches, commits, pushes. | Chaser agent is built through reproducible repo work. | Safe commits, build logs, handovers. | Run `git status`, create a branch, run tests, read a diff. |
| 2. Python package structure | `src/`, modules, imports, `pyproject.toml`, venvs. | Prevents scripts from becoming unmaintainable. | `src/chaser_agent/` package. | Add a tiny function and import it in a test. |
| 3. Filesystems and operating systems | Paths, WSL/Windows boundaries, permissions, line endings. | Chaser agent lives on Windows-mounted WSL paths. | Repo safety and artifact locations. | Translate a Windows path to `/mnt/c/...`. |
| 4. Source-grounded summarisation | Preserving what a source says before inference. | Core V0 behavior. | Source cards and claims tables. | Mark source facts vs inferences in a short note. |
| 5. Prompt engineering | Instructions, output schemas, constraints. | Skills/prompts shape review artifacts. | Source-summary skill pack. | Write a prompt that demands uncertainty labels. |
| 6. Harness engineering | Code that runs cases, checks outputs, logs results. | Makes behavior repeatable. | Eval runner and result logs. | Run existing pytest and inspect a JSONL row. |
| 7. JSONL as data format | One JSON object per line. | Useful for eval rows and future reviewed examples. | Golden/smoke datasets. | Validate all golden JSONL files. |
| 8. Evals conceptually | Measuring expected behavior after defining behavior. | Prevents vague quality claims. | Contract evals after Layer 0. | Classify one test as smoke/schema/contract/product-quality. |
| 9. RAG and retrieval | Finding evidence before generating output. | Later evidence layer. | Citation grounding. | Pair a claim with a snippet. |
| 10. Memory consolidation | Moving raw context to candidate/review/promoted states. | Prevents silent memory mutation. | Memory candidate review. | Label a memory candidate as candidate/reviewed/rejected. |
| 11. MCP and tool-use | Resources/tools/prompts and schemas. | Future least-authority tool behavior. | Tool/MCP mini-evals. | Decide whether a case needs a read resource or write tool. |
| 12. Runtime governance | Permission boundaries, audit, approval. | Keeps adapters safe. | Hermes/OpenClaw adapter experiments later. | Write a blocked-action reason. |
| 13. Skill files and SkillOpt-style improvement | Versioned task procedures improved by evals. | Makes reusable behavior testable. | Skill lifecycle and quarantine. | Compare before/after output of a skill on one case. |
| 14. PEFT / LoRA / fine-tuning later | Training or adapting model behavior. | Only useful after reviewed data exists. | Future fine-tuning decision. | Explain why one reviewed example is not enough to train. |
