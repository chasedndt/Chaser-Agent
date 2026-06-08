# Chaser agent Technical summary Skill

Purpose: guide Chaser agent technical summary behavior with source grounding, uncertainty labels, and no automatic writeback.

Trigger: use when a reviewed source or eval case asks for technical summary.

Safety: preserve provenance, avoid secrets, and route memory/actions as candidates only.

Eval: this skill is inactive until matched to a JSONL golden case and human review rubric.
