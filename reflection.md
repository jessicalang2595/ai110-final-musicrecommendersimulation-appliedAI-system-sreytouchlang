# Reflection Notes

## Profile Comparisons

`High-Energy Pop` versus `Chill Lofi`:
The pop profile pushed upbeat, low-acoustic tracks like `Sunrise City` and `Gym Hero` to the top, while the chill lofi profile shifted toward `Library Rain` and `Midnight Coding`. That difference makes sense because the strongest score components changed from `pop + happy + high energy` to `lofi + chill + acoustic`.

`High-Energy Pop` versus `Deep Intense Rock`:
Both profiles liked higher-energy songs, so there was still some overlap in energetic tracks, but `Storm Runner` only took first place for the rock profile because it matched both the target genre and the `intense` mood. The rock profile also pulled in `Pixel Heartbeat`, which showed that strong energy can still matter even without a genre match when the catalog has only a few intense options.

`Chill Lofi` versus `Deep Intense Rock`:
These profiles produced the biggest contrast. The lofi listener favored softer, more acoustic tracks, while the rock listener favored `Storm Runner` and other intense songs. This made it easier to see that the same catalog can feel completely different depending on which preferences the scoring rule prioritizes.

## Engineering Reflection

The biggest learning moment for me was seeing how a simple weighted formula can still create outputs that feel surprisingly personalized. Once the recommender produced ranked lists with explanations, it became much easier to connect the code to the user-facing result.

AI tools were helpful for brainstorming structure, checking whether the algorithm was easy to explain, and thinking through experiments. I still needed to verify the logic by running the code, because even a reasonable suggestion is not enough unless the outputs actually match the design.

What surprised me most is that recommendation systems do not need to be very complex to feel convincing. Even a tiny content-based system can look "smart" if the weights happen to line up with human intuition.

If I kept extending this project, I would add more songs, support multiple favorite genres or moods, and introduce a diversity rule so the top results are not always the closest possible matches.
