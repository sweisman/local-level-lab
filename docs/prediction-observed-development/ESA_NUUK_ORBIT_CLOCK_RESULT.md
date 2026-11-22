# Final satellite orbit and clock check

Replacing the broadcast satellite orbits and clocks with the final IGS products
did not account for the range error that would hide the test aircraft displacement.
The displacement spans the saved model-score gap and returns to zero at the four
permanent Nuuk ground observations. The check used the same 240 half-second
pairs and 2,496 signed range values on the open ESA development flight.

| Satellite update | RMS change | Signed fraction of the required pattern | RMS still needed |
| --- | ---: | ---: | ---: |
| Orbit | 0.049 mm | +0.007% | 3.008 mm |
| Clock | 0.585 mm | −0.089% | 3.067 mm |
| Orbit and clock | 0.574 mm | −0.082% | 3.065 mm |

On the common satellite set, adding the test displacement raises the range
residual from 3.856 to 4.891 mm RMS with the broadcast products and from 3.885 to
4.915 mm with the final products. Both calculations use the same recorded
signal transmit times and apply the product changes on the saved path. The
result isolates this archived update. Shared satellite errors, antenna effects
and absolute aircraft position error remain unbounded by this test. An
independent high-rate ground reference remains the next direct check.

The [plan](ESA_NUUK_ORBIT_CLOCK_PLAN.md) froze one replay, with zero new fits and
zero reserved-flight reads. Eight software tests passed and the replay closed
with 241 of 241 charged checks. The signed rows and completion receipt are in the
[result](esa-nuuk-orbit-clock-result.json), whose SHA-256 is
`40b586d4e848468e41482df75353efc8d93256cf0593e8eca8a3635d7cd7261d`.
To check the reported values from the signed rows alone, run from the repository root

```sh
PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py --threads 1 \
  ~/venv/bin/python -c 'import json; from pathlib import Path; from lll.esa_nuuk_orbit_clock import RESULT, summarize; result=json.loads(Path(RESULT).read_bytes()); assert summarize(result["rows"]) == result["product_summary"]; print("Verified the carrier product summary")'
```
