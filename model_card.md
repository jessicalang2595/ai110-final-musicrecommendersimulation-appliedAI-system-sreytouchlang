# Model Card: VibeMatch Reliable Recommender 2.0

## 1. Model Name

**VibeMatch Reliable Recommender 2.0**

## 2. Base Project

This project extends my Module 3 project, **Music Recommender Simulation**. The original system used a hand-written weighted scoring rule to rank songs by genre, mood, energy, and acousticness. The new version keeps that transparent scoring logic, but wraps it with local retrieval, constrained explanation styles, an observable workflow trace, guardrails, confidence scoring, a self-critique reranking loop, runtime logging, and an evaluation harness.

## 3. Intended Use

This system is designed for classroom learning and portfolio demonstration. It recommends songs from a small catalog based on a user profile and tries to explain how trustworthy each recommendation is.

It is **not** meant for real music personalization, psychological profiling, or commercial deployment. The dataset is tiny, hand-curated, and too narrow to support real-world claims about user taste.

## 4. How The System Works

The system has three connected layers:

1. **Base recommender**
   - genre match: `+4.0`
   - mood match: `+2.5`
   - energy closeness: up to `+2.0`
   - acousticness fit: up to `+1.5`
2. **Retrieval and specialization layer**
   - retrieves matching notes from `knowledge/genre_notes.md`
   - retrieves matching notes from `knowledge/mood_notes.md`
   - supports constrained explanation styles: `plain`, `curator`, `studio`
3. **Reliability layer**
   - normalizes and validates user input
   - clamps invalid energy values into the `0.0-1.0` range
   - penalizes repeated genres or artists when the top-k list gets too narrow
   - assigns confidence scores to each recommendation
   - emits warnings when diversity or reliability look weak
   - prints an observable workflow trace of the recommendation chain

This means the final output is not just a ranked list. It is a ranked list plus retrieved context, specialized explanation text, confidence, self-check notes, warnings, and a trace of the multi-step workflow.

## 5. Data

The dataset contains **16 songs** in `data/songs.csv`.

What the data includes:

- a small range of genres such as `pop`, `lofi`, `rock`, `ambient`, `edm`, and `hyperpop`
- moods such as `happy`, `chill`, `intense`, `focused`, and `reflective`
- numeric fields for energy, tempo, valence, danceability, and acousticness

What the data does not include:

- large-scale listening history
- user behavior across time
- cultural or language diversity at realistic scale
- enough artist variety to fully test fairness or coverage

The retrieval layer adds two custom local knowledge documents:

- `knowledge/genre_notes.md`
- `knowledge/mood_notes.md`

## 6. Strengths

- The model is transparent and easy to explain.
- Retrieval makes explanations more specific than the original baseline.
- The specialized styles make it easy to demonstrate constrained output behavior.
- The system no longer hides uncertainty behind a single score.
- Confidence scores and warnings make the output more honest.
- The self-critique loop helps reduce repetitive top-k lists.
- The evaluation harness makes the system easier to test consistently.

## 7. Limitations And Biases

- The catalog is still very small, so many listener types are underrepresented.
- Genre remains the strongest signal, which can create a filter bubble.
- A reranking penalty can improve diversity, but it cannot invent missing genres or artists.
- Low-ranked songs often have weak confidence because several songs are only partial matches.
- The acoustic preference is still binary, which oversimplifies how people actually describe taste.
- The retrieval layer is still limited to a small handcrafted knowledge base.

The biggest bias risk is uneven coverage: some tastes are better served simply because they appear more often in the data.

## 8. Misuse Risks And Guardrails

Possible misuse:

- treating the system like a real production recommender
- using its suggestions as if they reflect a person's full identity or culture
- hiding low-confidence results behind polished explanations

How I reduce that risk:

- I clearly state that the system is a classroom-scale prototype.
- The CLI prints confidence scores and warnings instead of pretending every answer is equally strong.
- Input guardrails explain when preferences are missing or invalid.
- The model card documents bias and data limitations directly.

## 9. Evaluation Results

I tested the system in two ways:

### Automated tests

- `13/13` tests passed.
- Tests cover scoring behavior, explanation generation, retrieval-backed context, style differences, confidence bounds, guardrail behavior, workflow trace behavior, and diversity reranking.

### Evaluation harness

I ran `python3 -m src.evaluate` on four predefined profiles.

Results:

- average confidence across profiles: `0.67`
- profiles with self-critique penalties: `2/4`
- profiles with diversity warnings: `1/4`
- profiles with input guardrail warnings: `1/4`
- profiles with retrieval-backed explanations: `4/4`
- specialized style output differed from baseline: `True`

What surprised me:

The lofi/chill profile still triggered a diversity warning even after reranking. That was useful because it showed the system can admit that a narrow result set is still narrow, instead of pretending the penalty solved everything.

## 10. Human Evaluation Notes

The strongest profiles still matched my intuition:

- pop/happy users still got `Sunrise City` first
- rock/intense users still got `Storm Runner` first
- lofi/chill users still got `Library Rain` first

The difference is that the system now tells me when it is leaning too heavily on repeated genres, shows the workflow trace that produced the result, and grounds the explanation with retrieved genre and mood notes.

## 11. Collaboration With AI

AI was helpful during this project, but it still needed verification.

Helpful suggestion:

- separating the project into a base scoring layer, a retrieval layer, and a reliability layer made the code easier to test and explain

Flawed suggestion:

- an early idea was to apply a much larger genre penalty, but that would have distorted the ranking too aggressively and pushed clearly good matches too far down the list

The important lesson was that AI suggestions became useful only after I ran tests and checked whether the outputs still matched the design goals.

## 12. Future Work

- support multiple favorite genres or moods
- expand retrieval to a larger external or user-supplied music knowledge base
- replace binary acoustic preference with a continuous preference scale
- add a larger catalog with better artist and genre coverage
- compare the current reranking approach with a diversity-aware scoring formula
- build a small Streamlit interface around the report output
