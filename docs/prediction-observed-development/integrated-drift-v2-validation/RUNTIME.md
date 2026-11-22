# Independent generated coverage evidence

The [frozen 256-case plan](PLAN.md) tests the fixed changing-gyro-bias law
on new generated histories: 128 with physical vibration and 128 without.
The source/environment manifest, charge journal, recovery qualification,
saved earlier-only forecasts, later scores and task receipts are retained.
No aircraft original, reserved ESA group or Earth-model fit was used.

All **256/256** tasks passed technical checks on one numerical thread; no
recovery task was needed. The [saved-only result](RESULT.md) reproduces every
later score. The predeclared generated gate failed: 0/128 whole-history
exceedances without vibration, 4/128 with vibration, where at most one was
allowed in each stratum. This failure remains part of the study evidence.

The portable evidence bundle and archive receipt are stored beside this
page. Verify a bundle with
`~/venv/bin/python -m lll.studies.portable verify <bundle.zip>`.
