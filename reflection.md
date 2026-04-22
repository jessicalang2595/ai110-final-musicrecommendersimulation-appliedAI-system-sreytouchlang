# Reflection Notes

## What This Project Became

The original Module 3 project proved that a simple scoring formula could produce recommendations that felt believable. This final version pushed the idea further by asking a harder question: not just "what should the system recommend?" but also "how trustworthy is that recommendation?"

That shift changed the whole project. Instead of focusing only on top matches, I added a retrieval layer that pulls matching genre and mood notes from custom local documents, a specialized explanation layer with constrained styles, and a reliability layer that validates input, flags narrow result lists, scores confidence, and records what happened during a run.

## What Worked

- The system still produces intuitive top picks for clear listener profiles.
- Retrieval-backed notes make the explanations more specific than the original baseline.
- The workflow trace makes the multi-step recommendation process easy to demo and inspect.
- Confidence scores make the lower-ranked songs easier to interpret.
- The self-critique loop helps expose filter-bubble behavior instead of hiding it.
- The evaluation harness made it much easier to summarize system behavior in a repeatable way.

## What Did Not Work Perfectly

- The catalog is still too small to support rich diversity.
- Some profiles naturally fall into repetitive results because the data itself is repetitive.
- Confidence scores are helpful, but they are still heuristic estimates rather than ground-truth accuracy values.
- The retrieval layer is only as good as the small local knowledge base that I wrote for it.

## What Surprised Me

What surprised me most was that the surrounding system behavior changed the feel of the project as much as the ranking logic itself. The scoring model did not need to become dramatically more complex to feel more professional. Adding retrieval, a workflow trace, guardrails, metrics, and self-checks made the system much more convincing because it became easier to inspect and challenge.

I was also surprised that the lofi profile still triggered a diversity warning after reranking. That felt like a good outcome, because it showed the system could admit a limitation instead of pretending the problem was solved.

## Ethics And Responsible Use

This project has clear limitations and bias risks:

- some genres and moods are underrepresented
- the data is hand-curated and not representative
- genre can dominate the recommendations and create a small filter bubble
- the retrieval notes come from a very small handcrafted knowledge base

The main misuse risk would be presenting this as a production-quality music recommender. To reduce that risk, I documented the limitations, printed warnings in the CLI, and made low-confidence behavior visible instead of hidden.

## Collaboration With AI

AI was useful as a collaborator for brainstorming structure and suggesting ways to separate scoring from evaluation. One particularly helpful idea was treating retrieval, confidence, and self-critique as layers around the recommender instead of rewriting the whole model from scratch.

AI was not always right. One flawed suggestion was to penalize repeated genres too aggressively, which would have damaged the ranking quality. That only became obvious after running tests and comparing the new outputs with the original intended behavior.

The biggest lesson for me is that AI works best as a fast design partner, not as a substitute for verification. The code, tests, and outputs still had to prove the idea.
