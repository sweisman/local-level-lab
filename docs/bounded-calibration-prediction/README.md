# A bound-aware prediction control

The first software component now handles a calibration value that lies on its
allowed limit. Nine local checks pass, including 3,000 independently drawn
boundary cases, a case where training cannot identify one parameter direction,
and a dense independent calculation of the flight-style forecast adapter.

For an affine model with a **known Gaussian error law**, the code uses earlier
observations to bound the calibration combinations they can estimate. The
declared parameter limits bound the remaining combinations. It then adds an
allowance for future measurement noise. With 2.5% allotted to calibration and
2.5% to future noise, each coordinate interval has a mathematical coverage
lower bound of 95% **under those stated assumptions**. A parameter reaching a
limit does not make its uncertainty vanish. The intervals are marginal, not a
simultaneous three-dimensional or whole-flight region.

The [nonlinear generated-aircraft check](NONLINEAR_RESULT.md) has now completed
24 cases covering three physical models, two processing assumptions, both
retained IMU error laws and interior/boundary calibration. All 24 technical
cases completed. Withheld-position accuracy passed in all 24; one fit failed
its numerical stopping check, leaving 23 combined passes. The bounded
intervals contained all 2,880 tested coordinates for each withheld target,
but this small development matrix cannot establish 95% coverage. The median
latitude interval spans about **85 m north to south**; containment alone does
not show useful precision. The flight model is nonlinear, its real error law is unknown,
and the true calibration limits have not been independently measured. The
numerical failure and nonlinear coverage need separate qualification before
any recorded-aircraft coverage claim.
The [saved numerical diagnosis](NONLINEAR_DIAGNOSIS.md) identifies the specific
stopping check that failed without refitting the case.
The [eight-point timing probe](TIMING_PROBE_RESULT.md) shows that changing
timing alone follows the local calculation, even when packet assignments
change. Its wrapper ended with a recorded technical failure; the saved values
are audited separately. The coupled calibration/timing step remains unresolved.

A [finite independent-seed check](INDEPENDENT_SEEDS_RESULT.md) completed the
24-condition matrix on each of two new noise realizations. All 48 cases passed
the predeclared numerical and withheld-position gate. Every tested coordinate
fell inside its bound, but two draws per condition do not establish 95%
coverage. The original 23/24 result remains unchanged. The completed study
needs no recovery. For an interrupted study with unfinished tasks, the
qualified recovery command checks frozen evidence before using a separate,
finite technical allowance:

```sh
PYTHONPATH=analysis /home/sweisman/venv/bin/python -m lll.bounded_independent_recovery
```

Run it from the repository root. It does nothing while the original worker
owns the study, and it never retries a sealed result.

The adapter accepts the complete saved trajectory tangent and all calibration
columns, conditions the fixed error law on earlier receiver residuals, and
produces a separate interval for each later coordinate. It has no interface
for later receiver positions. It labels every result as an unqualified
nonlinear-aircraft diagnostic.

[Control plan](PLAN.md) · [Nonlinear technical result](NONLINEAR_RESULT.md) ·
[Independent-seed result](INDEPENDENT_SEEDS_RESULT.md) ·
[Prediction-error roadmap](../PREDICTION_ERROR_LAW_PLAN.md).
