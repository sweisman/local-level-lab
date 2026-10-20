# Native observations reach the prediction interface

The new source connects packet-by-packet native predictions and all **27
calibration derivative columns** to the structured uncertainty calculation.
The [finite qualification](../ilvis0-native-source-qualification/README.md) passes
all **24 generated identities**, with exact agreement in native values and
derivatives. Nine deterministic component checks also pass, including all three physical models
under both processing cases, chunked propagation and the complete interface's
required abstention when a nonlinear error bound is missing.

The source accepts a fixed initial state and fitted calibration center, a fixed
coordinate frame, training/future query times and original increment inputs.
Its API accepts no future receiver positions and no fused navigation. Source
receipts bind the input identity, initial state, calibration, kernel/runtime,
coordinate frame and query schedule. A mismatched model label or uncertainty
configuration is rejected.

Those receipts do not prove that a caller's supplied fit or initial state was
estimated using training data alone. A future observed study must verify those
dependencies independently. The current checks also do not supply useful global
nonlinear prediction bounds or establish the receiver-error assumptions. With
those requirements unresolved, the complete interface correctly remains an
unsupported scientific prediction rather than a detection.

The finite study charged 216 native calls and 28,800 packet visits, with no
optimizer starts. No original recording was read, no archival fit ran, and none
of the 53 model preferences changed. The [affine contractor](../ilvis0-training-box-qualification/INTERPRETATION.md)
now passes all 24 frozen controls. The next [generated native test](../ilvis0-native-training-contraction/PLAN.md)
checks its usefulness over the full broad region without changing physical limits.

Implementation: `analysis/lll/ilvis0_native_stream_interface.py`.
Tests: `analysis/tests/test_ilvis0_native_stream_interface.py`.

[Plan](PLAN.md) · [Prediction requirements](../ilvis0-bounded-prediction-controls/NEXT_PLAN.md) ·
[Technical roadmap](../ANALYSIS_ROADMAP.md).
