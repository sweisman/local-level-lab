# SPDX-License-Identifier: AGPL-3.0-or-later
"""Research-only local stop candidate: reject real descent, preserve position."""

VERSION = 'one-sided-observable-stability-v1'
FRACTIONS = (.5,-.5,.25,-.25,.125,-.125)


def verify(point,residual,jacobian,evaluate,physical_step):
    import numpy as np
    from .ilvis0_solver_position import POLICY as POSITION, verify_stability
    from .ilvis0_solver_refinement import POLICY as STOPPING, projected_stationarity

    u = np.asarray(point,float)
    r = np.asarray(residual,float)
    j = np.asarray(jacobian,float)
    if (u.ndim != 1 or not len(u) or np.any(abs(u)>1)
            or r.ndim != 1 or not len(r) or j.shape != (len(r),len(u))
            or not all(np.all(np.isfinite(v)) for v in (u,r,j))
            or not callable(evaluate) or not callable(physical_step)):
        raise ValueError('complete feasible point, residual and tangent required')
    stationarity = projected_stationarity(u,r,j)[0]
    if stationarity > STOPPING['stationarity_tolerance']:
        return dict(version=VERSION,passed=False,reason='not_stationary',
                    original_probe=dict(passed=False,reason='not_stationary'),
                    initial_stationarity=stationarity,evaluations=0,scientific_decision='abstain')
    captured = []
    def original_fresh(point,fresh=False):
        if not fresh or captured:
            raise ValueError('one original full-correction fresh evaluation required')
        value = evaluate(point,fresh=True)
        captured.append((np.asarray(point,float).copy(),
                         np.asarray(value[0],float).copy()))
        return value
    original = verify_stability(u,r,j,original_fresh,physical_step)
    if not captured:
        return dict(version=VERSION,passed=False,reason=original['reason'],
                    original_probe=original,initial_stationarity=stationarity,
                    evaluations=0,scientific_decision='abstain')
    repeated,repeated_j,_ = evaluate(u.copy(),fresh=True)
    repeated,repeated_j = np.asarray(repeated,float),np.asarray(repeated_j,float)
    repeat_equal = bool(np.array_equal(repeated,r) and np.array_equal(repeated_j,j))
    if not repeat_equal:
        return dict(version=VERSION,passed=False,reason='baseline_not_repeatable',
                    original_probe=original,initial_stationarity=stationarity,
                    baseline_repeat_equal=False,evaluations=2,scientific_decision='abstain')
    baseline_cost = float(r@r)
    full_point,full_residual = captured[0]
    correction = full_point-u
    trials=[]
    def record(fraction,trial_point,trial_residual):
        trial_residual = np.asarray(trial_residual,float)
        difference = np.asarray(physical_step(trial_residual-r),float)
        if (trial_residual.shape != r.shape or difference.ndim != 2
                or difference.shape[1] != 3 or not len(difference)
                or not np.all(np.isfinite(trial_residual))
                or not np.all(np.isfinite(difference))):
            raise ValueError('complete finite fresh trial and physical difference required')
        cost = float(trial_residual@trial_residual)
        rms = np.sqrt(np.mean(difference*difference,axis=0))
        maximum = np.max(abs(difference),axis=0)
        row = dict(fraction=fraction,cost=cost,
            relative_reduction=(baseline_cost-cost)/max(baseline_cost,cost,1.),
            position_rms_neu_m=rms.tolist(),position_max_abs_neu_m=maximum.tolist(),
            feasible=bool(np.all(abs(trial_point)<=1)))
        trials.append(row)
    record(1.,full_point,full_residual)
    for fraction in FRACTIONS:
        trial = np.clip(u+fraction*correction,-1.,1.)
        trial_residual,_,_ = evaluate(trial,fresh=True)
        record(fraction,trial,trial_residual)
    position_stable = all(
        max(row['position_rms_neu_m'])<=POSITION['position_rms_tolerance_m']
        and max(row['position_max_abs_neu_m'])<=POSITION['position_max_tolerance_m']
        for row in trials)
    no_descent = all(row['relative_reduction']<=STOPPING['relative_cost_tolerance']
                     for row in trials)
    passed = bool(position_stable and no_descent)
    reason = ('one_sided_position_stability_verified' if passed else
              'physical_position_unstable' if not position_stable else
              'detectable_cost_decrease')
    return dict(version=VERSION,passed=passed,reason=reason,
        original_probe=original,initial_stationarity=stationarity,
        baseline_repeat_equal=True,baseline_cost=baseline_cost,
        position_stable=position_stable,no_detectable_descent=no_descent,
        cost_reduction_tolerance=STOPPING['relative_cost_tolerance'],
        trials=trials,evaluations=2+len(FRACTIONS),
        global_optimum_established=False,scientific_decision='abstain')
