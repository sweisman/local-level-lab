# Connect training information to a declared error model

The sparse five-observation problem cannot meet its original 20 m north-width
target: accepted saved alternatives already differ by about 23 m. Preserve that
result. The one-second diagnostic excludes simultaneous support for the original
point and selected pair in four cases; two still allow it. Neither result is an
outer uncertainty range or a test of the aircraft's Earth-model preference.

## The next connection

1. Keep the real prediction protocol separate from the sparse software benchmark.
   The earlier retrospective proposal uses 292 training receiver epochs and
   147 later epochs. A test using only five earlier observations does not reproduce
   that information. Check exact time association and clock support before adopting
   a complete-cadence generated fixture; preserve existing inputs and targets.
2. Compare saved trajectory differences under common, explicitly declared error
   laws before spending another nonlinear search. The previously declared receiver
   sensitivities use 10- and 300-second correlation times, shared offset and
   full-record drift anchors. These are assumptions, not measurements of GPS error.
   Keep them identical across physical candidates and exclude future observations.
3. Keep accumulated IMU noise separate from receiver noise and constant calibration.
   Existing joint-error software supports a supplied constant-coupling law.
   Receiver-only checks cannot qualify the complete aircraft error budget. Qualify
   any additional trajectory-dependent approximation separately.
4. Retain every calibration coordinate, its correlations and active bounds.
   Local derivative terms can diagnose cancellation; they do not enclose the full
   nonlinear domain. Do not tighten device bounds or relax width targets to obtain
   a pass. Whole-period coverage and numerical/clock guards still need qualification.

The [receiver metadata inventory](../ilvis0-receiver-metadata/README.md) establishes
what information is already available without original-file reads. It does not
establish covariance: no saved recording lists GST/GBS sentences, and the large
unparsed part of the primary stream remains unidentified. Checksummed quality-field
extraction may support further work, but GGA/DOP values alone are not independent
noise estimates. Exact hardware identification remains supporting work, not a
prerequisite for clearly stated software sensitivity tests.

Any next numerical comparison needs its own finite source/input/environment
freeze, allowance and acceptance rules. There are no queued optimizer retries
or observed aircraft fits. V01 remains unqualified; its failure does not authorize
dependent V02 fits or use of protected ESA confirmation data.

[Completed diagnostic](README.md) · [Error assumptions](../PREDICTION_ERROR_ASSUMPTIONS.md) ·
[Technical roadmap](../ANALYSIS_ROADMAP.md).
