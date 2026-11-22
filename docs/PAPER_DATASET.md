# Evidence dataset

The [development snapshot, version 2](paper-development-dataset-v2/README.md) brings the
selected observations, numerical results and validation status together without
changing the completed analysis.

A later [twenty-group forecast extension](prediction-group-transfer/REMAINING_GROUPS_PREDICTION_RESULT.md)
is published separately from this frozen snapshot. It completed 80 planned
fits: 30 passed numerical checks and 50 did not. Nine groups have scored later
forecasts within a fixed earlier development reference and pass a separate
physical screen; five pass both time cuts, four pass the later cut only, and
eleven lack a usable later-cut score. This retrospective
single-model result neither changes the snapshot nor calibrates a decision.

| Included | Coverage |
|---|---:|
| Selected stretches and source/track metadata | 53 |
| Latest primary model/processing-case comparisons | 318 |
| Preserved numerical-history records | 791 |
| Conservative development split groups | 27 |
| Retained-file eligibility outcomes | 232 |
| Raw-gyro geographic baseline comparisons | 159 |
| Catalog entries with reconciled storage/eligibility | 326 |
| Numerical records linked to publication and operation environments | 791 |

The history includes 244 records not marked converged. They remain visible
alongside later successful work; some entries are diagnostics rather than
optimizer starts. The latest complete numerical disposition remains **53 globe,
zero flat and zero unresolved**.

The [frozen grouping ledger and its current verification method](PROVENANCE_VERIFICATION.md)
keep overlapping recordings together without treating its 27 conservative
groups as 27 proven independent flights.

The [ESA forecast index](analysis-provenance/ESA_GROUP_EVIDENCE.md) is a separate
development record. It shows which studies share GPS positions within the
one opened flight group and lists the groups reserved for confirmation.
The [ground reference evidence](prediction-observed-development/ESA_GROUND_REFERENCE_EVIDENCE.md)
adds fourteen verified range, timing and geometry checks for that same flight. It
contributes no additional flight group.

## Verify the public evidence

Run these checks from the repository root. They use published evidence
files and run no fits. The first verifies both frozen dataset versions.
The others check the current NASA group evidence and the ESA forecast
group and observation counts.

```sh
~/venv/bin/python docs/paper-development-dataset-v2/build_dataset.py --check-public
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py --workers 1 --threads 1 --reserved-threads 0 -- ~/venv/bin/python -m lll.ilvis0_group_evidence_current check
env PYTHONPATH=analysis ~/venv/bin/python -m lll.esa_group_evidence check
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py --threads 1 -- ~/venv/bin/python -m lll.esa_ground_reference_evidence check --version 3
```

There are zero independently scored confirmation groups in these tables.
The seven reserved ESA groups should remain closed until the selection,
prediction and accuracy rules, and observational error model are fixed.
The permitted [receiver-only screen](external-imu-data/ESA_CONFIRMATION_RECEIVER_INVENTORY_RESULT.md)
found candidate windows in all seven groups. Those windows are provisional
until the confirmation protocol is frozen. A [separate timing audit](external-imu-data/ESA_CONFIRMATION_TIMING_RESULT.md)
verifies one 20-minute slice per group.

## How the 53 stretches cluster

The frozen `stretches.csv` contains **11 groups with one stretch, six with two,
and ten with three**. Every stretch in every group has the recorded numerical
preference `globe` and `specified_background_preferred=True`. This is a
dependence-aware description of the completed comparisons, not 27 independent
confirmations: groups can share physical hardware or systematic errors across
dates, and their original model comparisons have no calibrated detection rule.
The group key is `conservative_split_group`; the original 53 rows and the
[grouping ledger](analysis-provenance/README.md) provide the reproducible count.

Holding the background field at zero for both shapes produces a different
result. All stretches favor globe in 17 groups, all favor disc in five,
and the other five contain both outcomes. These are matched in-sample
cost comparisons. [Zero-field results by group](analysis-provenance/NASA_ZERO_FIELD_BY_GROUP.md)

