# Model Card: VibeMatch Lite 1.0

## 1. Model Name

**VibeMatch Lite 1.0**

---

## 2. Intended Use

This recommender suggests a few songs from a small classroom catalog based on a user's preferred genre, preferred mood, target energy, and acoustic preference. It is meant for learning how recommendation logic works, not for use in a real product.

The system assumes that music taste can be represented by a few fixed preferences. That makes the model easy to inspect, but it leaves out many parts of real listening behavior. It should not be used for real user profiling or any high-stakes personalization task.

---

## 3. How the Model Works

The model uses a weighted scoring rule instead of training a machine learning model. Each song gets compared to a user profile, and the score comes from four parts:

- genre match
- mood match
- energy closeness
- acousticness fit

In the final version, genre is weighted at `4.0`, mood at `2.5`, energy closeness contributes up to `2.0`, and acousticness contributes up to `1.5`. After all songs are scored, the recommender sorts the catalog and returns the top matches with score reasons and short explanations.

Compared with the starter code, I implemented the OOP and functional recommenders, CSV parsing, explanation generation, multi-profile CLI output, and tests for the scoring logic.

---

## 4. Data

The dataset contains **16 songs** in `data/songs.csv`. I expanded the starter 10-song catalog by adding 6 more songs to improve genre and mood variety.

Genres represented:

- `lofi` (3)
- `pop` (2)
- `rock` (1)
- `ambient` (1)
- `jazz` (1)
- `synthwave` (1)
- `indie pop` (1)
- `edm` (1)
- `folk` (1)
- `r&b` (1)
- `hyperpop` (1)
- `acoustic` (1)
- `indie` (1)

Moods represented:

- `happy` (3)
- `chill` (3)
- `intense` (2)
- `relaxed` (1)
- `moody` (1)
- `focused` (1)
- `euphoric` (1)
- `tender` (1)
- `sensual` (1)
- `chaotic` (1)
- `reflective` (1)

Even after expansion, this is still a tiny hand-curated dataset. It does not cover many cultures, languages, genres, or listening contexts.

---

## 5. Strengths

- The model is easy to explain because every score comes from visible feature matches.
- It works reasonably well for clear profiles like pop/happy or lofi/chill users.
- The CLI shows both the score reasons and a short explanation, which makes the output more transparent.
- A pop/happy/high-energy listener got `Sunrise City` first, which matched my expectation.
- A rock/intense listener got `Storm Runner` first, which also felt correct.

---

## 6. Limitations and Bias

- The catalog is still very small, so recommendation quality is capped by what is available.
- Genre has the largest weight, so the system can over-prioritize same-genre songs and create a small filter bubble.
- Some genres and moods appear only once, so users with those tastes have fewer chances to get strong matches.
- The model ignores lyrics, artist loyalty, social trends, and long-term listening behavior.
- The acoustic preference is binary, which flattens a more nuanced part of music taste.

If a similar scoring setup were used in a real app, it could serve some listeners much better than others simply because of the data mix and chosen weights.

---

## 7. Evaluation

I evaluated the system in three ways:

- I ran `pytest` to verify recommendation ordering, explanation output, energy sensitivity, acoustic preference behavior, CSV parsing, and sorted top-`k` output.
- I manually tested multiple user profiles and compared the rankings to my expectations.
- I temporarily changed the weights to see how the rankings shifted.

Examples:

- `genre=pop`, `mood=happy`, `energy=0.8` returned `Sunrise City`, `Gym Hero`, and `Golden Hour Run`.
- `genre=lofi`, `mood=chill`, `energy=0.4`, `likes_acoustic=True` returned `Library Rain`, `Midnight Coding`, and `Focus Flow`.
- `genre=rock`, `mood=intense`, `energy=0.9` returned `Storm Runner`, `Gym Hero`, and `Pixel Heartbeat`.
- Lowering the genre weight from `4.0` to `1.5` moved `Golden Hour Run` and `Rooftop Lights` above `Gym Hero` for the pop profile.

I did not use a formal accuracy metric because the project is based on a tiny classroom dataset and a hand-written rule. My main goal was to see whether the rankings felt consistent and explainable.

---

## 8. Future Work

- Let users express multiple favorite genres or moods instead of only one.
- Add a diversity rule so the top recommendations do not cluster too much by style or artist.
- Use more features, such as tempo similarity or valence, in a controlled way.
- Replace the binary acoustic preference with a continuous preference scale.
- Add multiple scoring modes such as genre-first or energy-first.

---

## 9. Personal Reflection

Building this project made recommendation systems feel less mysterious. Even a simple weighted formula can produce outputs that seem surprisingly personalized, which helped me understand why recommender systems can feel smart even before they become very complex.

What stood out most was how quickly bias appears, even in a small classroom simulation. The recommender is only as broad as its data and assumptions, so human judgment still matters when choosing the data, setting the weights, and deciding whether the results are actually fair.
