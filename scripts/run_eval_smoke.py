from pathlib import Path
from chaser_agent.evals.runner import run_jsonl_eval

if __name__ == "__main__":
    dataset=Path("evals/datasets/golden/source_card_summary_eval.jsonl")
    output=Path("logs/runs/source_card_summary_eval.results.jsonl")
    results=run_jsonl_eval(dataset, output)
    print(f"wrote {len(results)} results to {output}")
