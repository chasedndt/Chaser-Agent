# Chaser Agent Source Card Format

A source card contains source identity, source type/origin/privacy, workflow profile and version, summary, evidence-linked claims, separate Chaser Agent inferences, uncertainty labels, contradiction status, action candidates, memory candidates, review status, promotion status, creation time, and run identity.

The canonical builder is `src/chaser_agent/source_card.py`. `summary/source_card.py` is a compatibility re-export, not a second implementation.

Claims preserve source order and record how the source presents each statement: `reported_result`, `requirement`, `recommendation`, `opinion`, `definition`, `decision`, `constraint`, or `unknown`. A source statement is not labelled fact merely because it appears in the input. Markdown headings are not emitted as claims.

The output remains a review artifact. Profiles may shape analysis but cannot grant authority, execute an action, call a provider/tool, or promote memory.
