# Contributing

Review is the point of this project. Skeptical reviews of the physics, the statistics and the code are especially welcome.

- **Physics and statistics:** start with [docs/METHODOLOGY.md](docs/METHODOLOGY.md), then [docs/MATH.md](docs/MATH.md). "Open points" and "Known approximations" list what most needs scrutiny. If you think the analysis favours one model, show it with a synthetic session (`lll synth --truth ...`) that the pipeline gets confidently wrong. Synthetic truth must come from the geometric generator (`analysis/tests/truthgen.py`), never from `lll.models`.
- **Evidence:** every number in the methodology docs comes from `python analysis/tests/evidence.py`. If you change the analysis, regenerate `docs/EVIDENCE.md` and update the text that quotes it.
- **Hardware:** real captures from the IMUs (`lll bench`) are welcome as test fixtures under `analysis/tests/fixtures/`. They pin the decoder to real bytes.
- **Data format:** [docs/FORMAT.md](docs/FORMAT.md) is the contract between app, server and analysis. Changes need a `schema_version` bump.
- **Shared vectors:** `docs/test_vectors.json` holds the model math and hand-built WitMotion packets, and both `analysis/tests` and the Android unit tests check against it. If you change either, update the vectors and both implementations.
- **Tests:** `pytest analysis/tests server/tests` and `cd android && ./gradlew testDebugUnitTest`.
- **Licensing:** contributions are accepted under AGPL-3.0-or-later. New source files carry an SPDX header.
