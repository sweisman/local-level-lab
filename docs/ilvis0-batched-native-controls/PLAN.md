# Batched implementation qualification

The installed-source profiles identify repeated Python array checks, argument
conversion and separate norm calls as substantial costs. Scalar geographic
intervals already store binary64 endpoints; expanding rational denominators
are not the cause of the observed cost.

This separate implementation batches the existing component/global-radius
intersection inside C++, and passes Python-owned contiguous binary64 buffers
after checking their lengths. C++ retains every finite-input, radius-sign,
overflow and floating-point-mode check. It includes the unchanged arithmetic
primitive. No bound formula, point operation order, calibration cap or physical
assumption changes. Earlier candidates and completed studies remain untouched.

Local tests must show exact equality with separate operations, including scalar
and matrix cases, rational fallback, small/large inputs, invalid inputs and
immutable output views. Then repeat the original 24 generated native controls
for all three models and both processing cases. Compare all 348 generated
bounds with their sealed predecessor, including point predictions, the three
coefficient matrices and physical parameter/domain bindings.

## Separate finite allowance

- 24 identities; no retries or optimizer starts.
- At most 78 native evaluations and 19,632 native packet visits.
- At most 348 bounds and 30,144 world/source bound steps.
- Separately reserve 348 source setups, 7,536 source-reference steps and
  7,536 rounded body bounds before execution.
- Four workers with one numerical thread each.
- Original cooperative 60-second bound limit and 600-second overall limit.
- Original center, stationary-pose, derivative and containment acceptance limits.

Freeze code, saved generated inputs, matched comparison values, environment and
compiler before launch. Every native control and exact comparison must pass.
This qualifies implementation equivalence, not useful complete prediction
widths or observational confidence. A successful result permits a separately
frozen long-history runtime/range comparison. No aircraft originals, protected
ESA observations or new scientific fits enter this study.

[Roadmap](../ANALYSIS_ROADMAP.md) ·
[Earlier runtime profiles](../ilvis0-source-runtime-profile-v2/README.md).
