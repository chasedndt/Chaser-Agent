# JSONL For Evals Explained

JSONL means JSON Lines: one JSON object per line.

## Eval input dataset row
```json
{"id":"case_001","task":"source_card_summary","input":{"title":"Toy Note","text":"Raw source stays separate from reviewed memory."},"expected":{"must_include":["raw source","reviewed memory"]}}
```

## Model output result row
```json
{"id":"case_001","output":{"summary":"The note separates raw source from reviewed memory."},"passed":true,"score":0.88}
```

## Human review row
```json
{"id":"case_001","reviewer":"operator","grounded":true,"notes":"Good boundary, add uncertainty label."}
```

## Fine-tuning candidate row
```json
{"id":"case_001","candidate_type":"fine_tuning","approved":false,"reason":"Needs more reviewed failures first."}
```
