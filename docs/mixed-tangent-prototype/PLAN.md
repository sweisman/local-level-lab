# Faster numerical derivatives: isolated prototype

## Question

Can the software retain its wider-precision position and residual calculation
while computing derivatives in ordinary binary64 arithmetic? Derivatives guide
the optimizer; they must not feed back into the physical position calculation.
The aim is lower runtime without changing the measurements, physical model,
calibration bounds or stopping and accuracy rules.

## Isolation

Use a separate derived-source adapter. Preserve the wide scalar path, all
26/27 derivative columns, clock dispatch, profile mapping, query fractions and
native interface. Change only derivative storage and derivative coefficients.
Reuse the shared loader in a private function namespace, with exact source
hashes. Do not patch its globals or edit a running study's dependencies.

The metadata transformation accepts already-generated C++ text, so its tests
need no numerical imports. Native compilation and comparison wait for a free
core through the existing shared test queue.

## First gate

Run three metadata checks and six real-native cases: all three physical
candidates under both processing assumptions. Use the existing two-second
known-motion fixture and one fixed nonzero parameter vector. Require bitwise
identical predicted positions and residuals, unchanged boundary counts and
every derivative column within the fixed numerical tolerance. Verify that the
original loader and arithmetic remain untouched.

One source-bound test execution is allowed, with one numerical thread and three
reserved threads. It waits at most eight hours for a completed shard of the
current study to release its core. No retry, original-data read, fit or observed
model comparison is authorized. The native checks make 24 short kernel calls
across six cases, plus twelve per-case compiler invocations at most.

Passing these small checks does not qualify a replacement method or establish
a speed improvement. A separate finite long-record benchmark, followed by
training/forecast qualification, is required before any observed fitting.
If bitwise value agreement fails, preserve the failure; do not weaken that
requirement merely to accept the prototype.

The active noisy-data study, existing evidence and protected confirmation
groups remain unchanged.

[Reproducibility](../REPRODUCIBILITY.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
