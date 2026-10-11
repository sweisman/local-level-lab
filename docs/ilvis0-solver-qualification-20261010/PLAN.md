# Bounded solver qualification controls

This is a software qualification check, not an Earth-model campaign. It opens no NASA
originals, spends no observed-fit allowance and changes no frozen implementation.

Add `analysis/lll/ilvis0_solver_controls.py` and focused tests. Run at most **34 starts**:
six analytic optimization problems with three deterministic starts each, and eight
two-second IMU/GPS controls with two starts each. Every start has at most 200 actual
residual predictions or analytic tangent evaluations. No automatic retries or expansion.

Analytic cases cover interior and boundary optima, redundant and badly scaled directions,
nonlinear curvature, and coupled gyro gain/offset. Known objective values come from their
closed-form definitions, not a second run of the same optimizer.

IMU/GPS cases cover acceleration offset, orientation, gain and timing, plus stationary and
eastward constant-speed globe trajectories with and without background rotation. GPS
positions and inertial increments come from explicit analytic trajectories, never from
the prediction kernel. These controls test numerical recovery under known equations;
they do not measure archive instrument properties or calibrate a scientific decision.
They share the declared kinematic conventions and therefore cannot independently prove
that those conventions describe real flights.

Save objective agreement, numerical status, identifiable-parameter recovery, prediction
errors, boundary signs, actual evaluation counts and all failures. Preserve a separately
hashed source/environment record and report. Do not retune tolerances after seeing outcomes.
Qualification tolerances: analytic objective error ≤1e-7; expected prediction/parameter
tolerances are fixed by each control definition. Weak/nonunique parameter coordinates
are assessed through their predictions, without inventing unique parameter recovery.

Use at most two numerical threads. No observed timing refit is authorized by this plan.
Its proposed finite scope and runtime estimate will be prepared after these checks.
