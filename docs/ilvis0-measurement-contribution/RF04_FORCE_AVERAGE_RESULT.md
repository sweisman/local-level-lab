# Averaged force directions from the RF04 stretch

Both globe models predicted the direction of measured force more closely
than either disc model on the later part of this stretch. That ordering
held for both GPS reconstructions, both IMU packet clocks and both
averaging widths. The four models all used aircraft attitude supplied
by RF04 at the center of each window. [Frozen plan](RF04_FORCE_AVERAGE_PLAN.md)

| Averaging window | Earlier / later windows | Later globe error, RMS | Later disc error, RMS | Largest RMS difference between any two fitted predictions |
| --- | ---: | ---: | ---: | ---: |
| Quarter second | 265 / 118 | 0.169–0.172° | 0.297–0.298° | 0.280° |
| One second | 265 / 118 | 0.168–0.169° | 0.295–0.296° | 0.279° |

The first 265 windows estimated a constant mounting rotation for each
prediction. All scores in the table use the later 118 windows. Both clocks
retained the same centers, with median differences of about 1.6 ms between
their actual packet edges and a maximum difference of 3.75 ms. On the
nominal clock, averaging brought the globe direction error down from about
1.02° on the same centers. The earlier single-packet header-clock check
had only 19 later windows, so its error scores are for a different subset.
[Single-packet scores](RF04_FORCE_DIRECTION_RESULT.md)

The result establishes a ranking for this RF04-assisted comparison.
The RF04 attitude comes from its separate navigation solution, and
its one-second output leaves aircraft rotation within a window
unmeasured. The test still needs an independent error limit for that
motion and for the receiver-derived acceleration before it can support a
shape decision from accelerometry alone. Within each shape, switching
the tested background field changed the RMS by under 0.001°.

The sealed run used one task and one numerical thread. It produced
32 scores and 48 prediction comparisons with all 81 charges accounted
for, zero new Earth-model fits and zero reserved-data reads. The
result includes the selected seconds and the fit and timing summaries.
SHA-256 `a687d34bdf03de7909985aa32704d12aeb1a4c63ea7d9356cadc0d705bb6d587`.
[Machine-readable result](rf04-force-average-result.json) ·
[Frozen execution evidence](rf04-force-average-evidence/README.md)
