# Force prediction uncertainty depends strongly on receiver error over time

We propagated the receiver's reported velocity uncertainties through
the force-magnitude calculation. The result changes substantially
depending on how long errors in the velocity reports persist. The
analysis uses the same eight ESA windows and three receiver products
as the two-instrument force comparison.
[Force comparison](ESA_GIRAFE_FORCE_CONTRAST_RESULT.md)

| Assumed receiver error correlation | Median uncertainty in an individual force prediction | Median uncertainty in the globe–disc prediction difference | Paired uncertainty exceeds predicted shape difference |
| --- | ---: | ---: | ---: |
| Independent samples | 68.693 mm/s² | 0.0060 mm/s² | 0 of 192 |
| 5-second correlation time | 117.646 mm/s² | 0.0111 mm/s² | 24 of 192 |
| 30-second correlation time | 76.705 mm/s² | 0.0124 mm/s² | 36 of 192 |
| 120-second correlation time | 42.396 mm/s² | 0.0118 mm/s² | 32 of 192 |
| Fully shared standardized error | 0.023 mm/s² | 0.00024 mm/s² | 0 of 192 |
| Individual worst-case dependence bound | 436.270 mm/s² | 0.0363 mm/s² | 128 of 192 |

“Uncertainty” here means the propagated standard deviation, summarized
over the eight later time supports. Both shapes share the receiver
errors. Those errors largely cancel in the paired prediction difference.
They can still change the comparison between either predicted force
and the measured force. The uncertainty for at least one of the two
individual predictions exceeds the predicted shape signal in every
setting under the independent and finite-correlation scenarios.

The table uses the receiver's printed velocity covariance, with a
position held fixed at each report. Two difference steps gave agreeing
sensitivities. The worst-case row gives separate linear bounds for
each scalar prediction. It does not describe one error path that
simultaneously attains every bound. The units and receiver covariance
fields are known, while their actual coverage, time correlation and
dependence on position remain unverified. The table supplies no
calibrated uncertainty for an Earth-model decision.
[Receiver covariance audit](GNSS_COVARIANCE_AUDIT.md)

All eight tasks reproduced the earlier force predictions. They
charged 15,458,304 quadrature points and used zero new receiver decodes,
original recording reads or protected flight groups.
[Frozen design](ESA_FORCE_VELOCITY_ERROR_PLAN.md) ·
[Per-window uncertainties and charges](esa-force-velocity-error-result.json)

To verify the saved report, restore `data/esa-force-velocity-error-v1`
and run the following command.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_force_velocity_error report
```
