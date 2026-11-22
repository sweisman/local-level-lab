# Tighten the dominant calibration ranges using the same score

Use the nine surviving calibration ranges from the [linked directional
study](ESA_LINKED_DIRECTIONAL_RESULT.md) on development recording 187.
Preserve all other ranges and their exclusions and bounds. Keep the exact
earlier-loss increase limit of 0.01, zero assumed earlier unshared error,
the original score directions and the original static-map allowances.

For each range, choose a single physical coordinate to bisect using the
largest width times outward derivative magnitude of the archived signed
score expression. Break ties by coordinate index. Derive the derivative
from the same linked static map, with no later GPS values. Audit that the
two closed children cover the parent, including the split boundary. On
each child, apply the existing stored-cut score and earlier-loss
certificates. Keep the original parent bound if the verified child cover
does not tighten it. Check every previously feasible witness in the
children that contain it before accepting an exclusion or a lower bound.

Use nine task identities, at most 45 charged bound calculations, two
workers with one thread each and a 120-second cooperative limit. Use zero
new fits, integration, original-file reads or reserved-flight reads.
Report the recombined upper bound against the original 25.41-unit gap.
The calculation checks the static map. The full nonlinear integration
remainder and aircraft uncertainty stay separate.
