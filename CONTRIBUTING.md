# Contributing

Review is the point of this project. Skeptical reviews of the physics, the statistics and the code are especially welcome.

Start with the [project overview](README.md) and [plain-language methodology](docs/METHODOLOGY.md).
[Developer setup](docs/DEVELOPMENT.md) has installation and build commands. Public guides should
define IMU on first use, explain the experiment without assuming specialist knowledge, describe
the current evidence honestly, and link to readable pages rather than research data files.
Keep session history and personal authorization references out of public explanations.

- **Physics and statistics:** the [technical methodology](docs/METHODOLOGY_TECHNICAL.md), [equations](docs/MATH.md) and [technical validation record](docs/VALIDATION_TECHNICAL.md) preserve the assumptions and unresolved issues. If you think the analysis favours one model, show it with a synthetic session (`lll synth --truth ...`) that the pipeline gets confidently wrong. Synthetic truth must come from the geometric generator (`analysis/tests/truthgen.py`), never from `lll.models`.
- **Evidence:** historical tables come from `analysis/tests/evidence.py`; campaign results have separate frozen records. Keep the readable [evidence summary](docs/EVIDENCE.md) current without replacing historical results. Regenerating simulation tables requires an appropriate compute budget; retain generated detail in `docs/EVIDENCE_TECHNICAL.md`, with its source/configuration limits explicit.
- **Hardware:** real captures from the IMUs (`lll bench`) are welcome as test fixtures under `analysis/tests/fixtures/`. They pin the decoder to real bytes.
- **Data format:** [docs/FORMAT.md](docs/FORMAT.md) is the contract between app, server and analysis. Breaking changes need a `schema_version` bump. Backward-compatible optional metadata and event kinds must be documented; old archives remain immutable and missing metadata stays unknown. External provider tracks remain separate artifacts with their own provenance and terms.
- **Shared vectors:** `docs/test_vectors.json` holds the model math and hand-built WitMotion packets, and both `analysis/tests` and the Android unit tests check against it. If you change either, update the vectors and both implementations.
- **Tests:** `pytest analysis/tests server/tests` and `cd android && ./gradlew testDebugUnitTest`.
- **Licensing:** contributions are accepted under AGPL-3.0-or-later. New source files carry an SPDX header.
