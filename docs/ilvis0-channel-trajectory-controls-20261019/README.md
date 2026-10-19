# Independent trajectory-force diagnostic

**18/18 controls passed.** The batch used 1134 force evaluations and 2268 scalar comparisons in 0.80 seconds. It read no recordings and performed no fits or native integrations.

This checks a new calculation, not instrument accuracy or flight evidence. The reference uses independent Cartesian geometry and derivatives; the adapter uses local coordinate metrics. Two changing attitudes are checked at every epoch.

| Reference model | Motion | Specified-field globe RMS | Zero-field globe RMS | Flat RMS | Software check |
|---|---|---:|---:|---:|---|
| sphere_rotating | stationary | 6.713998e-16 | 6.713998e-16 | 6.713998e-16 | pass |
| sphere_rotating | slow | 9.495027e-16 | 0.0003602079 | 0.0003690539 | pass |
| sphere_rotating | eastbound | 7.752657e-16 | 0.02358849 | 0.03006832 | pass |
| sphere_rotating | northbound | 1.061576e-15 | 4.30539e-05 | 0.007781618 | pass |
| sphere_rotating | changing direction | 9.090796e-16 | 0.01525166 | 0.02167901 | pass |
| sphere_rotating | climbing | 1.314527e-15 | 0.007182204 | 0.00991276 | pass |
| sphere_still | stationary | 6.713998e-16 | 6.713998e-16 | 6.713998e-16 | pass |
| sphere_still | slow | 0.0003602079 | 9.090796e-16 | 8.846e-06 | pass |
| sphere_still | eastbound | 0.02358849 | 1.096391e-15 | 0.006479839 | pass |
| sphere_still | northbound | 4.30539e-05 | 9.495027e-16 | 0.007824672 | pass |
| sphere_still | changing direction | 0.01525166 | 9.090796e-16 | 0.006428548 | pass |
| sphere_still | climbing | 0.007182204 | 1.256074e-15 | 0.01709473 | pass |
| flat_still | stationary | 6.713998e-16 | 6.713998e-16 | 6.713998e-16 | pass |
| flat_still | slow | 0.0003690539 | 8.846e-06 | 9.495027e-16 | pass |
| flat_still | eastbound | 0.03006832 | 0.006479839 | 1.314527e-15 | pass |
| flat_still | northbound | 0.007781618 | 0.007824672 | 6.713998e-16 | pass |
| flat_still | changing direction | 0.02167901 | 0.006428548 | 1.256074e-15 | pass |
| flat_still | climbing | 0.00991276 | 0.01709473 | 8.222934e-16 | pass |

RMS values are acceleration-magnitude mismatches in m/s² with exact generated trajectories and known calibration. They are not whitened costs, confidence levels, model detections or measured device errors. Stationary controls correctly have no magnitude separation. Incorrect-model outcomes are preserved without requiring discrimination.

Passing qualifies only this exact-trajectory calculation. Receiver differentiation, its temporal uncertainty, averaging and synchronization, calibration assumptions and recorded-data selection still need qualification. The main 53-stretch findings are unchanged.

[Frozen scope and limits](PLAN.md) · [Channel-removal requirements](../ilvis0-measurement-contribution/CHANNEL_CONTROLS.md) · [Next step](NEXT_PLAN.md).
