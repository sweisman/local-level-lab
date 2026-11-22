# Horizontal force changes leave the platform clock unresolved

None of the nine horizontal checks reached the required correlation of
0.70 at the candidate offset of 38,474.267 seconds. The original two
force-magnitude matches still suggest that offset. The horizontal channels
give no confirmation under the tested axis mapping and averaging rule.

| Excerpt | Candidate X | Candidate Y | Horizontal magnitude |
| --- | ---: | ---: | ---: |
| First | 0.045 | 0.321 | −0.400 |
| Second | −0.252 | −0.191 | 0.110 |
| Third | −0.128 | −0.005 | −0.108 |

Values are correlations of first differences at the locked time. The
candidate horizontal channel identities still need verification. The
different responses of the total force magnitude and horizontal channels
motivate an explicit check of the candidate vertical channel on held-out
platform data.

The [plan](ESA_GIRAFE_PLATFORM_COMPONENT_TIMING_PLAN.md) preserves two
earlier software outcomes. An exact floating-point equality check stopped
the first attempt before any signal reads. The second run found implausible
global peaks in two quiet horizontal-magnitude intervals. Computing each
centered window directly removed those peaks. The correlations at the
locked time are the same to the precision shown here.

The [stable receipt](esa-girafe-platform-component-timing-stable-result.json)
has SHA-256 `96ab9287fe13b6c93b4a36fcfdc3bd717b35f62385e4c96f1f6923ce221184a2`.
The [earlier numerical result](esa-girafe-platform-component-timing-result.json)
remains available. The stable run used 13 charged operations and completed
in 2.7 seconds on one numerical thread. It ran entirely from saved
inputs with zero network calls and zero model fits.
The [portable evidence bundle](esa-girafe-platform-component-timing-evidence/bundle.zip)
contains the stable source, charge ledger and all nine comparisons.

```sh
env PYTHONPATH=analysis ~/venv/bin/python -m lll.esa_girafe_platform_component_timing prepare
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py --workers 1 --threads 1 -- ~/venv/bin/python -m lll.studies run data/esa-girafe-platform-component-timing-v3 --reserved-threads 0
env PYTHONPATH=analysis ~/venv/bin/python -m lll.esa_girafe_platform_component_timing report
```
