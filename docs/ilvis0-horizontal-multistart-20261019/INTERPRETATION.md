# What the timing search established

The matched search completed all 38 starts and eight exact reconstruction checks
in 6.59 hours. **37 individual fits passed; both fresh controls passed. Only
two of six selected independent-repeat comparisons passed.** The four-minute
IMU21 horizontal-only sensitivity result therefore remains unresolved.

Each model received the same three timing starts and two independent parameter
seed families. The lowest returned cost in each family determined its result;
no inconvenient attempt was discarded. This is a finite search, not a guarantee
that the global optimum was found.

| Comparison | What happened |
|---|---|
| Specified-field globe, both processing cases | Both independent searches found the same lower-cost solution and passed the cost and prediction checks. |
| Zero-field globe, both processing cases | Different local solutions remained. Selected costs differed by about 0.0145%; north/east prediction RMS differences were about 3.0/2.0 mm, above the 1 mm limit. |
| Flat, no upstream removal | Costs agreed within the limit, but north prediction RMS differed by 1.32 mm, above the 1 mm limit. |
| Flat, profiled removal | Selected costs and predictions disagreed: north/east RMS differences were about 38/62 mm. |

The selected specified-field globe costs are about 0.0807, zero-field globe about
5.56, and flat about 1,774–3,646. That ranking persists across the searched seed
families. The numerical gate still withholds a complete matched interpretation
because the other candidates did not reproduce their own best predictions.
An unfinished or nonrepeatable fit does not provide evidence for flat geometry.

## Why height remains important

Even the repeatable specified-field solutions have about 646 m of **unscored
height error**. Other selected target solutions have roughly 20–25 km. These
are reconstructed errors against receiver altitude, not actual aircraft motion.
Removing height from the objective permits trajectories that are poor full-flight
reconstructions. The earlier complete IMU8 sensitivity comparison also has large
unscored height errors.

The check shows how the horizontal score behaves when height is not scored. It
does not remove height from initialization or propagation, isolate gyroscopes
from accelerometers, or establish a physically adequate flight reconstruction.
The original full-position **53 globe / zero flat / zero unresolved** findings
remain separate and unchanged.

## Next measurement check

Further widening this timing search is deferred. The next step defines what
replaces a removed IMU channel and checks that replacement on known-answer
examples before any new recorded-data fit. Gyroscope-free attitude cannot be
silently supplied by the fused navigation solution; acceleration-free tilt
cannot still be initialized from the omitted accelerometer observations.

[All attempts and source metadata](DETAILS.md) ·
[Measurement-contribution plan](../ilvis0-measurement-contribution/README.md).
