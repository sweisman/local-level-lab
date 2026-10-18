# Final-stretch free-timing comparison

## Question and frozen evidence

Stretch `b4e44ddc0f130ecd45674c78` is the last unresolved stretch. Its
specified-field endpoints have passed both processing-case repeat checks.
The separate zero-field timing profiles completed eight conditional fits and
two controls in 132 native evaluations; all four within-offset comparisons
passed. Both nuisance starts reproduced the smaller cost near a 0.093-second
alignment, compared with the original +0.15-second bound alignment. Fixing time
does not qualify the full fit.

This comparison releases time and all other original active parameters from
the verified lower-cost solutions. It uses only the sealed final-stretch
profile evidence. No other stretch, model or new processing assumption enters
the target population.

## Implementation and checks

`analysis/tests/ilvis0_last_free_time_worker.py` privately adapts the checked
two-case free-time executor. Earlier launchers and candidates remain unchanged.
The original bounded trust solver, full native stationarity and repeated-center
checks, fresh prediction-stability check and repeat-comparison limits remain
in force. Sources, selected input hashes, environment, native kernel, finite
plan and software qualification are sealed before launch. Shared source
directories acquire one exclusive lock each. Every native evaluation is charged
before execution, and interrupted charge transactions block continuation.

For each processing case and original starting solution, retain both verified
profile offsets and choose the smaller saved cost with the existing deterministic
tiebreak. Check the saved starting cost against a fresh native evaluation.
Release time within its original ±0.15-second bounds; never use a conditional
profile pass as full convergence. Save residuals, full Jacobians, packet
boundaries, parameters and failures. Two fresh controls must pass before targets.

## Finite allowance

| Work | Maximum |
|---|---:|
| Fresh controls | 2 identities × 3 diagnostic evaluations |
| Free-timing target fits | 4 identities × 81 fitting evaluations |
| Fresh full checks | 3 diagnostic evaluations per target |
| Charged identities | **6** |
| Optimizer starts | **4** |
| Native evaluations | **342** |
| Allocation | **4 total numerical threads**, one worker |
| Retries | **0** |

Each target's fitting allowance includes one starting-cost reproduction and at
most 80 solver evaluations. At the preceding profile study's approximately
20 seconds per evaluation, exhausting this allowance takes about two hours.
Earlier stopping is possible. Completed or interrupted identities cannot be
retried, and unused allowances from earlier studies cannot be transferred.

## Unchanged assumptions and acceptance

The selected complete interval, original increments, receiver observations,
nominal 200 Hz integration, physical bounds, ±1 degree/hour constant offsets,
coordinate weighting and `h1_v3_tau60` covariance remain unchanged. Both
fixed-zero and profiled upstream-field-removal cases remain separate. No science
measurement is repaired or interpolated.

Every target needs the original full convergence gates. Primary and repeat must
agree separately within each processing case: relative cost difference at most
10⁻⁶ and per-axis prediction RMS difference at most 0.01 metre. Fresh position
stability retains the 1 mm axis-RMS and 1 cm epoch-maximum limits. Failed full
checks remain failures; no numerical limits are relaxed to obtain a result.

Even success requires a separate saved-evidence review of all six model primaries,
controls and required repeats before changing the stretch's disposition. This
trial does not establish global optimality, calibrated statistical significance,
processing provenance or the cause of the measured background field. Preserve
all earlier results and all new failures.
