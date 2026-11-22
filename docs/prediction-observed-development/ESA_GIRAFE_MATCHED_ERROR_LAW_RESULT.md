# The force error transfers better under the same recording conditions

After matching the time cells, training on the three earlier windows
with constant atom interrogation predicted the four later windows more
closely than training on all four earlier windows. The later windows
all used that same constant setting.

| Averaging width | Later RMS using all earlier windows | Later RMS using constant-setting windows | Mean error from the constant-setting estimate |
| --- | ---: | ---: | ---: |
| 11 receiver reports | 0.342 mm/s² | 0.165 mm/s² | −0.112 to +0.023 mm/s² |
| 25 receiver reports | 0.264 mm/s² | 0.062 mm/s² | −0.023 to +0.028 mm/s² |

The constant-setting offset was −0.446 to −0.488 mm/s². Both working
covariance laws covered all four later window means at each width.
After matching the bandwidth and the operating condition, the
correlated law had a slightly lower log score at 11 reports, and
the independent law had a slightly lower score at 25.
The more complicated law helped on the earlier comparison of raw
magnitudes. That gain mostly disappears after matching the averaging.
[Raw-magnitude error check](ESA_GIRAFE_FORCE_ERROR_LAW_RESULT.md)

The variable-setting window stays in the evidence. Its disagreement
helped motivate this split, which was tested retrospectively on the
same flight. The result supports treating averaging and operating
condition as inputs to an error model. Independent flights are still
needed to verify absolute error and forecast coverage.

Both width tasks passed. The study reads only saved scores and
interrogation metadata. [Frozen design](ESA_GIRAFE_MATCHED_ERROR_LAW_PLAN.md) ·
[Saved error estimates, scores and charges](esa-girafe-matched-error-law-result.json)

To verify the saved report, restore `data/esa-girafe-matched-error-law-v1`
and run this command.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_girafe_matched_error_law report
```
