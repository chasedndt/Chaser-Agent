# AI Engineering Learning Map

This ladder starts from practical systems work, then maths/CS foundations, then prompting and harnesses, and only reaches evals, MCP, runtime governance, and fine-tuning after Chaser agent behavior is defined.

The repo should integrate LLM foundations from the beginning, but not by jumping straight to “run evals.” Language-model fundamentals, evaluation, prompt engineering, PEFT/LoRA, model editing, and RAG only become useful when the systems and maths underneath them are understandable.

| Step | What it is | Why it matters | Chaser agent feature it supports | First exercise |
|---|---|---|---|---|
| 1. Terminal / shell / Git | Navigating files, running commands, branches, commits, pushes. | Chaser agent is built through reproducible repo work. | Safe commits, build logs, handovers. | Run `git status`, create a branch, run tests, read a diff. |
| 2. Python package structure | `src/`, modules, imports, `pyproject.toml`, venvs. | Prevents scripts from becoming unmaintainable. | `src/chaser_agent/` package. | Add a tiny function and import it in a test. |
| 3. Filesystems and operating systems | Paths, WSL/Windows boundaries, permissions, line endings, processes. | Chaser agent lives on Windows-mounted WSL paths and must know where it may read/write. | Repo safety and artifact locations. | Translate a Windows path to `/mnt/c/...` and identify declared output folders. |
| 4. Sets, functions, vectors, matrices | The basic mathematical language of data, transforms, and embeddings. | Evals, schemas, embeddings, retrieval, and model literacy all depend on these. | Dataset rows, source-card transforms, later embeddings. | Describe a source-card transform as a function from input source to output artifact. |
| 5. Probability and conditional probability | Reasoning about likelihood, uncertainty, and evidence. | Chaser agent must label uncertainty instead of pretending guesses are truth. | Uncertainty labels and eval interpretation. | Explain how confidence changes after stronger evidence appears. |
| 6. Embeddings and similarity | Representing meaning as vectors and comparing items. | Later retrieval/RAG and clustering require similarity literacy. | Future evidence retrieval and source grouping. | Compare two short source summaries and describe why they are similar or different. |
| 7. Prompt engineering | Instructions, output schemas, constraints, and safety boundaries. | Skills/prompts shape review artifacts. | Source-summary skill pack. | Write a prompt that demands source facts, inferences, and uncertainty separately. |
| 8. Harness engineering | Code that runs cases, checks outputs, and logs results. | Makes behavior repeatable. | Eval runner and result logs. | Run existing pytest and inspect a JSONL row. |
| 9. JSONL as a data format | One JSON object per line. | Useful for eval rows and future reviewed examples, but not proof by itself. | Golden/smoke datasets. | Validate all golden JSONL files. |
| 10. Evals conceptually | Measuring expected behavior after defining behavior. | Prevents vague quality claims. | Contract evals after Layer 0. | Classify one test as smoke/schema/contract/product-quality. |
| 11. RAG and retrieval | Finding evidence before generating output. | Later evidence layer. | Citation grounding and source retrieval. | Pair a claim with a snippet and mark whether the snippet supports it. |
| 12. Memory consolidation | Moving raw context to candidate/review/promoted states. | Prevents silent memory mutation. | Memory candidate review. | Label a memory candidate as candidate/reviewed/rejected. |
| 13. MCP and tool-use | MCP is an interface standard for resources, tools, and prompts; it is not magic intelligence. | The real value is domain logic and safety discipline underneath the interface. | Later Tool/MCP mini-evals. | Decide whether a case needs a read resource, a write tool, or no tool at all. |
| 14. Runtime governance | Permission boundaries, audit, approval, trust tiers, failure handling. | Keeps adapters from collapsing boundaries across shell, browser, filesystem, credentials, SaaS, and persistent state. | Hermes/OpenClaw adapter experiments later. | Write a blocked-action reason for a forbidden tool call. |
| 15. PEFT / LoRA / fine-tuning later | Training or adapting model behavior. | Only useful after reviewed data exists. | Future fine-tuning decision. | Explain why one reviewed example is not enough to train. |

## MCP stays later

MCP should remain a later topic. It can expose useful resources/tools/prompts, but it does not replace product definition, domain logic, eval design, trust boundaries, or review discipline. Chaser agent should learn MCP after Layer 0, V0 behavior, source-card artifacts, and contract eval concepts are understood.
