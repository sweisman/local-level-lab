# Verify the aircraft motion evidence

This evidence covers ESA recording 187 and two paired NASA flights. It
keeps seven completed calculations and two stopped attempts, including
the source mismatch between 20 and 24 October. The checks use no new
model fits.

| Evidence | What can be checked from the public tables |
| --- | --- |
| [ESA clock transfer](../prediction-observed-development/ESA_GIRAFE_LEVEL1_AIRBORNE_RESULT.md) | Recompute the accepted time shift from every saved score. The reversed-sign vertical values agree at zero shift on both airborne intervals. |
| [ESA tilt sensitivity](../prediction-observed-development/ESA_GIRAFE_TILT_IDENTIFIABILITY_RESULT.md) | Recompute 20 orientation changes and force-magnitude changes from the saved vectors. |
| [20 October NASA pair](../ilvis0-measurement-contribution/PAIRED_GYRO_MOTION_RESULT.md) | Verify the recorder identities and the packet and one-second summaries. |
| [24 October NASA pair](../ilvis0-measurement-contribution/PAIRED_GYRO_AVERAGED_FORCE_RESULT.md) | Match the 64 averaged summaries to the single-packet cases. Both averaging widths retain the interval counts and remove the recorded shortfalls. |

From the repository root, run the public check with Python and the
repository's analysis package on its import path.

```sh
env PYTHONPATH=analysis ~/venv/bin/python -m lll.aircraft_motion_evidence
```

Add `--runtime` when the local frozen study directories or their archive
copies are available. This also checks the manifests, source and input
bytes, source identities, result envelopes and charged operation counts.
That check requires local access to the original inputs. The public check
recomputes summaries from published values. Re-deriving the values from
the sensor recordings is a separate step.

The local run checked 1,915 frozen source bindings and 42 input files
across the nine study records. The related focused test run passed eight
tests.

The ESA exports agree on the copied vertical channel. Actual platform
orientation and horizontal motion are still open. The NASA paired checks
use two sensors on one aircraft per flight. They supply a scale comparison
and leave an independent physical motion limit open. Neither finding
qualifies reserved ESA data or establishes an Earth-model decision.
