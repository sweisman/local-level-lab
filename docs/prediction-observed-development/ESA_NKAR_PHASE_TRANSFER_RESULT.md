# Can a ground GPS correction improve later aircraft readings?

On ESA development flight 187, an earlier correction from the nearby Nuuk
Museum receiver left the later aircraft error essentially unchanged. The
correction from the more distant Qaqortoq receiver reduced it by 0.018 mm.
Both corrections changed the saved score by less than 0.4% of the gap
between the models in that score.

| Correction on later readings | RMS range difference | Signed change as a share of the saved score gap |
| --- | ---: | ---: |
| No ground correction | 4.7332 mm | 0% |
| Nuuk Museum | 4.7335 mm | +0.124% |
| Qaqortoq | 4.7155 mm | −0.317% |

Both stations used the same satellites and aircraft observations on 335
earlier intervals and 120 later intervals. The earlier residuals determined
one multiplier per station, 0.0523 for Nuuk Museum and 0.1762 for Qaqortoq.
The table uses clock-centered carrier ranges on the shared support. The
small improvement at Qaqortoq does not establish that a more distant
station would work better on another recording.

The comparison leaves aircraft antenna and tracking errors, absolute
aircraft position error, and inertial errors open. It used no new model fits
or reserved flights. [Frozen method](ESA_NKAR_PHASE_TRANSFER_PLAN.md) ·
[Verified result](esa-nkar-phase-transfer-result.json)

The result includes the earlier and later range differences for each shared
satellite, the later score weights, and the hashes of the three parent results.
To check it against the sealed local study, run
`env PYTHONPATH=analysis ~/venv/bin/python -m lll.esa_nkar_phase_transfer report`
from the repository root. This reads saved results and runs zero fits.
