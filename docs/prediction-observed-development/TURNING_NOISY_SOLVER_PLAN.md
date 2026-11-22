# Independent bounded search at the two noisy turning points

## Question

The original generated turning fits ended with low cost but did not pass the
frozen full-correction stopping check. Can an independent bounded algorithm
find a lower feasible cost or a point that passes that **same** check?

Use only the two sealed generated turning training problems. Rebuild their
noise, receiver reports, native operator, bounds and 26-parameter objective
from the original recipe and verify every relevant hash. Preserve the two
original failed fit labels. No observed or protected recording is opened.

## Methods and limits

Run SciPy's bounded trust-region reflective and dogbox algorithms, each
starting from the saved failed point, for four tasks total. The saved point is
nudged only 10⁻¹² inside exact numerical bounds as required by the new
algorithm. Use the complete native analytic Jacobian and the unchanged
objective. Each task has at most 80 charged native tangent calls, including
one fresh final evaluation and the original full-correction stability check.
No retry or method tuning follows a completed task. Two workers use one
numerical thread each; the cooperative wall limit is 20 minutes. Generic
task recovery must qualify before launch, so a reboot can resume only
unfinished work under the original allowance.

Record SciPy's own termination separately from the original stopping gate,
the final cost, cost change from the sealed parent and the original gate's
stationarity, actual relative cost change and physical-position components.
A lower cost does not automatically validate a model. If either method finds
a passing point, a separate matched solver policy would still need known
answer and multi-start qualification before a larger geometry study. If none
does, diagnose whether the full-correction gate is overstrict near a noisy,
weakly identified optimum; do not quietly relax or relabel the old fits.

The [known-optimum control](TURNING_KNOWN_OPTIMUM_RESULT.md) already passed
four exact-target fits. Focused software tests of both new methods against
known objectives, source/environment hashes, a finite study definition and
reboot-recovery qualification are required before this run.
