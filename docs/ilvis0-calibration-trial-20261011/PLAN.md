# Z-axis calibration sensitivity and prediction checks

**Prepared development plan; no new observed fits have started.** The completed
clock comparison preserved globe over flat and then rotating over still globe.
The next question is whether that preference requires the Z-axis gain or offset
correction to sit at its permitted limit.

An IMU (inertial measurement unit) measures turning and acceleration. Gain is a
multiplicative measurement correction; offset is a constant added rate. Neither
is the same as changing drift. This comparison will isolate the two corrections
without adding a more flexible drift model or widening any limits.

## Fixed target and comparisons

Reuse the entire preselected 438-second control
`570b37d23af5e245dd461051`, from
`ILVIS0_applanix_57300_610_LVIS_38614965.013`, IMU type 21,
median ground speed 878.06 km/h, minimum 859.55 km/h. Selection is unchanged.

Use packet-header integration intervals, the original frozen optimizer and
initialization, existing receiver coordinates/covariance, and the same gravity,
mount, timing and remaining calibration limits. Reuse the completed six-fit
header-clock comparison as the reference, without refitting it.

| Alternative | Z gyro gain | Z gyro offset | Other parameters |
|---|---|---|---|
| Reference, already complete | Free within ±2% | Free within ±1°/hour | Existing bounds |
| Gain ablation | Fixed at zero | Free within ±1°/hour | Identical to reference |
| Offset ablation | Free within ±2% | Fixed at zero | Identical to reference |

For each alternative fit rotating globe, still globe and stationary disc under
both existing processing cases: no upstream Earth-rate removal, and a fitted
common removal fraction. This gives **12 new starts**, one per identity, with
**at most 200 evaluations per start and no retry reserve**. The fixed parameter
is removed from the active fit; it is not given an artificial tiny bound.

Zero is a diagnostic calibration anchor, not a measured factory calibration or
a claim that these instruments have zero error. These ablations ask whether each
correction is necessary to achieve the reported model preference. They do not
replace physically supported performance limits or establish an absolute-fit
criterion. Tightening limits to undocumented precision would answer a less
defensible question; widening them would add nuisance freedom before the existing
trade-off is understood.

## Initialization and checks

Use the same model-specific GPS/raw-increment initialization as the reference,
computed without Group-1 fitted rates or attitude. Do not warm-start from the
preferred completed model or search several starts until a result succeeds.
Original normalized initialization sets calibration gains/offsets to zero
except the established accelerometer-gain seed. Fixing one Z parameter to zero
therefore preserves the same physical initial values for the remaining parameters.

Before fitting, freeze source, input hashes, exact numerical environment,
configuration and selection in a new study. Verify existing evidence receipts.
Use one detached worker and two numerical threads, an exclusive lock, a durable
charged-start journal and atomic hashed results. Preserve failed and interrupted
starts without retry. Packaging and documentation must never start fitting.

Record objective, physical horizontal/vertical errors, fresh projected gradient,
solver success, parameter estimates and signed boundaries, singular values and
per-epoch covariance-scaled residuals. Count diagnostic predictions inside the
200-evaluation allowance. Keep unchanged reference costs alongside new results.
A restricted fit has fewer permitted parameter values: a lower cost than the
reference can indicate local optimization differences, not proof that fixing a
parameter improves the underlying physical model.

Report shape before rotation. Require all three fits to converge under both
processing cases before interpreting a complete three-model comparison. An
unfinished flat fit is not evidence that flat cannot fit. Rotation is revealed
only after both shape comparisons favor globe. Keep the production gate and
statistical significance claims unchanged.

## Budget

The six completed clock fits used 963 evaluations. Their median elapsed time per
evaluation was 3.17 seconds; the slowest fit averaged 3.70 seconds per evaluation.
Using all 2,400 new evaluations estimates **127–148 minutes**, plus extraction,
verification and publication. Allow roughly **2–2.5 hours**, with no wall-clock
guarantee. Explicit approval of this allowance is required before launch; the
unused allowances of completed studies remain unavailable.

## Follow-on: genuine prediction on unused observations

After this calibration comparison is reviewed, prepare a separate prediction
trial using the same preselected stretch: fit the first two thirds of the receiver
epochs and predict the final third without fitting that portion. Freeze the
chronological split before any new residual calculation. This provides a future
time check, not an independent flight replication.

Initialization, tuning and parameter estimation must use training receiver
observations only; using the whole track to estimate the starting velocity or
mount would leak the prediction segment into the fit. Raw IMU increments over
the prediction segment are predictor inputs. Keep calibration fixed during
prediction, propagate continuously, and do not restart from withheld GPS fixes.
Use the marginal training covariance during fitting. Evaluate prediction errors
and, if using correlated receiver-error conditioning, explicitly apply the
training-to-prediction cross-covariance instead of pretending those epochs are
independent. Fit and evaluate all three candidates equally.

Archive full-stretch, training and prediction results separately. Declare timing,
calibration alternatives, numerical allowances and receiver uncertainty before
this further trial. No held-out fits or archive expansion are authorized by this
plan. Replication should later use stretches selected by independent geometry
and provenance criteria, with overlapping records grouped as dependent evidence.
