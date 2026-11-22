# Longer generated solver confirmation

The short generated controls tested both bounded solvers on the three
physical candidates, all 26 calibration directions, and nominal 200 Hz or
header-elapsed 300 Hz timing. This separately frozen confirmation tests
whether their **withheld forecasts** still agree over a longer noisy path.

Preselect six 120-second generated histories: each of the three candidates
under both exact-grid clock policies (200 Hz nominal and 300 Hz header).
Put Z-gyro calibration near its permitted boundary, use a separate noise
seed for each history, and preserve one declared route and processing case.
Fit the first 79 of 119 receiver reports and predict the final 40 without
receiver updates. Run both bounded solvers from zero and fixed perturbed
starts: **24 identities**. The source generator remains separate from the
fitter, but all six histories come from the same declared generator family.

Before launch, qualify source and environment hashes, task-level recovery,
and a separately frozen short real-worker preflight. Freeze inputs, exact
seeds, the numerical environment, four one-thread workers, finite
per-task call and packet-visit limits, and a cooperative wall cap. Charge
starts before work; preserve failures. Do not read observed aircraft or
reserved ESA confirmation data.

The numerical confirmation gate is preregistered: all 24 fits must pass
their stopping checks, each fixture's four later forecast paths must stay
within **0.1 m** of one another at every withheld report, and the four
training costs must differ by at most **0.01** in the existing normalized
objective. Score generated physical error separately; it cannot be hidden
by close solver agreement. A failure blocks the proposed stopping-rule
revision and triggers saved-result diagnosis, not a wider allowance or a
changed gate within this study.

Even a pass would qualify only the generated numerical method. The next
gate is a separately frozen observed development comparison on preselected
groups, with every original failed fit label preserved. The generated
study cannot establish real-aircraft predictive coverage or an Earth-model
decision. It also cannot resolve how irregular 200 Hz packet-header times
relate to the underlying integration interval.
