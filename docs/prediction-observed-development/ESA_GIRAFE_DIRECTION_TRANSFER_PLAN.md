# Can the horizontal quartz axes track the aircraft's motion?

Use only the opened ESA development recording. Reconstruct the horizontal
specific-force vectors from the sealed continuous carrier path at the
earlier receiver times. Compare them with the independent horizontal
quartz channels at the same time support. Use both zero-field geometries
and the same gravity and acceleration kernel as the earlier magnitude
comparison.

Divide the first 384 seconds of the continuous path into sixteen
nonoverlapping 24-second supports. Use the first ten supports to estimate
a fixed two-axis orthogonal alignment and a constant offset. Allow either
axis handedness because the logged quartz signs have not been qualified.
Test clock offsets of minus 0.1, zero and plus 0.1 seconds. For each
geometry, select the offset and alignment with the lowest earlier error.
Save the selection before reading the last six support results. Retain
all alternatives, both singular values of the earlier directional
fit and the signed errors on all six check supports.

Compare the vector error and its north component with the scale of the
previously constructed north–south path change. Compare later errors
with the earlier alignment against the result of applying a second
alignment fitted only to the six check supports, as a stability
diagnostic. A large internal error or alignment change leaves the
measurement unsuitable for deciding between the two paths. Even good
agreement would leave common position error and cross-flight uncertainty
open.

Use one task and one thread. Scan at most the sealed GIRAFE file's declared
row count to stage only these support samples. Allow one setup and 16
support evaluations. No model or trajectory fit, later comparison
positions or reserved flight data enter the study.
[Previous magnitude comparison](ESA_GIRAFE_HORIZONTAL_WITNESS_RESULT.md)
