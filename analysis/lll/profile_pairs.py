# SPDX-License-Identifier: AGPL-3.0-or-later
"""Experimental nonlinear pair-line profiles independent of the global science rank."""
import numpy as np
from scipy.optimize import least_squares
from scipy.stats import chi2

from . import models
from .policy import MODEL_PAIRS
from .inference_policy import INFERENCE_POLICY

PROFILE_METHOD = 'pair-line-profile-1'


def solve_pair(problem, comparison, *, y=None, endpoint=None, start=None, penalty=None):
    a, b = MODEL_PAIRS[comparison]
    base = np.asarray(models.EXPECTED_K[b], float)
    direction = np.asarray(models.EXPECTED_K[a], float)-base
    y = problem.y if y is None else y
    P = problem.penalty() if penalty is None else penalty
    offset = np.zeros(problem.npar); offset[:3] = base
    if endpoint is not None: offset[:3] += endpoint*direction
    T = np.zeros((problem.npar, problem.npar-3+int(endpoint is None)))
    first = int(endpoint is None)
    if first: T[:3,0] = direction
    T[3:,first:] = np.eye(problem.npar-3)
    initial = np.zeros(T.shape[1])
    if start is not None:
        if first: initial[0] = np.dot(start['z'][:3]-base,direction)/np.dot(direction,direction)
        initial[first:] = start['z'][3:]
    def fun(x):
        z = offset+T @ x
        return problem.objective_residual(z,y,P)
    def jac(x):
        return problem.objective_jacobian(offset+T@x,P)@T
    lo,hi=problem.bounds()
    lower=np.r_[[-np.inf] if first else [],lo[3:]]
    upper=np.r_[[np.inf] if first else [],hi[3:]]
    initial=np.clip(initial,lower,upper)
    opt = least_squares(fun, initial, jac=jac, x_scale='jac', max_nfev=problem.settings['max_nfev'],
                        ftol=1e-10, xtol=1e-10, gtol=1e-8,bounds=(lower,upper))
    z = offset+T @ opt.x
    A = jac(opt.x)
    inverse = np.linalg.pinv(A)
    return dict(z=z, pred=problem.prediction(z), objective=float(opt.fun @ opt.fun),
        success=bool(opt.success), estimate=float(opt.x[0]) if first else float(endpoint),
        sd=float(np.linalg.norm(inverse[0])) if first else None)


def profile_evidence(problem, design, *, n_boot=0, seed=0, block=15, sampling='moving'):
    from .fit import bootstrap_order, _autocorr_scale
    pairs = {}
    for name, (a,b) in MODEL_PAIRS.items():
        reasons = []
        information = design.get('untruncated_contrasts',{}).get(name,{})
        if not information.get('estimable'): reasons.append('pair contrast not identified')
        free = solve_pair(problem,name)
        endpoints = {a: solve_pair(problem,name,endpoint=1.,start=free),
                     b: solve_pair(problem,name,endpoint=0.,start=free)}
        best = min(endpoints.values(), key=lambda v:v['objective'])
        if free['objective'] > best['objective']+1e-6: free = solve_pair(problem,name,start=best)
        converged = free['success'] and all(v['success'] for v in endpoints.values())
        converged &= free['objective'] <= best['objective']+1e-6
        if not converged: reasons.append('pair profile did not converge or nest')
        if problem.wind_tas is not None and any(problem.wind_tas.boundary(v['z'][problem.p:problem.p+problem.nc])['near_boundary']
                for v in [free,*endpoints.values()]):
            reasons.append('physical wind/TAS fit near parameter boundary')
        residual = problem.y-free['pred']
        scale,_ = _autocorr_scale(residual*np.sqrt(problem.w),problem.idx,problem.bins)
        statistics = {m:max(0.,v['objective']-free['objective'])*scale for m,v in endpoints.items()}
        rng = np.random.default_rng(np.random.SeedSequence([seed,list(MODEL_PAIRS).index(name)]))
        standardized = (residual*np.sqrt(problem.w)).reshape(len(problem.bins['t']),-1)
        standardized -= standardized.mean(axis=0)
        estimates, null_counts, failures = [], {a:0,b:0}, []
        attempted = n_boot if len(standardized) >= 2*block else 0
        for i in range(attempted):
            for model, reference in [(None,free),*endpoints.items()]:
                order = bootstrap_order(rng,problem.bins,block,sampling)
                y = reference['pred']+standardized[order].ravel()/np.sqrt(problem.w)
                fit = solve_pair(problem,name,y=y,start=reference)
                null = None if model is None else solve_pair(problem,name,y=y,endpoint=float(model==a),start=fit)
                if not fit['success'] or (null is not None and (not null['success'] or fit['objective']>null['objective']+1e-6)):
                    failures.append(dict(replicate=i,model=model)); continue
                if model is None: estimates.append(fit['estimate'])
                else: null_counts[model]+=1
        valid_boot = attempted >=20 and len(estimates)>=np.ceil(.95*attempted) and all(v>=np.ceil(.95*attempted) for v in null_counts.values())
        if n_boot and not valid_boot: reasons.append('inadequate pair bootstrap convergence')
        direction = np.asarray(models.EXPECTED_K[a])-np.asarray(models.EXPECTED_K[b])
        floors = np.array([INFERENCE_POLICY['k_sys_floor'][m] for m in ('k_rot_sphere','k_curv','k_disc')])
        floor = np.linalg.norm(direction*floors)/np.dot(direction,direction)
        sd = float(np.sqrt(max(free['sd']/np.sqrt(scale), np.std(estimates,ddof=1) if len(estimates)>1 else 0.)**2+floor**2))
        shifts = {}
        keys = ['bias']+(['bias_drift'] if problem.dynamic_bias else [])+(['crab','rate'] if problem.nc else [])+(['forward'] if problem.forward else [])
        if problem.wind_tas is not None: keys+=['airspeed','airspeed_rate']
        if problem.temp_ref is not None: keys.append('temperature')
        for key in keys:
            widened = solve_pair(problem,name,start=free,penalty=problem.penalty(**{key:3.}))
            shifts[key] = (widened['estimate']-free['estimate'])/max(sd,1e-30)
            if not widened['success']: reasons.append('pair prior refit did not converge')
        if any(not np.isfinite(v) or abs(v)>1 for v in shifts.values()): reasons.append('pair prior dominated')
        pairs[name] = dict(method=PROFILE_METHOD, coordinate='first model=1, second model=0',
            estimate=free['estimate'],sd=sd,statistics=statistics,
            p_diagnostic={m:float(chi2.sf(v,1)) for m,v in statistics.items()},
            converged=bool(converged), eligible=not reasons,exclusions=list(dict.fromkeys(reasons)),
            design_information=information, prior_shift_sigma=shifts,
            autocorrelation_scale=float(scale),
            bootstrap=dict(requested=n_boot,attempted=attempted,replicates=len(estimates),null_replicates=null_counts,
                           failures=failures,bootstrap_valid=bool(valid_boot)),
            effective_rank=1, objective=free['objective'], endpoint_objectives={m:v['objective'] for m,v in endpoints.items()})
    return pairs
