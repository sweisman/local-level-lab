# SPDX-License-Identifier: AGPL-3.0-or-later
"""Adapt independent bounded optimizers to counted training fits."""

import numpy as np

from .independent_bounded_solver import solve
from .ilvis0_solver_position import physical_residual_step

VERSION='ilvis0-independent-scipy-trf-adapter-v1'


def fit_candidate(problem,model,*,start,maximum_evaluations=200,
                  physical_step=None,method='trf'):
    # fit_training wraps every native residual/tangent call in this Counted
    # proxy. The lower-level SciPy control's second reservation hook is a
    # no-op here because the proxy already charges each actual call.
    counter = 'tangent_calls' if hasattr(problem, 'tangent_calls') else 'calls'
    count = getattr(problem, counter, None)
    if (type(problem).__name__!='Counted' or type(count) is not int or count!=0
            or getattr(problem, 'value_calls', 0) != 0):
        raise ValueError('counted training adapter required before SciPy fit')
    if method not in ('trf', 'centered_lbfgsb'):
        raise ValueError('declared training solver required')
    transform=(physical_step if physical_step is not None else
               lambda delta:physical_residual_step(problem,delta))
    if not callable(transform):
        raise ValueError('physical residual conversion required')
    result=solve(problem,model,start=start,method=method,
                 maximum_calls=maximum_evaluations,
                 reserve=lambda **work:None,physical_step=transform)
    if getattr(problem, counter)!=result['native_calls_actual']:
        raise ValueError('counted native calls differ from SciPy record')
    point=np.asarray(result['point'],float)
    decoded=problem.bounds.decode(point)
    parameters={key:float(value) for key,value in decoded.items()}
    converged=bool(result['original_gate_passed'])
    version = VERSION if method == 'trf' else 'ilvis0-centered-lbfgsb-adapter-v1'
    return dict(version=version,model=model,optimizer_family='scipy_trf' if method == 'trf' else method,
        normalized_parameters=point.tolist(),parameters=parameters,
        active_parameters=list(problem.bounds.active),
        residual_sum_squares=result['cost'],
        initial_cost=result['initial_cost'],
        evaluations=result['native_calls_actual'],
        maximum_evaluations=maximum_evaluations,
        converged=converged,stopping_rule_verified=converged,
        stability_verified=result['original_stability_probe']['passed'],
        stability_probe=result['original_stability_probe'],
        exact_projected_gradient_relative=result['original_projected_stationarity'],
        scipy_success=result['scipy_success'],scipy_status=result['scipy_status'],
        scipy_message=result['scipy_message'],
        scipy_nfev=result['scipy_nfev'],scipy_njev=result['scipy_njev'],
        scipy_optimality=result['scipy_optimality'],
        evaluation_trace=result['evaluation_trace'],
        active_bounds=[name for name,u in zip(problem.bounds.active,point)
                       if abs(u)>=.999],
        scientific_eligible=False,scientific_decision='abstain',
        confidence_calibrated=False,parameter_identification_established=False)
