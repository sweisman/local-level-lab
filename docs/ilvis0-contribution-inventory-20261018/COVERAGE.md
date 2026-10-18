# Which saved fits can support the next comparison?

The inventory covers **318 final primary fits**: three models, two processing
assumptions and 53 preselected stretches. It follows the current qualified ledger
and preserves the exact primary parameter points.

| Saved-data coverage | Fits | Meaning |
|---|---:|---|
| Ready | 164 | Parameters, residual cost, full Jacobian, receiver layout and saved times passed the consistency checks. |
| No declared saved linearization | 133 | The published fit does not name a saved residual/Jacobian artifact. This includes all 72 first-pass fits from the original twelve completed stretches. |
| Saved arrays need time context | 20 | The arrays are present, but the required saved epoch times are unavailable through the fit's declared references. The inventory records the precise validation reason. |
| Unresolved artifact reference | 1 | The declared artifact digest was not found at the published path or among that comparison's recorded inputs. |

**Eighteen stretches have all six primary fits ready.** They provide the first
matched set for full-position, horizontal-only and height-only sensitivity checks
at unchanged parameters. Availability determined this set; no result from a
coordinate projection was used to choose it. It is a subset of the existing
53-stretch study, not new independent flight evidence.

The inventory's technical status `incompatible_saved_artifact` covers the twenty
missing-time-context cases. It does not mean the IMU recording is corrupt or its
model comparison has failed. Similarly, “not saved” concerns a reusable array
file, not convergence of the completed fit. All 53 numerical model comparisons
remain complete and globe-preferred.

## What comes next

First compare the three receiver-coordinate objectives across the eighteen
complete artifact sets, with the proper covariance and every nuisance column
retained. Freeze the exact operation limits and inputs before that calculation.
Those fixed-parameter diagnostics will show how the existing predictions behave
under different constraints; they will not establish newly optimized ablated
models or an isolated gyroscope result.

For the twenty context gaps and single unresolved reference, follow the recorded
provenance to see whether compatible public copies already supply the missing
metadata. Preserve this inventory unchanged; any successful follow-up gets its
own record. The remaining array gaps may need separately budgeted predictions at
saved parameters. They do not require refitting merely to recreate diagnostics.

[Full inventory and checks](README.md) · [CSV](inventory.csv) ·
[All stretch metadata](../ilvis0-current-findings-20261015/ANALYTICS.md).
