# Contributing

Review is the point of this project. Skeptical reviews of the physics, the statistics and the code are especially welcome.

- **Physics and statistics:** start with [docs/MATH.md](docs/MATH.md). The "Known approximations" section lists what most needs scrutiny. If you think the analysis favours one model, show it with a synthetic session (`lll synth --truth ...`) that the pipeline misclassifies.
- **Data format:** [docs/FORMAT.md](docs/FORMAT.md) is the contract between app, server and analysis. Changes need a `schema_version` bump.
- **Shared math:** `docs/test_vectors.json` is checked by both `analysis/tests` and the Android unit tests. If you change the model math, update the vectors and both implementations.
- **Tests:** `pytest analysis/tests server/tests` and `cd android && ./gradlew testDebugUnitTest`.
- **Licensing:** contributions are accepted under AGPL-3.0-or-later. New source files carry an SPDX header.
