# The installed GPS system showed about 7 mm of range disagreement on the apron

On an 18.5-second excerpt of the receiver-selected Nuuk ground stop,
the aircraft's GPS ranges disagreed with the fixed-position prediction
by **6.93 mm RMS** over half-second steps and **7.03 mm RMS** over
one-second steps. A five-metre shift of the assumed antenna position
along any coordinate axis changed the reported RMS by less than
0.025 mm.

| Interval | Steps | Satellite range differences | RMS |
| --- | ---: | ---: | ---: |
| Half a second | 37 | 444 | 6.93 mm |
| One second | 18 | 216 | 7.03 mm |

The comparison used two carrier frequencies, the final satellite
orbits and clocks, and the earlier approximate parking position.
It removed common receiver-clock changes at each step. GPS satellite
G17 lacked a final clock product and was excluded throughout. The
recorded receiver-clock offsets ranged from 0.319 to 0.365 ms. The
first run stopped on those nonzero offsets before computing any range
residuals. The corrected run preserved the derived transmit times
by applying the RINEX correction to time, code and phase together.
[Clock convention](https://files.igs.org/pub/data/format/rinex304.pdf)

The excerpt precedes the available iMAR observations at that stop, so
this check assumes the aircraft stayed at its parking position. The
disagreement includes satellite, propagation and aircraft effects.
The 7 mm figures describe the whole residual on the apron. The earlier
2.10 mm target is for an error component in the moving-flight score.
The apron comparison supplies a check on the installed system under
ground conditions. Independent airborne bounds remain open.
[Accuracy requirements](ESA_CARRIER_ERROR_REQUIREMENTS_RESULT.md)

The corrected run completed 260 charged checks. Eight focused tests
passed. It used zero new downloads, physical-model fits or
reserved-flight reads.

[Corrected plan](ESA_APRON_CARRIER_CLOCK_PLAN.md) ·
[Result and source hashes](esa-apron-carrier-result.json) ·
[Preserved initial stop](esa-apron-carrier-v1-terminal.json)
