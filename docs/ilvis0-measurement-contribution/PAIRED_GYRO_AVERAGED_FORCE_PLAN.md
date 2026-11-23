# Check whether averaging force resolves the paired motion mismatch

Use the exact 24 October 2009 recorder pair and the earlier receiver paths,
packet centers, clocks and training split from the [single-packet comparison](PAIRED_GYRO_INTERVAL_RESULT.md).
Verify the original packet-selection hash for both recordings. On the
24 October recording, sum complete accelerometer packets within 0.25 s
and 1.0 s centered on each original packet midpoint. Require at least 95%
support, with each packet inside the original allowed support. Average the
required force over the same endpoints in each model's fixed axes using
four-point quadrature and the original fourth-degree GPS path.

Score two versions of the force-direction requirement. First use only
the acceleration half-count allowance at each endpoint. Then allow for
orientation change within the averaging support. Under a model that
represents each packet by its mean, rotating a vector by at most angle
*a* can change it by at most \(2\sin(a/2)\) times its norm. Use a full
support's recorded gyro travel as *a*, with the previous clock margin,
half-count gyro allowance and frame-rate allowance. Add that allowance
over the force packets before converting it to a directional cone. Score
the turn between originally adjacent targets with both endpoints supported against the larger gyro
travel from the two recorders, with the same allowances as before.

This is a sensitivity calculation with fixed models, biases and receiver
paths. The packet model and the logged angle budget do not bound actual
within-packet motion. Report each paired candidate, both centers' support
rules and the change in the number of shortfalls. Keep the earlier check
as its own result. Use one task on one thread, two bounded decodes,
64 fixed histories and at most 77,824 required-force evaluations. Allow
90 seconds, zero Earth-model fits and zero reserved-data reads.
