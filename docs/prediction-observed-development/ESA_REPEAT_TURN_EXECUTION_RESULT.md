# The 16 repeat-turn forecast tasks are frozen

The manifest binds four windows, both IMU error descriptions and both
fixed starts. It uses the [verified training-only files](ESA_REPEAT_TURN_MATERIAL_RESULT.md)
and the archived fit recipe. The task runner checks the training packet
prefix, reproduces the earlier Gaussian fit score within the full error
operator, and seals a converged conditional forecast for separate scoring.

Seven execution tests and six shared recovery tests passed under
source-bound qualification. The generated execution control checks the
full joint covariance and conditional mean against known error. The
input check rejects an extra receiver file before accessing any task
input. The recovery tests check that sealed tasks are skipped, interrupted
charges remain recorded, and changed inputs block reuse.

The frozen manifest has one thread on each of four workers, an eight-hour
original wall allowance and at most 200 evaluations per start. A separate
recovery allowance permits one retry per interrupted task, up to four
additional interruptions charged, with a four-hour wall allowance. These
are bounds on work, not scientific acceptance thresholds.

The local execution manifest SHA-256 is
`e79d1f7e516f7282298e03ca13291bbc5b02e42a8412eafdf740e2e1097e6f46`.
At preparation it had **0 of 16** completed results and zero native calls
charged. The separate outcome reader still needs a verified gate that
chooses primary starts from training costs before any later receiver
positions are decoded. The numerical forecast study remains pending.

[Plan and preparation commands](ESA_REPEAT_TURN_EXECUTION_PLAN.md) ·
[Execution qualification](esa-repeat-turn-execution-qualification.json) ·
[Execution tests](esa-repeat-turn-execution-tests.xml) ·
[Recovery qualification](esa-repeat-turn-recovery-qualification.json) ·
[Recovery tests](esa-repeat-turn-recovery-tests.xml)
