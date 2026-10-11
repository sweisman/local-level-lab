# SPDX-License-Identifier: AGPL-3.0-or-later
"""Audit saved solver diagnostics without integration, fitting or status changes."""
import math

from . import ilvis0_saved_audit as saved

VERSION='ilvis0-saved-solver-diagnosis-v1'
# Replay the already published stable-stop diagnostic; do not tune its tolerances.
POLICY=dict(stationarity=1e-4,relative_cost_change=1e-8,
    relative_residual_step=1e-6,stable_callbacks=3,bound_projection=1e-6)


def finite(value,nonnegative=False):
    if (isinstance(value,bool) or not isinstance(value,(float,int)) or
        not math.isfinite(value) or nonnegative and value<0):
        raise ValueError('invalid saved numerical diagnostic')
    return value


def history_summary(history,evaluations):
    streak=0; first=None; previous=0
    for row in history:
        n=row['evaluations']
        if not isinstance(n,int) or isinstance(n,bool) or not previous<=n<=evaluations:
            raise ValueError('invalid saved callback order or allowance')
        previous=n; finite(row['cost'],True)
        stationarity=finite(row['stationarity'],True)
        cost=row['relative_cost_change']; step=row['relative_residual_step']
        for value in (cost,step):
            if value is not None: finite(value,True)
        stable=(cost is not None and step is not None and stationarity<=POLICY['stationarity']
            and cost<=POLICY['relative_cost_change'] and step<=POLICY['relative_residual_step'])
        streak=streak+1 if stable else 0
        if first is None and streak>=POLICY['stable_callbacks']: first=n
    return dict(recorded_callbacks=len(history),terminal_stable_callbacks=streak,
        first_three_stable_evaluation=first,last_callback_evaluation=previous if history else None,
        last_callback_cost=history[-1]['cost'] if history else None,
        last_relative_cost_change=history[-1]['relative_cost_change'] if history else None,
        last_relative_residual_step=history[-1]['relative_residual_step'] if history else None)


def parameter_diagnostics(fit):
    names=fit['active_parameters']; n=len(names)
    if not n or len(set(names))!=n: raise ValueError('invalid saved parameter names')
    keys=('normalized_parameters','gradient','projected_gradient','scaled_projected_gradient')
    if any(len(fit[k])!=n for k in keys): raise ValueError('invalid saved gradient dimensions')
    rows=[]
    for name,u,g,p,s in zip(names,*(fit[k] for k in keys)):
        for value in (u,g,p,s): finite(value)
        if abs(u)>1+1e-12: raise ValueError('saved point outside box')
        blocked=(u<=-1+POLICY['bound_projection'] and g>0 or
                 u>=1-POLICY['bound_projection'] and g<0)
        expected=0. if blocked else g
        if not math.isclose(p,expected,rel_tol=1e-10,abs_tol=1e-15):
            raise ValueError('saved projected gradient disagrees with box')
        if (p==0 and s!=0) or p*s<0: raise ValueError('invalid scaled gradient sign')
        rows.append(dict(parameter=name,normalized_value=u,
            boundary='lower' if u<=-.999 else 'upper' if u>=.999 else 'interior',
            raw_gradient=g,projected_gradient=p,scaled_projected_gradient=s,
            bound_blocks_descent=blocked))
    actual={r['parameter'] for r in rows if r['boundary']!='interior'}
    if set(fit['active_bounds'])!=actual or len(fit['active_bounds'])!=len(actual):
        raise ValueError('saved bounds disagree with point')
    maximum=max(abs(r['scaled_projected_gradient']) for r in rows)
    if not math.isclose(maximum,finite(fit['exact_projected_gradient_relative'],True),
                        rel_tol=1e-10,abs_tol=1e-15):
        raise ValueError('saved stationarity disagrees with gradient')
    singular=fit['singular_values']; vectors=fit['right_singular_vectors']
    if len(singular)!=n or len(vectors)!=n or any(len(v)!=n for v in vectors):
        raise ValueError('invalid saved singular dimensions')
    for value in singular: finite(value,True)
    if any(a<b for a,b in zip(singular,singular[1:])): raise ValueError('singular values not ordered')
    for i,v in enumerate(vectors):
        for value in v: finite(value)
        for j in range(i+1):
            if not math.isclose(sum(a*b for a,b in zip(v,vectors[j])),float(i==j),abs_tol=1e-6):
                raise ValueError('right singular vectors not orthonormal')
    modes=[]
    for rank,index in enumerate(range(n-1,max(-1,n-4),-1),1):
        v=vectors[index]
        def feasible(sign):
            return all(not (u<=-1+POLICY['bound_projection'] and sign*x<-1e-8 or
                            u>=1-POLICY['bound_projection'] and sign*x>1e-8)
                       for u,x in zip(fit['normalized_parameters'],v))
        for name,loading in zip(names,v):
            modes.append(dict(weak_rank=rank,singular_value=singular[index],parameter=name,
                loading=loading,positive_direction_feasible=feasible(1),negative_direction_feasible=feasible(-1)))
    return rows,modes


def inspect_fit(fit,baseline,case_id):
    parameters,modes=parameter_diagnostics(fit)
    history=history_summary(fit['accepted_step_history'],fit['evaluations'])
    tolerance=finite(fit['stationarity_tolerance'],True)
    if tolerance<=0: raise ValueError('invalid stationarity tolerance')
    before=finite(baseline['exact_projected_gradient_relative'],True)
    before_tolerance=finite(baseline.get('stationarity_tolerance',1e-4),True)
    if before_tolerance<=0: raise ValueError('invalid baseline tolerance')
    cost=finite(fit['residual_sum_squares'],True)
    before_cost=finite(baseline['residual_sum_squares'],True)
    singular=fit['singular_values']
    return dict(case_id=case_id,model=fit['model'],status=saved.fit_status(fit),
        baseline_status=saved.fit_status(baseline),evaluations=fit['evaluations'],
        training_cost=cost,baseline_training_cost=before_cost,
        relative_objective_change=(cost-before_cost)/max(before_cost,1.),
        stationarity_ratio=fit['exact_projected_gradient_relative']/tolerance,
        baseline_stationarity_ratio=before/before_tolerance,
        fresh_stationarity_passed=fit['exact_projected_gradient_relative']<=tolerance,
        scipy_success=bool(fit['solver_reported_success']),
        parameters_at_limits=sum(r['boundary']!='interior' for r in parameters),
        jacobian_condition_ratio=singular[0]/singular[-1] if singular[-1] else None,
        last_callback_matches_final_cost=history['last_callback_cost'] is not None and
            math.isclose(history['last_callback_cost'],cost,rel_tol=1e-12,abs_tol=1e-12),
        stopping_message=fit['message'],**history)
