# Selective-precision arithmetic: long-record check

The [fresh ESA solver comparison](OBSERVED_DISPATCH_FRESH_RESULT.md) passed
all 16 pairs and all eight settings on a new window of the development
flight. The largest spread among near-tied predictions was 0.265 mm.
The [saved trial-work audit](OBSERVED_TRIAL_WORK_RESULT.md) finds that a
value-only proposal check would skip full derivatives on just one pair.
It could remove 3.1% of wide and 8.2% of selective derivative calls before
the cost of the additional checks. A [short recorded timing test](ESA_SHORT_FIT_TIMING_RESULT.md)
measured 2.19–2.84× fit CPU speedups with equivalent globe fits. The
[20-minute timing study](ESA_FULL_FIT_TIMING_RESULT.md) confirmed 1.69–1.72×
fit CPU speedups for its two globe pairs.

The [held-out accuracy check](ESA_DISPATCH_ACCURACY_RESULT.md) then compared the
32 sealed paths with 400 later receiver positions. Four of 16 primary forecasts
met the full-horizon limits. No fits were repeated.
The [scope audit](ESA_DISPATCH_SCOPE_RESULT.md) counts these as two unique
settings and verifies that solver and start change none of the accuracy flags.

The new isolated prototype keeps wider precision for the ten parameter
sensitivities that missed the tolerance in the previous long-record benchmark.
Its other seventeen derivative directions use ordinary precision. The
physical-value calculation and output interface still follow the unchanged
wide reference.

The initial six generated two-second cases passed bitwise position and
residual checks, timing-boundary checks, and every 26/27-column derivative
comparison. The separate frozen twenty-minute study has now completed all six
physical-candidate/processing-setting combinations. Its saved arrays show
**zero derivative tolerance violations**, bitwise-identical positions and
residuals, and correct timing boundaries. All 12 native calls and all six
construction journals verify against their charged limits. No optimizer was
started and no observed or protected recording was read.

On these generated native calls, the selective version ran 2.03–2.21× faster
than the unchanged wide reference. That is a kernel measurement, not a
whole-fit speed measurement. The [separate two-minute paired fitting and
prediction study](paired-qualification/README.md) passes all six generated
cases. The [twenty-minute paired study](long-fit-study/README.md) also passes
all six: both variants converge and meet the prediction screen, and their
largest matched forecast difference is 1.63 × 10⁻⁹ m. A [separate whole-fit
timing study](timed-fit-study/README.md) repeated all six cases and measured
2.38× median fit CPU speedup, with every case faster. The first long-fit
release stopped on an adapter import before charging a case; its failure is
preserved. The earlier all-ordinary derivative prototype still fails its
long-record tolerance check. A [same-source paired ESA check](../esa-observed-hybrid/PLAN.md)
finished with [21 of 24 pairs passing](../esa-observed-hybrid/combined/README.md),
so the faster method is **not qualified** for observed-data replacement.
At six saved failed-fit points, the values match exactly but the derivative
columns differ by up to about one micrometre per normalized parameter unit.
A separate revised prototype widens the two attitude columns with the largest
differences. Source generation and a six-case, two-second generated physical
comparison now pass: values and differences match the wide method bitwise,
and all derivative columns meet the fixed local tolerance. This short control
does not qualify substitution in the 20-minute observed fits.
The [six saved-point ESA check](../esa-observed-hybrid/same-point-v2/README.md)
also passes its predeclared improvement gate at every point: position values
and timing boundaries remain identical, while the largest derivative difference
is at least ten times smaller than before. No model was refitted, so the
original 21/24 observed substitution result remains unchanged.
The established wide method remains in use. These checks make no Earth-model
decision.

A [model-declared selection](dispatched-fit-study/README.md) has now passed six
separate generated two-minute paired fits. It chooses the faster selective
tangent for the two globe candidates and wide precision for the flat candidate
before fitting. The largest matched position difference was 1.40 × 10⁻⁹ m.
This verifies the generated fit path; observed use remains gated.

