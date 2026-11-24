# With all satellites, the tested errors cannot close the ESA score gap

With the full satellite set, the modeled trajectory error can account
for at most **50.2%** of the two-minute ESA development score gap under
the example limits. A directly checked error path accounts for 49.1%.
For the three satellite screens, the bounds still straddle the full gap.

| Satellite set | Share reached by a verified path | Upper bound on the share | Can this error model close the gap? |
| --- | ---: | ---: | --- |
| Full set | 49.1% | 50.2% | Excluded under the tested limits |
| 0° starting tilt screen | 86.2% | 100.6% | Undetermined |
| 5° starting tilt screen | 89.7% | 102.5% | Undetermined |
| 10° starting tilt screen | 96.8% | 111.4% | Undetermined |

The example allows 1 m per coordinate at each of six position anchors,
1.876 mm/s² RMS in trajectory-error acceleration, and 1 mm and 2 mm RMS
of additional GPS range error inside and outside the ground receiver's
coverage. The upper bounds include the verified fixed-transmit
geometric remainder. They apply to trajectories with continuous
velocity and square-integrable acceleration. Using all 361 carrier
and score times preserves every relevant position while allowing the
smoothest interpolating path.

The full satellite set retains low-elevation rays. Its real airborne
antenna response and shared errors still need independent bounds.
The numbers above give a quantitative result under the example
limits. The development flight supplies no measurement showing that
the limits hold in operation.

All four numerical solves concluded before their cap and the checks
of the path and upper bound ran separately. One task completed 245
charged checks. Seventeen focused tests passed. No new physical-model
fits ran and no reserved flights were opened.

[Frozen plan](ESA_CARRIER_CONTINUOUS_BOUND_PLAN.md) ·
[Saved paths, bounds and completion receipt](esa-carrier-continuous-bound-result.json)
