# Galileo ranges favor the original path over the tested northward shift

The same north–south displacement that would close the saved GPS score gap raises the Galileo range residuals by about half. The displacement peaks at **17.6 cm**. Both aircraft receivers show the same result on **120 one-second intervals** and **1,067 matched satellite changes** each.

| Receiver | Galileo range RMS on the original path | RMS after adding the displacement | RMS change in the modeled ranges |
| --- | ---: | ---: | ---: |
| Septentrio | 6.54 mm | 9.84 mm | 7.30 mm |
| NovAtel | 6.17 mm | 9.57 mm | 7.30 mm |

The projection of the original residuals onto the predicted change was −0.65% and −0.21% of that change for the two receivers. Both are close to zero. The recorded ranges show little of this particular displacement's predicted pattern.

The check used separate Galileo satellite observations and final orbit and clock products, while retaining the original GPS path and the same aircraft antenna. The two Galileo receivers share the antenna. The comparison tests one displacement and leaves other trajectory errors, the antenna response and independent in-flight accuracy limits open. No shape or field decision follows from this check alone. [Original displacement](ESA_MOTION_AXIS_SUPPORT_RESULT.md) · [Galileo observation provenance](ESA_GALILEO_PHASE_PATH_RESULT.md)

All 120 interval checks reproduced the sealed Galileo satellite selection. No aircraft trajectory was refitted and no original files were downloaded or reserved flights opened. [Frozen plan](ESA_GALILEO_NORTH_WITNESS_PLAN.md) · [Signed range residuals and completion receipt](esa-galileo-north-witness-result.json)
