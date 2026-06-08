# Chaser agent Source Summary Spec

The source summary pipeline is:
```text
raw source
→ normalized source
→ evidence packet
→ source card
→ claims table
→ uncertainty labels
→ actions
→ memory candidates
→ review packet
```

## Required distinctions
- what the source says
- what Chaser agent infers
- what is uncertain
- what conflicts with other sources
- what should become memory
- what should become an action
- what may update the roadmap

Roadmap updates must be **suggestions only**, never automatic writes. Chaser agent can prepare a proposed update packet, but ChaseOS governance decides promotion.
