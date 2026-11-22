# Two bounded solvers pass exact curved controls

The existing trust-region method and centered L-BFGS-B each passed all
eight generated cases. SciPy TRF reported success on all eight and passed
the project's unchanged stopping check on only the two linear cases.

| Case, two starts each | Existing trust region | SciPy TRF | Centered L-BFGS-B |
| --- | ---: | ---: | ---: |
| Linear | 2/2 | 2/2 | 2/2 |
| Curved interior | 2/2 | 0/2 | 2/2 |
| Curved upper bound | 2/2 | 0/2 | 2/2 |
| Curved lower bound | 2/2 | 0/2 | 2/2 |
| Total residual and derivative evaluations | 68 | 372 | 91 |

Even the six nonpassing TRF fits finished within 0.00001 normalized units
of their known optima and within 4.7 × 10⁻⁸ of the exact least-squares cost.
The fresh undamped correction in those cases moved a generated position by
up to 2.5 m. Weak sensitivity of the residual tangent can make that last
correction unstable despite close agreement with the exact solution. This
control shows why a second solver's own success flag cannot resolve the
ESA stopping failures. It gives a candidate for a matched, generated
flight-scale comparison under the original stopping requirements.

The first release ended when the adapter supplied only one field of the
required evaluation charge. All 24 task records were retained and no
evaluation ran. A separate corrected freeze completed 24/24 tasks and
18 passed the declared gate. All 531 evaluations, including those from
the six nonpassing fits, are recorded. No aircraft fit was run and the
reserved groups remained closed.

## Reproduce the saved result

Use the closed `data/curved-bounded-solver-v2` study. The report reads
sealed artifacts and charges without refitting.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.curved_bounded_solver_study report
```

[Frozen cases and gate](CURVED_BOUNDED_SOLVER_PLAN.md) ·
[All 24 results](curved-bounded-solver-result.json)
