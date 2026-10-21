# Reuse compatible prediction certificates

Saved bounds can be reused without repeating their integration when their
inputs, numerical environment, physical domains, reference values, shared
coefficients and error assumptions match exactly. An inspection of the 16
specified-field regions finds compatible earlier future bounds and newer
completed training bounds. This establishes compatibility, not narrower
prediction ranges or a successful new comparison.

The metadata-handling component passes 29 deterministic tests of hashes,
environments, complete parameter columns, domains, shared maps and malformed
inputs. This is data-handling verification, not numerical reuse qualification.

## Proposed rule

1. Verify provider qualification, frozen environment, result seals and artifact
   hashes. A saved completed bound from a later time-limited task is distinct
   from a completed task. Keep the failed task label unchanged. Do not reuse
   a bound implicated in a known-truth or mathematical failure.
2. Require identical source/reference bindings, times, domains, centers,
   coefficient matrices, shared caps, conditioning and error assumptions.
   Reject an incompatible provider rather than silently transferring its rows.
3. When several valid reports describe the same expression on the same
   domain, their componentwise minimum remainder is also a valid bound.
   Preserve the provider selected for each coordinate and the original reports.
   Do not invent an additive decomposition for a mixed certificate.
4. Reconstruct training rows and independently audit their future endpoints
   under the unchanged observation allowance, arithmetic margin and width target.
   Select certificates without consulting future truth or empirical model costs.
5. A fresh group requires every region and query. If coverage is incomplete,
   use only its earlier **complete** certified group range; do not use a partial
   new union. Keep fresh coverage and inherited coverage separate. Intersect
   complete valid group ranges only after checking their coordinate frame and
   physical domain. All six final groups must meet the original target.

This is a separate prospective postprocessing method. It cannot make the
completed direct-only study pass or erase its failures. Metadata handling needs
focused tests. The [known-answer controls](../ilvis0-reused-joint-controls/INTERPRETATION.md)
now pass all 12 cases. A [separate complete-cover comparison](../ilvis0-reused-complete-prediction/PLAN.md)
has completed its separately frozen support/LP allowance: all 40 region
calculations pass, but only four of six cases meet the unchanged width target.
See the [complete outcome](../ilvis0-reused-complete-prediction/INTERPRETATION.md).
No new integration calls, optimizer starts or aircraft observations ran.

Passing would establish usefulness on the existing generated problem only.
Recording-scale bounds, floating-execution assumptions, observational adequacy
and calibrated confidence remain open.

[Current comparison scope](../ilvis0-direct-complete-prediction/PLAN.md) ·
[Next numerical gates](../ilvis0-direct-complete-prediction/NEXT_PLAN.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
