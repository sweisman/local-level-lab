# Next solver control: full calibration and withheld paths

The [short generated comparison](GENERATED_SOLVER_FORECAST_RESULT.md) passed
all 24 fits and six four-fit forecast checks. It freed only six nuisance
parameters and predicted four seconds ahead. The 20-group aircraft study has
50 fixed failed fit labels, so this short control cannot change them.

The next finite software pilot will use the existing independently generated
noisy flight constructor and the shared training-only forecast protocol.
It will retain all 26 physical calibration directions, hold out the final
third of receiver positions and compare the original bounded solver with
the separately implemented verified-stop solver on identical inputs and
parameter bounds. Begin with one generated 60-second, 300 Hz, 59-receiver-
epoch case and two fixed starts per solver: four task identities. Use one
declared noise law, one specified-field globe truth, one clock construction
and a fixed seed. No aircraft or reserved confirmation input enters.

Before fitting, freeze source and native kernels, generator seed, exact
noise law, training cut, two starts, thread allocation and a finite native
call/packet-visit allowance. Qualify the real worker and reboot recovery.
Run a separately frozen one-task, 10-second real-worker preflight first;
its pass means the source-bound worker saved the required artifacts, not
that an eight-evaluation calibration fit was scientifically adequate.
The first preflight froze its numerical environment outside the thread guard
and stopped before any native call. Its terminal record is retained. The
separate repaired freeze requires the one-thread environment at request and
preparation time as well as during execution.
Save each forecast before generating or reading later truth. Report every
numerical stop, objective, fitted calibration, later-path error against
known truth and pairwise path spread. Preserve failed tasks. A separate
multimodel and alternate-clock control is required before a general
stopping-rule change; this four-task pilot is a diagnostic, not confirmation.

If the four fits agree, extend only through a new freeze to the other two
physical models, both clock constructions, near-boundary calibrations and
longer/noisier histories. If they disagree, diagnose the saved fit and path
differences without opening aircraft outcomes or relaxing a failed gate.

The [sealed pilot result](FULL_CALIBRATION_SOLVER_RESULT.md) records 4/4
numerical stops and 4/4 generated physical-screen passes. The next
multimodel extension remains a separate freeze; the original aircraft
stopping failures are unchanged.
