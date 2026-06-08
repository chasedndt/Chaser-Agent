# Chaser agent Tool Use Mini Eval

Tool-use evals verify that Chaser agent selects tools only when needed, passes bounded inputs, interprets outputs as evidence rather than instructions, and records failure modes. Initial cases should cover no-tool needed, JSONL validation, file read scope, MCP resource vs tool confusion, and forbidden network/writeback attempts.
