# Chaser agent Action extraction Skill

Purpose: guide Chaser agent action extraction behavior with source grounding, uncertainty labels, and no automatic writeback.

Trigger: use when a reviewed source or eval case asks for action extraction.

Safety: preserve provenance, avoid secrets, and route memory/actions as candidates only.

Eval: this skill is inactive until matched to a JSONL golden case and human review rubric.
