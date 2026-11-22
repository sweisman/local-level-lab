# How far did the saved forecasts stay on track?

The specified-field globe forecasts followed the measured path far more closely
than the zero-field globe forecasts on this ESA development window. At the full
400-position horizon, the specified-field forecasts had 8.10–16.97 m horizontal
RMS error. The zero-field forecasts had 7.26–8.17 km. Four of the 16 primary
forecasts met all four fixed accuracy limits at that horizon. All four used the
specified field and the receiver error policy that allowed persistent errors.

The forecasts were sealed before the later positions were decoded for scoring.
The fits used 800 earlier positions from ESA recording 187. The score uses the
next 400 positions, about 6 minutes 40 seconds. Each row below combines two
processing assumptions and two solvers. Their results agree at the shown precision.

| Globe model | Receiver error policy | Horizontal RMS | Height RMS | Primary paths within all limits |
|---|---|---:|---:|---:|
| Specified field | Short correlation | 16.97 m | 20.23 m | 0/4 |
| Specified field | Persistent errors | 8.10 m | 21.18 m | 4/4 |
| Zero field | Short correlation | 8,166.66 m | 108.24 m | 0/4 |
| Zero field | Persistent errors | 7,262.30 m | 41.23 m | 0/4 |

At both the first 120 and the first 240 positions, eight of 16 primary forecasts
met every limit. These were all eight specified-field paths. Including the
alternate starts gave the same pattern at every horizon. All 32 saved paths
were scored without refitting or correcting them from the later observations.

This comparison covers one window on one development flight and two globe models.
The accuracy limits describe prediction errors. Independent-flight error coverage
and a matched flat-disc forecast remain separate requirements.

[Scoring plan](ESA_DISPATCH_ACCURACY_PLAN.md) ·
[Earlier solver comparison](OBSERVED_DISPATCH_FRESH_RESULT.md) ·
[Reproduction evidence](esa-dispatch-accuracy-evidence/README.md)
