# How much can an ideal antenna's tilt change the saved score?

For the two-minute ESA development comparison, each degree of maximum
tilt can change the full range score by **at most 1.03% of the original
model-score gap** in the ideal antenna model, provided all used satellite
rays stay above the antenna plane throughout the modeled tilt. A rotation
around the antenna's own normal changes the phase equally for all
satellites and cancels when the score removes their mean.

| Part of the score | Maximum shift per degree of tilt | Share of the original gap per degree |
| --- | ---: | ---: |
| Full | 0.0004613 | 1.026% |
| Covered by the Nuuk comparison | 0.0004553 | 1.013% |
| Outside the Nuuk comparison | 0.0000211 | 0.047% |

The covered part would need at least 48° of maximum tilt to consume the
remaining allowance from the published example under these assumptions.
The calculation establishes a lower limit on the tilt needed even if every
effect aligns with the score. It does not establish that such a tilt keeps
the satellites above the antenna plane. The actual aircraft tilt,
transmitter wind-up and phase changes for the upright antenna remain
outside this bound. A separate replay found that the [upright phase
correction](ESA_NKAR_PHASE_WINDUP_RESULT.md) changed the score by a tiny
fraction of the gap. The installed antenna's calibration and reflections
remain open. [Error budget](ESA_NKAR_ERROR_BUDGET_RESULT.md) ·
[Aircraft antenna records](ESA_AIRCRAFT_ANTENNA_INVENTORY.md)

In the crossed-dipole model, let $s$ be the unit direction toward a
satellite and $n$ the antenna normal. A small rotation vector changes
phase according to its dot product with $-(n+s)/(1+n\cdot s)$. The
component along $n$ is $-1$ for every satellite. The perpendicular
component has length $\sqrt{(1-n\cdot s)/(1+n\cdot s)}$, at most one
in the upper hemisphere. Integrating along the tilt gives the stated
bound. The two-band GPS range combination multiplies phase in cycles by
$c/(f_1+f_2)$. [Original phase model](https://ntrs.nasa.gov/citations/19920060722)

Four software checks verified the derivative against finite rotations,
the phase-to-range scale, the cancellation of common phase, and the
interval-to-endpoint weighting. The replay used 240 saved intervals and
2,496 range weights. It ran no fits and opened no reserved flights.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_phase_windup_budget check
```

[Plan](ESA_PHASE_WINDUP_PLAN.md) · [Numerical receipt](esa-phase-windup-budget.json)
