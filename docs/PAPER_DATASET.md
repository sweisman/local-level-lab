# Evidence dataset

The [development snapshot, version 2](paper-development-dataset-v2/README.md) brings the
selected observations, numerical results and validation status together without
changing the completed analysis.

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

The later [three-recording prediction pilot](ilvis0-retrospective-prediction-pilot-v2/INTERPRETATION.md)
is a separate archived result, not an amendment to this frozen snapshot. It
completes one recording-level comparison across all required settings and
preserves numerical or accuracy failures on the other two. Its predictions,
charges, source freezes and verified report remain reproducible alongside
the original dataset. Calibrated uncertainty and independent confirmation
remain outstanding.

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

The [tables and checker](paper-development-dataset-v2/README.md) use frozen input
copies and recorded SHA-256 hashes. Later project changes cannot silently alter
this version. Assembly and checking read saved metadata, not original recordings,
and run no model predictions or fits. `--check-public` works in a repository
checkout without the runtime data directories. Protected ESA outcomes are not
part of the dataset. [Version 1](paper-development-dataset-v1/README.md) remains sealed.

[Current findings](CURRENT_STATUS.md) · [Raw gyro companion](ilvis0-gyro-companion-v2/INTERPRETATION.md) ·
[Roadmap](ANALYSIS_ROADMAP.md).
