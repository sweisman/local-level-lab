# Which archived stretches could enter the matched pilot?

**21 of 53 stretches** meet the saved file, instrument configuration and
receiver checks used in this inventory. They represent **18 conservative
flight groups**. None is northern. That limits the variety of routes a pilot
can test under these checks.

| Instrument | Original stretches | Meet all three checks | Flight groups | Mean latitude range | Course sectors |
|---|---:|---:|---:|---|---|
| IMU8 | 2 | 2 | 2 | 63.1°S to 62.7°S | 1 east, 1 south |
| IMU21 | 51 | 19 | 16 | 62.6°S to 56.7°S | 19 south |

Course sectors are 90° wide, centered on the four cardinal directions. The
two available IMU8 stretches share a decoder configuration. The group counts
come from the conservative provenance ledger.

The audit joined the source hash and original window times to the flight
group and GPS inventories. It checked the configuration on two dates and
the individual file's physical conversion. For IMU8 it used the earlier
task and filename binding and required full-navigation decoder context.
One IMU21 file satisfies both conversion checks but has no strictly decoded
receiver stream. All four northern records in the original selection fail
at least one of the conversion checks.

The [metadata receipt](matched-pilot-metadata.json) includes every stretch,
each check and hashes of the six input ledgers. Recreate it from the
repository root with the saved inputs and the
[audit program](../../analysis/lll/ilvis0_matched_pilot_audit.py):

```sh
env PYTHONPATH=analysis ~/venv/bin/python -m lll.ilvis0_matched_pilot_audit
```

No fit scores, gyro residuals or reserved ESA records were used. The GPS
check establishes a single uninterrupted block under the 1.5-second gap
rule. It does not establish position accuracy. This inventory leaves the
original 53-stretch study intact and selects no pilot recordings. A southern
pilot can use the available coverage after the remaining gates pass. A
northern comparison requires separate decoder qualification or new input.

The [northern clock check](NORTHERN_IMU21_CLOCK_RESULT.md) found that all
four northern files share one configuration. Nominal timing cleared two
engineering failures, while the original two-date failure remained. The
21-stretch eligibility result stays unchanged.
