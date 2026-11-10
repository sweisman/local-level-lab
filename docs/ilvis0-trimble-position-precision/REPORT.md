# Primary-receiver precision inventory

The 53 previously selected recording files were checked for position-precision
reports in their preserved primary GNSS receiver streams. This inventory did
not fit an Earth model or read IMU measurements. It does not change which of
the 53 flight stretches entered the earlier model comparison.

**Result:** all 53 receiver-stream tasks finished. Fifty-two passed the
predeclared packet and same-receiver position checks. One did not, so the
whole-cohort receiver-precision gate did not pass. The failed recording remains
available for other analyses under their own criteria.

| Checked output from the 52 passing files | Result |
|---|---:|
| Checksummed receiver packets | 725,499 |
| Enhanced-position reports | 145,446 |
| Binary positions matched to the same receiver's GGA positions | 29,085 |
| Position reports per file, minimum / median / maximum | 2,232 / 2,817 / 3,459 |
| Median of each file's reported one-sigma north / east / up precision | 0.657 / 0.560 / 1.169 m |
| Largest binary-versus-GGA difference, north / east / up | 0.000009 / 0.000007 / 0.001062 m |

These precision numbers are **the receiver's own estimates**, not independently
measured position errors. The binary/GGA agreement confirms that two outputs
from the same receiver were decoded consistently. It does not establish their
accuracy, error distribution or correlation through time. Twenty-four passing
streams start or end inside a receiver packet; the exact boundary fragments are
recorded, and all accepted interior packets pass framing and checksum checks.

The remaining file,
`ILVIS0_applanix_57315_610_loaner_20Oct15LVIS.013`, has unsupported bytes
inside its receiver stream at byte 185,840. Its outer Applanix recording was
not rejected by this finding. The strict receiver decoder did not skip those
bytes, so this file has no accepted precision report in this inventory. A
later, separately qualified decoder may identify the additional message type.

The first execution freeze stopped before starting a task because its adapter
could not load as a standalone worker module. No task or fit was charged. A
tested import correction was frozen under a new study ID; it produced the
53 saved task outcomes above. The original startup failure remains preserved.

## What this enables

The 52 accepted streams provide observed, time-tagged receiver precision
estimates for a later receiver-error study. The next gate is to test whether
those estimates describe actual held-out position errors and their temporal
dependence. They cannot yet set a calibrated prediction threshold or turn the
earlier 53 model preferences into significance claims.

The [selection and checks](PLAN.md) were fixed before the inventory. The
archived study contains the source and input hashes, frozen code, all task
results, the failed result and the per-epoch position tables. Trimble's
[enhanced-position specification](https://receiverhelp.trimble.com/oem-gnss/icd-subtype7-enhanced-position-record-29.html)
defines the reported precision fields.
