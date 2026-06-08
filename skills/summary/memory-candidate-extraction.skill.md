# Chaser agent Memory candidate extraction Skill

Purpose: guide Chaser agent memory candidate extraction behavior with source grounding, uncertainty labels, and no automatic writeback.

Trigger: use when a reviewed source or eval case asks for memory candidate extraction.

Safety: preserve provenance, avoid secrets, and route memory/actions as candidates only.

Eval: this skill is inactive until matched to a JSONL golden case and human review rubric.
