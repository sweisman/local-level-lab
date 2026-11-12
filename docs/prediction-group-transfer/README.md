# Four additional development flight groups selected

The next retrospective prediction check has four recordings fixed **before
new fitting**, using only saved route, instrument and provenance metadata.
They add one southern IMU8 recording, one northern IMU21 recording and two
southern IMU21 recordings from different years. None shares a conservative
flight group with the three-recording prediction pilot or with another row
here.

| Recording | IMU type | Latitude | Duration | Conservative group |
|---|---:|---:|---:|---|
| `b365bdf3…` | 8 | 63.1° S | 9.75 min | `ilvis0-69e08949…` |
| `b4ab6e12…` | 21 | 75.3° N | 6.88 min | `ilvis0-9290e1fb…` |
| `c16df82d…` | 21 | 63.7° S | 10.80 min | `ilvis0-c06ebf50…` |
| `2f7e37c4…` | 21 | 60.9° S | 9.42 min | `ilvis0-92eedf51…` |

The selection used no gyro outcome or model cost. No protected ESA recording
was read. The subsequent [four-group result](RESULT.md) is reported separately.
Same-date grouping protects against obvious overlap but does not prove
separate aircraft or independent instruments. The NASA archive has already
informed development, so these recordings can test transfer within that
archive but cannot serve as untouched confirmation.

The [fixed rule](PLAN.md), [complete selection](selection.csv),
[selection hash receipt](selection-receipt.json) and
[exact receiver split receipt](split-receipt.json) preserve the choice and
the training/scoring boundary. Rebuild the selection with
`/home/sweisman/venv/bin/python -c 'from lll.ilvis0_group_transfer_selection import publish_selection; publish_selection(".")'`
from the repository root. The split receipt is immutable once published; its
producer is `lll.ilvis0_group_transfer_selection.publish_layouts`.
The [finite transfer plan](OBSERVED_PLAN.md) now fixes a descriptive error
reference from the original three recordings' first-cut forecasts. Its
source-bound builder passes three focused checks. The source/environment
qualification passed 24 tests, and the [recovery route](RECOVERY.md) passed
five interruption checks. The 16-start study closed with all outcomes sealed
after 611 native calls. Six fits passed the numerical check. The qualified
saved-only report finds three of four groups scorable at the second cut; all
three meet the fixed descriptive error reference and the separate physical
prediction screen. One group abstains because its second-cut fits did not
pass. This does not calibrate prediction coverage or a model decision.

The [fit audit](fit-audit.csv) preserves all ten nonpassing fits. In the one
unscored group, neither start passed at either cut; close training costs from
the two starts do not replace the required stopping check. Nine nonpassing
fits stopped with no positive predicted decrease, and one exhausted its trust
region. These are numerical abstentions, not evidence favoring either geometry.
The [saved stopping-probe replay](STOPPING_DIAGNOSTIC.md) identifies the
specific failed checks without changing these outcomes.
Among the three scored second-cut forecasts, height RMS in the final quarter
is 8.4–10.3 times the first-quarter RMS. This is observed forecast-error
growth, not a calibrated time-dependent error law.
