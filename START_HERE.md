# Start Here — Chaser agent

This repo is the first standalone development lane for **Chaser agent**.

## Purpose
Chaser agent starts with source-grounded summaries, evals, memory candidates, and governed runtime notes. It turns messy sources into reviewable source cards, not uncontrolled chatbot output.

## Evals
An eval is a repeatable test of an AI behavior with an input, expected properties, a rubric, a result, and known failure modes.

## JSONL
JSONL stores one JSON object per line. It is easy to append, stream, diff, validate, and review, so it is a good format for golden cases, outputs, human review rows, and future fine-tuning candidates.

## Human review
Human review prevents automatic promotion. The operator checks grounding, safety, usefulness, and ChaseOS alignment before a candidate becomes memory, action, skill update, or dataset material.

## Source summaries
A source summary separates what the source says from what Chaser agent infers, what remains uncertain, what conflicts, what might become memory, and what might become an action.

## Memory consolidation
Memory candidates are not canonical truth. They move from raw context to candidate memory to reviewed memory only after evidence and operator approval.

## Fine-tuning
Fine-tuning changes model behavior using training examples. It comes later, after stable eval data and reviewed failures exist.
