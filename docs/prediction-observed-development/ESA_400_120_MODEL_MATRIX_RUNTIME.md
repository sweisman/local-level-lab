# ESA 400/120 model matrix: execution record

The [frozen plan](ESA_400_120_MODEL_MATRIX_PLAN.md) fixed 24 fits on one
previously opened development recording. Four one-thread workers closed all
24 tasks in 10,357 seconds. Twenty passed the numerical check; four
zero-removal flat-disc fits did not converge. There were no technical errors.
The original study is terminal because its all-task gate did not pass.

All 24 starts were charged before execution: 16.8 million native calls and
1.08 trillion packet visits at their frozen ceilings. No completed result was
restarted, and the separate reboot-recovery allowance was not used. The
training inputs contained only the first 400 receiver positions; the later
120 positions were opened by the saved-only auditor after the fits closed.

The [result](ESA_400_120_MODEL_MATRIX_RESULT.md) has two complete matched
settings, both with profiled upstream removal. In both, the specified-field
globe has the lowest later-position error and passes the stated physical
screen. The two zero-removal settings remain unresolved because the flat
candidate did not pass numerical stopping. This is one development flight,
with a horizon selected after earlier work on that flight. It does not
calibrate aircraft uncertainty or establish a scientific detection. The
seven reserved ESA flight groups remain unopened.
