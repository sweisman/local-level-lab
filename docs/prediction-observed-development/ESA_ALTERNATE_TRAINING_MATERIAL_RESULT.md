# Alternate receiver positions are ready for a bounded refit test

The [training-only preparation](ESA_ALTERNATE_TRAINING_MATERIAL_PLAN.md)
matched the first **400** reports of the opened ESA development flight to
both parallel GNSS-only PPP exports. The original `air1` positions agree
exactly with the sealed parent input. Only latitude, longitude and height
were changed; velocity, quality fields and the original covariance were
retained to isolate coordinate choice. The source files were hash-checked,
but later positions were not decoded or staged for fitting. Two local
coordinate controls pass. A separate [source-bound audit](esa-alternate-training-source-audit.json)
compares the staged rows with the original matrix's actual training input:
**all 400 rows in each export match in every non-position field**. Its two
preservation tests pass.

| Replacement training positions | RMS change, north/east/up | Largest change, north/east/up |
|---|---:|---:|
| `mosaic03` | 1.24 / 1.58 / 2.76 cm | 3.17 / 2.37 / 6.11 cm |
| `pwrpak7` | 0.72 / 0.69 / 3.49 cm | 2.39 / 1.71 / 6.49 cm |

Both complete 400-row alternatives, their hashes and the source bindings
are in the 68 KB [compressed training material](esa-alternate-training-material.json.gz).
This is **input preparation**, not a refit. The existing
[fixed-forecast check](ESA_FIXED_FORECAST_RECEIVER_MARGIN_RESULT.md) held
calibration constant; these inputs enable a separate test of whether small
changes to training positions move the fitted calibration or later model
ranking. The [separate six-fit result](ESA_ALTERNATE_TRAINING_REFIT_RESULT.md)
has now closed: all six fits pass and both alternate training sources retain
the same numerical model ordering on the fixed later positions.
Neither the relative PPP comparison nor the staged training inputs establish
absolute receiver accuracy. The seven reserved ESA flight groups remain
closed.
