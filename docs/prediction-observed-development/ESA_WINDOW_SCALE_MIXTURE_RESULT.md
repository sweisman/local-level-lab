# Allowing forecast error to vary between windows

Seven of eight windows on ESA recording 187 fell inside the reference
range with the Student error model, compared with six under the Gaussian
model. Both input conventions gave the same result. The forecast paths and
expected covariance stayed fixed. The Student model allows whole windows
to have larger or smaller errors than the Gaussian model expects.

| Input convention | Gaussian negative log score | Student negative log score | Windows inside, Gaussian → Student |
| --- | ---: | ---: | ---: |
| Increments | −12,261.52 | −12,270.62 | 6/8 → 7/8 |
| Point rates | −12,261.52 | −12,270.62 | 6/8 → 7/8 |

Lower negative log scores indicate better predictions. Each convention
improved by 9.10 units across the omitted windows. The six donor windows
selected 320 degrees of freedom in two folds and 160 in the other two.
The previously low-error turn moved inside the reference. The high-error
steady window still exceeded its upper reference, at 491.84 versus 482.41.

All eight software tasks completed in 10.5 seconds with no errors and
zero new trajectory fits. This is a development comparison within a single
flight. The reference counts do not establish aircraft prediction coverage.
The seven reserved flight groups remain closed.
[Frozen plan](ESA_WINDOW_SCALE_MIXTURE_PLAN.md) · [Reproduction evidence](esa-window-scale-mixture-evidence/README.md)