One IMU21 recording that favored the disc in its original zero-field fit
now has a complete four-candidate forecast check. On its held-out GPS
reports the globe has lower 3D error at both matched fields. At zero
field the disc has lower height error. The orderings hold across the
measured GPS spread. [Shared-reference forecast check](ilvis0-measurement-contribution/MATCHED_IMU21_RECEIVER_HULL_RESULT.md)

An **IMU (inertial measurement unit)** records turning and specific force. Its
gyro increments supply the observed turning; receiver positions supply the
route context. The snapshot keeps those roles, source fingerprints and unknown
instrument identities explicit. Conservative groups do not establish a count
of independent flights.

This version is for development and audit. Qualified withheld-prediction
adequacy, observational error assessment, independent confirmation and calibrated
decisions remain open. The acquisition-flow and operation/environment indices
are now complete: 58 initial no-level rejections, 35 later rejections and one
verified duplicate removal reconcile the 326 entries with 232 retained files.
Sixteen history origins resolve to 23 execution manifests and two recorded
numerical environments. Later publication reviews retain their own environment
separately from the operations they describe. The snapshot does not label numerical preferences as
calibrated detections or claim to be the final paper dataset.

## Prediction evidence kept separately

The [current evidence table](analysis-provenance/NASA_GROUP_EVIDENCE.md) links
the fitted and prediction results by recording group. It identifies where the
same group contributes to more than one study and keeps their outcomes separate.

The [earlier 27-group evidence table](analysis-provenance/nasa-group-evidence.csv)
links all 53 baseline stretches to the later prediction records. Each group
has one row, with its constituent stretches and the representative used
for the later check.

| Retrospective check | Groups | Saved prediction outcome |
| --- | ---: | --- |
| Three-model comparison | 3 | One group completed all four settings and one completed one setting. The specified-field globe passed the physical screen in all five completed settings. The third group had no complete comparison. |
| Single-model forecast | 24 | Twelve later forecasts met both the fixed error reference and the physical screen. Twelve lacked a passing later fit. |

The checks answer different questions. The single-model forecasts test
how well the specified-field globe predicts unseen positions. The
three-model pilot compares candidates on the same positions. All groups
come from the original development archive, and the table supplies no
calibrated decision or independent-flight count. It leaves the frozen
development snapshot unchanged.

The separate [four-flight matched audit](ilvis0-measurement-contribution/MATCHED_FOUR_GROUP_AUDIT_RESULT.md)
uses four preselected conservative groups and verifies 15 of 16 forecasts.
It adds same-field comparisons and a fixed accuracy screen per GPS track.
These checks use the archived NASA development cohort and do not increase
the number of independent confirmation flights.

Run this command from the repository root to verify the table against
the frozen baseline and the three saved prediction reports.

```sh
PYTHONPATH=analysis ~/venv/bin/python -m lll.ilvis0_group_evidence check
```

The later [three-recording prediction pilot](ilvis0-retrospective-prediction-pilot-v2/INTERPRETATION.md)
is a separate archived result, not an amendment to this frozen snapshot. It
completes one recording-level comparison across all required settings and
preserves numerical or accuracy failures on the other two. Its predictions,
charges, source freezes and verified report remain reproducible alongside
the original dataset. Calibrated uncertainty and independent confirmation
remain outstanding.

The later [four-group NASA transfer check](prediction-group-transfer/RESULT.md)
also remains separate from the 53-stretch snapshot. All 16 planned fits are
sealed; six pass numerical checks. Three groups have scorable second-cut
forecasts that meet both the fixed descriptive error reference and physical
screen. One group abstains. This is retrospective development evidence, not
calibrated prediction coverage or independent confirmation.

The [first ESA development pilot](esa-development-pilot/README.md) is also
separate. It returns 24 fits, with 15 numerical passes and one complete
three-model comparison. Globe geometry has lower later error in that comparison,
but its preferred forecast fails the physical-accuracy limits. This is not an
independent confirmation of the NASA result.

The [48 known-correction gravity controls](esa-gravity-controls/README.md) pass;
all 24 [long training/forecast cases](esa-height-training-controls/README.md)
also qualify. These use generated measurements and add software evidence, not
observed flight replications. They do not alter the frozen version-2 counts.
The [observed gravity revision](esa-observed-height-pilot/README.md) completes
one adequate three-model setting on the same development interval, with later
specified-field horizontal/height RMS of 6.80/13.71 m. Eight of 24 fits pass
numerical checks; all failures and repeated starts are retained separately.
This adds development evidence without changing the original dataset counts.
All seven ESA confirmation groups remain protected.

