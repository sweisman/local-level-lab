# ESA start choices under the revised rule

The sealed ESA development run passed **8/8 model and processing groups**
when its saved fits and forecasts were checked under the revised start rule.
Three groups chose different primary starts with the wide and faster
calculations. In all eight groups, the saved training costs were near-tied
under the previously declared `1e-8` *relative* tolerance. No absolute cost
allowance was added for the observed objective.

The largest difference between wide and faster forecasts across near-tied
starts was **0.00407 m**. The largest spread within one method's near-tied
starts was also **0.00407 m**, below the fixed 0.01 m software-method limit.
The audit read the archived, hash-checked fits and forecasts. It made **no new
fits** and read no original or reserved aircraft file.

This is a **retrospective diagnostic**, not a new qualification. The original
observed run still fails its frozen exact-primary-start gate at **5/8**. The
fresh generated study passed the revised rule, but a separate, prospectively
frozen observed development input must pass before the faster calculation can
replace the established wide calculation for aircraft data.

[Machine audit](observed-start-v2-retrospective.json) ·
[Original observed result](../esa-observed-model-dispatch-v2/README.md) ·
[Generated qualification](START_EQUIVALENCE_V2_RESULT.md).
