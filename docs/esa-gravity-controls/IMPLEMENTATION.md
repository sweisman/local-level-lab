# Gravity-control implementation

The implementation uses the shared library. The [study plan](PLAN.md) defines
the question, finite allowance and gates. A software pass alone does not qualify
an observed-data fit.

1. **Native interface and derivatives.** Add explicit height-gravity entry points
   to `analysis/lll/ilvis0_native.c` and `analysis/lll/ilvis0_tangent.cpp`.
   Preserve existing entry points and private constant-step callers. Extend
   `ilvis0_exploratory.load_kernel` and `ilvis0_shape.load_tangent` with optional
   `gravity_anchor_height_m`; `None` keeps the original interface and metadata.
   The height adapter binds a fixed anchor while preserving the call signature
   expected by training and forecast code. Evaluate gravity from predicted
   midpoint height, including automatic derivatives through that state.
2. **Focused qualification.** Write failing tests first in
   `analysis/tests/test_ilvis0_height_gravity.py`. Compile historical source from
   the verified ESA pilot archive for constant-mode comparisons. Test analytic
   vertical motion, invalid anchors, value/tangent agreement and all 27 derivative
   columns for all three candidates. Retain both processing cases. Run through
   `analysis/tests/run_numerical.py` and include affected native/compensation
   regression checks.
3. **Independent generated study.** Extend the existing independent Cartesian
   truth generator with explicit climbing/descending profiles and a separately
   implemented gravity law. Keep its old defaults unchanged. Implement a small
   `lll.studies` definition/evaluator and saved-only reporter calling shared rate,
   calibration and motion components. Bind all source, environment, construction
   and finite native-work limits before running the 48-case matrix. Publish every
   failure and verify saved positions, derivatives and accounting without replay.

The independent truth must not use the predictor's gravity helper or equations
to generate the expected trajectory. Later receiver positions cannot enter the
height-gravity forecast. Changing the source requires a new freeze; completed
allowances and historical dependencies remain unchanged. Archive writes are
serialized.