The [wider-precision motion controls](esa-wide-tangent-controls/README.md) also
pass all 48 known-answer cases. The [full training/forecast qualification](esa-wide-training-controls/README.md)
also passes all 24 cases, with every saved result and charge verified. A
[matched observed precision revision](esa-observed-wide-pilot/INTERPRETATION.md)
now supplies 22 qualified forecasts and three complete, physically adequate
comparisons favoring globe plus the specified field. Two disc starts stop at
the runtime ceiling. This verified development evidence is published separately
from the frozen paper dataset; no original fit is reclassified and none of its
counts changes. Broader prediction and uncertainty assessment remain open.

The [ESA direction prediction check](prediction-observed-development/ESA_DIRECTION_HOLDOUT_SCORE_RESULT.md)
compares sealed predictions with angular changes measured in eight further
windows of the same recording. It adds evidence on when field assumptions
change the shape comparison. Independent-flight accuracy and calibrated
decisions remain open.

The [tables and checker](paper-development-dataset-v2/README.md) use frozen input
copies and recorded SHA-256 hashes. Later project changes cannot silently alter
this version. Assembly and checking read saved metadata, not original recordings,
and run no model predictions or fits. `--check-public` works in a repository
checkout without the runtime data directories. The checker now verifies frozen
inputs from the content-addressed evidence archive when their expanded copies
have been compacted; the public check passed on both published snapshots.
Protected ESA outcomes are not part of the dataset.
[Version 1](paper-development-dataset-v1/README.md) remains sealed.

## Later uncertainty work

The [flight-group score](PREDICTION_GROUP_DECISION.md) now connects saved
matched forecasts to the two-stage decision software. The twelve generated
controls are too few to exclude a candidate at a 5% allowance. This leaves
the frozen paper snapshot and its evidence counts unchanged.

The separate [generated-data calibration](prediction-calibration-host-20261030/INTERPRETATION.md)
completed all 7,176 prescribed fits and set a fixed prediction-error limit for
its simulated population. A reboot interrupted the original independent
validation after 3,750 saved fits. A [task-level continuation](VALIDATION_CONTINUATION.md)
completed the other 594 fits under a separate, recorded recovery allowance.
The [independently replayed combined report](prediction-validation-continuation/README.md)
passed the declared generated-data coverage rule across all 181 preselected
simulated cases. These calculations are not part of
the frozen development snapshot and do not establish confidence in the 53
observed-aircraft preferences.

