# Four southern flight groups reserved for pilot development

The metadata rule reserved four distinct groups. It retained the east and
south IMU8 course sectors and spans about six degrees of latitude among
the eligible IMU21 stretches. All four recordings are southern.

| Recorder | Mean latitude | Mean course | Duration | Median speed | Used by the two-recording preflight |
|---|---:|---:|---:|---:|---|
| IMU8 | 62.65°S | 119.54° | 11.13 min | 858 km/h | Yes |
| IMU8 | 63.07°S | 203.69° | 9.75 min | 849 km/h | No |
| IMU21 | 56.66°S | 177.78° | 7.37 min | 822 km/h | Yes |
| IMU21 | 62.59°S | 176.97° | 8.95 min | 798 km/h | No |

These are retrospective development records. The [receipt](matched-pilot-candidates-receipt.json)
binds their original time windows, source hashes, group IDs and geometry.
The [selection rule](MATCHED_PILOT_CANDIDATES_PLAN.md) uses metadata only.
It leaves the earlier engineering eligibility and the 53-stretch findings
unchanged. A separate fitting freeze and qualification are required before
any of these records enter the pilot.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py --workers 1 --threads 1 -- ~/venv/bin/python -m lll.ilvis0_matched_pilot_candidates
```