The [sixteen-case observed dispatch study](OBSERVED_DISPATCH_PLAN.md) checked
the globe cases on saved ESA development inputs. Its first release closed on
a technical path error before any native calculation; the preserved failure
is described in the [correction note](OBSERVED_DISPATCH_V2_ADDENDUM.md).
The corrected run sealed all 16 fits under 1,240 charged native calls. The
[independent saved-result audit](../esa-observed-model-dispatch-v2/README.md)
replayed every pair and retained the earlier flat numerical failure. All
16 matched forecasts pass the 0.01 m comparison, but only **5 of 8**
training-selected primary starts agree. The faster method therefore **does not
qualify** for observed-data replacement under its frozen rule.

The three switched groups have nearly tied training costs. Comparing the
saved wide forecast at its chosen start with the saved selective forecast at
its chosen start gives these maximum 3D differences over the same 1,200
withheld epochs:

| Model | Processing profile | Error law | Difference |
|---|---:|---|---:|
| Specified-field globe | 0 | Short | 0.00000012 m |
| Zero-field globe | 0 | Short | 0.00007914 m |
| Zero-field globe | 1 | Persistent | 0.00001346 m |

For each method, the start is the lower training-cost row in the
[verified 24-case table](../esa-observed-model-dispatch-v2/pair-results.csv).
The distance calculation uses the saved `wide-forecast.json` and
`hybrid-forecast.json` for those starts and the same `receiver_errors`
coordinate conversion as the paired audit, then takes the maximum vector
norm. These small differences explain the selection sensitivity; they do not
change the predeclared exact-start gate or make an Earth-model decision.
The first sealed report remains preserved; the second publication corrects
two relative document links. Its 24-case CSV is byte-identical to the first.
The [sealed calculation record](../esa-observed-model-dispatch-runtime/README.md)
retains the frozen inputs, source, charges, fits and forecasts in verified
archive packs; the result audit still passes after compaction.

The subsequent [three-pair observed development run](../esa-observed-hybrid/three-pair-v2/WALL_CAP.md)
reached its frozen four-hour wall cap. All three tasks sealed as budget
failures after 349 native calls. Their wide fit and forecast artifacts are
preserved, but no revised fit or paired comparison completed. This leaves the
faster method unqualified; the unfinished-task recovery route does not apply.

A separate [two-start generated check](START_EQUIVALENCE_RESULT.md) completed
all 12 paired tasks and passed their individual fit checks. Only two of six
full start-equivalence settings passed: all four globe settings failed the
predeclared relative training-cost rule, although the selected forecasts
agreed within 1.75 × 10⁻⁹ m. One setting also changed its preferred start.
The faster method remains unqualified for observed fits. The result and
source-bound evidence are preserved in its [study record](start-equivalence-study/README.md).

The [fresh 180-second generated check](START_EQUIVALENCE_V2_RESULT.md) then
passed all six settings under a separately frozen rule that handles near-zero
costs and checks forecast spread within each method. Its 12 tasks passed;
the largest forecast difference was 3.13 × 10⁻⁹ m. The original failed rule
remains failed. An observed development check is still required before the
faster method can replace the established calculation on aircraft data.

A [saved ESA start audit](OBSERVED_START_V2_RETROSPECTIVE.md) applies the
revised rule to the sealed observed fits with the original `1e-8` relative
cost tolerance and **no absolute floor**. All 8/8 groups pass; the largest
across- or within-method forecast spread is 0.00407 m. This retrospective
result does not change the original 5/8 exact-start failure. The fresh
development comparison and its scope are reported above. Other recordings and
the disc retain the wide method.

[Frozen plan](PLAN.md) · [Sealed long-record evidence](long-study/README.md) ·
[Paired fitting evidence](paired-qualification/README.md) ·
[Long paired fitting evidence](long-fit-study/README.md) ·
[Whole-fit timing](timed-fit-study/README.md) ·
[Model-declared generated fits](dispatched-fit-study/README.md) ·
[Two-start generated result](START_EQUIVALENCE_RESULT.md) ·
[Fresh generated result](START_EQUIVALENCE_V2_RESULT.md) ·
[Saved ESA start audit](OBSERVED_START_V2_RETROSPECTIVE.md) ·
[Earlier failure diagnosis](../mixed-tangent-long-controls/DIAGNOSIS.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