The separate [ESA fixed-fit horizon check](prediction-observed-development/TRAINING_SPLIT_EXTENSION_RESULT.md)
holds one 600-report calibration fixed through 400 later reports. Its nominal
height coverage falls to 0/100 in the last 100-report bin; an older 800-report
fit also covers 0/100 on those same receiver positions. Both calculations
remain development diagnosis. The observed prediction-error law is not yet
adequate for a final paper decision or the seven reserved flight groups.
The [training-only innovation check](prediction-observed-development/TRAINING_INNOVATION_RESULT.md)
also finds persistent fitted height residuals under both supplied error laws;
it is diagnostic and does not change the frozen snapshot.
The [saved local-fit audit](prediction-observed-development/TRAINING_LINEAR_REFERENCE.md)
checks all 26 fitted calibration directions against the same training residuals.
The small fitted error cannot be attributed simply to those 26 directions
under the declared linear covariance reference. This remains a development
diagnostic, not a calibrated aircraft decision.
The [known-answer two-recording control](prediction-observed-development/FIT_ADJUSTED_CONTROL_RESULT.md)
finds training costs near 1,800 in four numerically passing generated fits,
compared with 7.15 on the ESA development recording. All four generated fits
reach calibration bounds. This strengthens the error-model question but is
too small to calibrate a probability or qualify observed-aircraft uncertainty.
The [saved calibration-boundary audit](prediction-observed-development/FIT_ADJUSTED_BOUNDARY_REPORT.md)
finds only a small local cost reduction from releasing those limits. It does
not rule out a different nonlinear solution or explain the later height miss.
The [saved residual comparison](prediction-observed-development/FIT_ADJUSTED_RESIDUAL_REPORT.md)
shows generated fitted errors near unit whitened RMS on each axis while the
ESA development fit has RMS 0.063 and persistent height correlation. The
observation-model difference remains unexplained.
The [saved IMU-rate comparison](prediction-observed-development/GENERATED_RATE_COMPARISON.md)
shows much larger short-span changes in recorded ESA rates than in generated
inputs; aircraft motion and vibration are not separated. Neither diagnostic
qualifies the observed prediction-error law.
An [independent known-motion control](prediction-observed-development/MOTION_ERROR_CONTROL.md)
shows the specific risk: in one matched generated example, treating a
0.02-second gyro contrast as white sensor noise overstates the known white
component by 35 times, while longer contrasts can cancel the physical
vibration. This tests the diagnostic, not the ESA instrument.
The [generated known-answer forecast check](prediction-observed-development/FIT_ADJUSTED_FORECAST_REPORT.md)
also finds 50–84 m future horizontal RMS after numerically passing training
fits. This blocks using those two controls as evidence of prediction coverage.
It leaves the frozen 53-stretch snapshot unchanged.
The [known-calibration follow-up](prediction-observed-development/ORACLE_NOISY_REPORT.md)
also drifts on both generated noisy streams, despite using the generator's
true corrections. Its two forecasts passed the finite software run; neither
qualifies physical prediction accuracy or observed-aircraft uncertainty.
A [long clean counterpart](prediction-observed-development/ORACLE_CLEAN_REPORT.md)
stays within 0.035 m horizontal and 0.322 m vertical future RMS. This
localizes the generated forecast failure to injected IMU errors or their
interaction with propagation. [Matched channel forecasts](prediction-observed-development/ORACLE_CHANNEL_REPORT.md)
show gyro errors dominate horizontal drift on the two fixed draws. A
[four-task component comparison](prediction-observed-development/ORACLE_GYRO_COMPONENT_REPORT.md)
then separates white gyro noise from changing gyro bias; both can cause large
drift, and their effects partly cancel in one draw. This does not identify the
recorded IMU's error law or change the frozen snapshot.
The [matched error-scale calculation](prediction-observed-development/ORACLE_MATCHED_SCALE_REPORT.md)
finds a 350.7 m horizontal RMS scale under either declared synthetic law,
while the two saved outcomes are 59.7 m and 637.1 m. Two generated draws do
not establish uncertainty coverage for an aircraft recording.
The [generated horizon table](prediction-observed-development/ORACLE_HORIZON_REPORT.md)
and [saved ESA development scores](prediction-observed-development/RECORDED_HORIZON_DIAGNOSTIC.md)
show lower errors on shorter withheld intervals. The ESA prefixes were
inspected after their long-horizon result; they are design evidence, not a
new validation or a change to the frozen 53-stretch snapshot.
The [short-block development layout](esa-short-block-development/README.md)
selects three additional windows from existing receiver-only metadata. It
does not add a fitted result to this dataset or open reserved ESA groups.
Its [chronology note](esa-short-block-development/INTERPRETATION.md) makes
clear that the shorter prediction duration was selected after first-window
results were known, so these windows remain exploratory development.
The [saved ESA cross-channel check](prediction-observed-development/RECORDED_CHANNEL_DEPENDENCE.md)
finds strong short-time correlation between one gyroscope and accelerometer
axis. It uses only the established training interval; it does not assign the
shared variation to aircraft motion or instrument error.
The [analytic sampled-data control](prediction-observed-development/ERROR_ATTRIBUTION_CONTROL.md)
shows that real vibration and correlated sensor error can produce identical
IMU and one-second receiver reports. It is a software limitation check,
separate from the observed flight and the frozen snapshot.

[Current findings](CURRENT_STATUS.md) · [Raw gyro companion](ilvis0-gyro-companion-v2/INTERPRETATION.md) ·
[Roadmap](ANALYSIS_ROADMAP.md).
