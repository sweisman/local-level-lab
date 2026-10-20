# Preserve the common packet clock

The complete orientation cover passes correctness but misses its improvement
target. A saved-input calculation identifies a specific loss: independent
packet cutoff remainders can be large even when their sum is nearly linear.
This stage changes the uncertainty construction, not the physical candidates,
instrument timing assumptions or original observations.

## First: qualify a correlated prefix-clock component

Let packet durations be positive binary values `dt_j`, rounded start tags be
`s_j`, and exact physical prefix durations be `P_j = sum(dt_1 ... dt_j)`.
The mathematical clipped-period sum is

`S_i(t) = sum(clip(t-s_j, 0, dt_j), j<=i)`.

With `D_i = max(abs(s_j-P_(j-1)), j<=i)`, monotonicity and exact telescoping give

`clip(t-D_i, 0, P_i) <= S_i(t) <= clip(t+D_i, 0, P_i)`.

Thus its discrepancy from `clip(t,0,P_i)` is at most `D_i`, regardless of the
number of packets. Keep exact rational center/endpoints and the sum of selected
one-sided packet slopes. Bound the reference clamp's remainder at endpoints and
its two knots, then add the clock defect and center discrepancy. Include any
supplied upstream time-map remainder. Do not add independent packet kink bounds
when a common-clock bound is available.

Use a streaming prefix accumulator with work linear in packet count. Reject
nonpositive durations, noncontiguous declared tags and nonfinite inputs. Keep
the original left-sided boundary convention and explicitly distinguish the
mathematical clipped-period map from whole-program floating-point behavior.
Check against independent exact sums at every relevant knot, interval endpoint,
boundary center and generated interior point, including non-dyadic periods,
variable rates and repeated rounded tags.

After component tests pass, freeze a finite generated qualification. Preserve
the old independent-kink method and all completed results. No native predictions,
archive reads or observed fits are needed for this component.

## Then: qualify regrouped native propagation separately

In a new candidate, split coordinate updates into a fixed reference-rate term
times the correlated prefix clock and a residual-rate integral. Retain all
calibration directions. Combine specific force and gravity before multiplying
by their common partial-packet duration, so their known cancellation is not
lost through separate norm bounds. Preserve unknown gains, biases, frame and
time dependencies; no physical model term may be deleted.

The regrouping must reproduce the unchanged native center and its full
27-column linearization within separately stated numerical checks. Independent
constant-motion/constant-force controls, packet boundaries and all candidate/
processing cases precede another generated usefulness experiment. Keep the
complete orientation cover where needed. Save training inequalities, Jacobians,
support certificates and each remainder term for subsequent metadata-only
diagnosis. Freeze finite calls, bound steps, thread allocation and cooperative
time limits before each new execution; never reuse a completed allowance.

This does not establish the physical instrument clock, a whole-program numerical
certificate, actual receiver covariance, long-record usefulness or predictive
adequacy. Failed qualifications block dependent observed fits. Protected ESA
groups remain sealed.

[Completed orientation result](../ilvis0-orientation-cover/INTERPRETATION.md) ·
[Canonical roadmap](../ANALYSIS_ROADMAP.md).
