# One-thread native compatibility

The execution controls pass all nineteen tests. This separate gate checks the
scientific calculations under four workers, each using one numerical thread.
The earlier native qualification and all its results remain unchanged.

Use the same 24 generated cases: three candidate geometries, two processing
cases and four control families. Copy the exact compressed inputs and preserve
all 27 physical and 15 common-error columns. The callback-driven acceptance
calculation retains the original limits: 1 micrometre for independent/central
positions, 20 micrometres per normalized parameter for all 162 finite-difference
columns, and a 10 micrometre arithmetic margin on generated probe containment.

Every native point, predicted coordinate, Jacobian entry and warning must match
the sealed four-thread reference. Floating-point arrays must have identical
shapes and binary64 bytes, including signed zero. Every full factored-bound
report and reference binding must have identical canonical JSON. Do not loosen
these requirements after observing this study.

Freeze Python, NumPy, SciPy, compiler versions, complete numerical sources,
inputs and reference outputs. Charge before each operation. Limits are 24 starts,
78 native evaluations, 19,632 packet visits, 348 bounds, 7,536 bound steps and
300 cooperative seconds. No retries, archive reads or observed fits. No process
signals enforce the deadline. Run all preselected cases, retaining any failures.

Only a fully passing, receipt-verified result permits the longer generated
prediction comparison. Compatibility does not establish observational coverage,
floating-point interval certification or a scientific detection.
