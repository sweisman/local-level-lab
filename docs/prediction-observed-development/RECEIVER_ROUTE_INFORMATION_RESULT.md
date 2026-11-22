# The three ESA windows offer different geometry contrasts

The training-period receiver reports were decoded for all three
preselected ESA windows. The geometry check used positions and
reported velocity throughout. It compared predicted angular rates
under each candidate while allowing each one its own constant gyro
offset. This helps distinguish windows that test shape from windows
that mostly test the specified background field.

| Training window | Course span | Specified-field globe vs disc | Specified-field vs zero-field globe | Zero-field globe vs disc |
|---|---:|---:|---:|---:|
| 187-042470-044870 | 5.1° | 0.187 | 0.129 | 0.138 |
| 187-049554-051954 | 4.6° | 0.421 | 0.149 | 0.410 |
| 187-058525-060925 | 34.3° | 0.666 | 0.682 | 0.152 |

The last three columns are the smallest residual vector RMS differences
across the declared attitude grid, in degrees per hour. The table
allows an unrestricted constant offset. Allowing 10°/h per candidate
per axis gave the same results. The full report also includes allowances
of 0, 1, 3 and 20°/h. These are sensitivity settings for this calculation.

The larger course change in the last window strengthens the field
contrast most. The middle window has the largest shape contrast when
both candidates have zero field. A single course-change cutoff would
miss that difference. All three windows remain selected.

The calculation assumes that aircraft angular motion can be removed
independently and uses the conventional receiver coordinate chart.
An independent body-motion record and an aircraft error law are still
needed to interpret these distances as power. The noise figures in the
full report assume independent per-axis white error and serve only as
fixed-path reference values. The source hash and all 2,400 training
queries verified. The original receiver file was hashed in one pass.
Later positions were excluded from decoding. All reserved groups
remain closed.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.receiver_route_information replay
```

[Fixed design](RECEIVER_ROUTE_INFORMATION_PLAN.md) ·
[Frozen source and settings](receiver-route-information-freeze.json) ·
[All pair and offset results](receiver-route-information-result.json)
