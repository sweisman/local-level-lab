# The linked calibration bounds leave the forecast gap unresolved

The combined upper bound remains **53.04 units** for ESA development flight
187, compared with a **25.41-unit** gap between the zero-field globe and
disc forecasts. The new check used the earlier residuals from the
high-scoring proposals after linking their calibration terms physically.

Ten of the eleven ranges supplied a usable residual direction. Each of
those ten was tested at **12.61 units** and again at its highest previously
tested score. The eleventh range retained its previous bound. Splitting
each tested range along its two most sensitive physical coordinates
tightened 17 of the 20 certificates, but none ruled out the tested score.
The smallest upper bound on the weighted slacks was 426.11. A certificate
would need to be strictly negative to rule a score out. The calculation
leaves open how closely the linked model can approach the forecast gap.

The [first attempt](esa-linked-floor-support-v1-evidence/README.md) stopped
before subdivision because the code reserved a derivative step without a
bound operation. It recorded ten technical failures, one planned skip and
20 charged operations. A targeted regression check reproduced the failure.
The [accounting correction](ESA_LINKED_FLOOR_SUPPORT_ACCOUNTING.md) reserved
the derivative with the whole-box check. Under its separate freeze, all
eleven tasks finished in 72 seconds with 120 charged operations. Ten focused
tests passed. The original results and charges are preserved.

The checks used a saved trajectory approximation. The strongest physically
linked points checked by full integration moved the forecasts by 0.432
units combined. Higher scores remain unverified, and a tighter global
bound on the calibration and integration errors is still needed.
[Full-integration check](ESA_LINKED_PHYSICAL_REPLAY_RESULT.md)

[Frozen calculation](ESA_LINKED_FLOOR_SUPPORT_PLAN.md) ·
[Retained bounds](esa-linked-floor-support-result.json) ·
[Execution receipts](esa-linked-floor-support-evidence/README.md) ·
[Reproduction bundle](esa-linked-floor-support-evidence/bundle.zip)
