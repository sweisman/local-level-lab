# What evidence could rule out a score-changing aircraft error?

The matched Qaqortoq measurements cover most of the carrier score's
sensitivity. The part they miss still matters. In the fitted aircraft path,
the two parts nearly cancel, so a small total residual cannot be used as an
absolute error bound.

| Signed contribution from the saved aircraft path | Score units |
| --- | ---: |
| Directions covered by Qaqortoq | +0.001917 |
| Directions outside the match | −0.001804 |
| Sum before ground correction | +0.000112 |
| Sum after the correction learned earlier | −0.000028 |

The saved model-score gap is 0.044958. The sum above is based on the path
fitted to the aircraft carrier phases, so its cancellation leaves the true
aircraft error open. [Matched ranges](ESA_QAQ_GROUND_SCORE_RESULT.md) ·
[Earlier correction](ESA_QAQ_PHASE_TRANSFER_RESULT.md)

## Accuracy requirements

The error contributions below must add to less than the saved gap after
including the absolute residual of 0.000028. Each coefficient converts a
separately supported error cap into score units. Both range RMS caps use
the same set of 2,496 signed half-second values, after projecting onto the
listed directions.

| Unknown error cap | Score units per unit of error |
| --- | ---: |
| Aircraft error left after the ground correction in the matched directions, RMS metres | 22.369 |
| Aircraft error outside the matched directions, RMS metres | 4.521 |
| Position error at every reference time, metres per coordinate | 0.021929 |
| Acceleration of the position error, RMS m/s² | 0.0004464 |
| Error from using the linear range calculation, in score units | 1 |

For example, with 1 m of anchor error per coordinate and 2 mm RMS outside
the match, the remaining allowance in the matched directions is about
**0.62 mm RMS**. This illustration uses the earlier constructed error's
motion limit and sets the linearization error to zero. None of those caps
has been established for the aircraft. The verifier therefore returns
**abstain**. A local ground receiver can constrain some shared errors, while
aircraft-specific and remaining directions require their own evidence.
[Anchor analysis](ESA_CARRIER_ANCHOR_ERROR_RESULT.md) ·
[Pending local observation](ESA_GROUND_REFERENCE_AVAILABILITY.md)

The [geometric remainder check](ESA_CARRIER_RANGE_REMAINDER_RESULT.md) now
provides an explicit value for the linearization term once the anchor and
motion caps are supplied. The earlier illustration used zero for that term.
The actual carrier, anchor and motion errors still need independent limits.

The arithmetic uses five pinned reports, and two tests passed. The
[budget receipt](esa-reference-error-budget-v1.json) has SHA-256
`9c0678e6c6c75e5fe45ff31d0c9905669e3b0789bee926570ba7c4a13f7347a6`.
It runs without original flight recordings or new fits.

```sh
env PYTHONPATH=analysis ~/venv/bin/python -m lll.esa_reference_error_budget check
```
