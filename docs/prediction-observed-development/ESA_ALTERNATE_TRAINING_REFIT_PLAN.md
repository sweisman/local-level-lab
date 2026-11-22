# Finite ESA training-source sensitivity refit

Question: do centimetre-scale changes in **training receiver positions**
alter the saved 400-training/120-later model ordering on the opened ESA
development recording? The two alternate 400-row inputs are fixed in
[training material](ESA_ALTERNATE_TRAINING_MATERIAL_RESULT.md). Both use
the original `air1` velocity, quality and covariance fields so only the
training coordinates differ.

Run six matched fits: `mosaic03` and `pwrpak7` training positions ×
specified-field globe, zero-field globe and flat disc. Use only the existing
profiled-removal, increment-error setting and original primary start 0.
Keep the same raw IMU prefix, model method, 400/120 split, numerical bounds,
200-evaluation limit and 700,000 native-call/45-billion packet-visit ceiling
per task. Four workers, one numerical thread each, maximum 7,200 seconds.
The earlier 24-fit matrix took 10,357 seconds with four workers; six fits
are expected to take roughly 45–90 minutes. This is a finite development
sensitivity, not a new frozen confirmation campaign.

The worker must have task-level recovery and source-bound qualification
before launch. Prepay calls before execution, preserve completed successes
and numerical failures, and never rerun a sealed task. Later receiver
positions are absent from all fit inputs. After closure, score the same 120
later `air1` receiver reports and compare with the original saved matrix.
If any required fit fails its original numerical stopping check, report
that setting unresolved. No selection, method or threshold may be changed
in response to the outcome. Seven reserved ESA flight groups remain closed.
