# Maths For Chaser agent

This handout builds the maths intuition needed for Chaser agent without jumping straight to advanced eval implementation.

| Concept | Plain-English explanation | Where it appears in Chaser agent | University module link | First mini-exercise |
|---|---|---|---|---|
| Sets and functions | Sets collect things; functions map inputs to outputs. | Dataset rows and source-card transforms. | Mathematics for Computer Science, Programming. | Treat source text as input and source card as output. |
| Sequences | Ordered lists. | JSONL rows, run logs, action steps. | Programming, Algorithms. | Number each step in the V0 loop. |
| Vectors | Lists of numbers representing features. | Future embeddings and scoring. | Maths, ML/AI. | Represent a rubric score as `[grounding, usefulness, safety]`. |
| Matrices | Tables of numbers. | Batches of vectors/results. | Advanced Mathematics. | Make a table of cases by rubric scores. |
| Dot product | Measures aligned magnitude between vectors. | Similarity/ranking intuition. | Linear Algebra. | Compute whether two simple score vectors point in same direction. |
| Cosine similarity | Measures direction similarity independent of size. | Future retrieval/embedding search. | ML/AI, Advanced Maths. | Compare two short bag-of-words vectors. |
| Probability | How likely an event is. | Uncertainty labels and eval interpretation. | Probability/Statistics. | Estimate probability a claim is unsupported. |
| Conditional probability | Likelihood given another fact. | Confidence after evidence appears. | Probability/Statistics. | Ask: probability action is useful given source is weak? |
| Distributions | Patterns of values. | Score distributions over eval runs. | Statistics. | Plot or list pass/fail counts by eval family. |
| Entropy / cross-entropy intuition | Uncertainty and surprise; training loss intuition. | Later model literacy. | ML/AI. | Explain why a confident wrong answer is costly. |
| Gradient descent intuition | Stepwise reduction of loss. | Later training literacy. | Advanced Maths, ML/AI. | Imagine adjusting a prompt to reduce one failure type. |
| Loss functions | A penalty for wrong outputs. | Future scoring/training discussion. | ML/AI. | Define a penalty for unsupported claims. |
| Precision | Of proposed positives, how many were correct. | Memory/action candidate quality. | Statistics, ML/AI. | Count useful memory candidates / all proposed candidates. |
| Recall | Of all correct items, how many were found. | Claim/action extraction coverage. | Statistics, ML/AI. | Count found claims / expected claims. |
| F1 | Balance of precision and recall. | Eval summary metric. | ML/AI. | Explain why high precision but low recall may still fail. |
| Confusion matrix | Counts true/false positives/negatives. | Classifier/eval diagnosis. | ML/AI. | Build a 2x2 for memory candidate accept/reject. |
| Ranking metrics | Whether best items are near the top. | Future retrieval and action prioritization. | Algorithms, ML/AI. | Rank actions by usefulness and inspect top 3. |
| Embeddings | Vectors representing meaning. | Future retrieval and clustering. | ML/AI. | Describe what similar source cards should cluster together. |
| Confidence intervals | Range around a measured estimate. | Benchmark interpretation. | Statistics. | Explain why 3 toy rows cannot prove product quality. |
| A/B testing intuition | Comparing version A and B under a metric. | Skill/prompt improvement. | Statistics, Software Engineering. | Compare two source-card prompts on the same case. |
| LoRA intuition | Small trainable adaptation layered on a model. | Future fine-tuning decision only. | ML/AI. | Write why LoRA waits until reviewed datasets exist. |
