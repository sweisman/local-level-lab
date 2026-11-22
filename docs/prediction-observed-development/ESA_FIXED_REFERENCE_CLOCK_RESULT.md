# Reykjavík receiver clock replay

Applying the recorded aircraft clock offsets to GPS time, code and carrier
phase together leaves the vertical disagreement with the aircraft GPS
position solution at **0.85 m RMS**. It changes the reconstructed vertical
path by at most 6 cm over the 30-minute ground stop.

| Treatment of recorded aircraft clock offset | Difference from GPS position solution N / E / up RMS (m) | Maximum change from original path N / E / up (m) |
| --- | ---: | ---: |
| Original log | 0.273 / 0.404 / 0.854 | 0 / 0 / 0 |
| Apply offset to time, code and phase | 0.273 / 0.404 / 0.853 | 0.025 / 0.025 / 0.060 |
| Apply offset to code and phase only | 0.228 / 0.334 / 0.728 | 0.222 / 0.297 / 0.572 |

The comparison uses the same 61 observation times, ten common GPS
satellites and fixed reference station as the
[carrier-phase check](ESA_FIXED_REFERENCE_PHASE_RESULT.md). The first
observation anchors the path. The table summarizes the 60 later times. The aircraft
file omits the header flag that describes whether the receiver already
applied the logged correction. The third row checks sensitivity to
timestamps that would already be corrected. A smaller difference from
the aircraft GPS solution cannot establish that this was the convention.

The complete correction preserves the epoch pairing and leaves the
transmit times calculated from the raw code within 0.06 ns of the original.
That numerical check verifies the algebra used by the replay. The result
leaves the source of the vertical disagreement open. A raw Doppler
comparison can check motion independently of the carrier-phase
accumulation over this stop.

[Frozen plan](ESA_FIXED_REFERENCE_CLOCK_PLAN.md) ·
[Recorded results and hashes](esa-fixed-reference-clock-result.json)
