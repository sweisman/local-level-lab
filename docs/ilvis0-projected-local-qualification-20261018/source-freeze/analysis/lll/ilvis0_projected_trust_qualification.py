# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite generated-motion scope and paired-start acceptance; never archive decisions."""
import itertools
import math


def tasks():
    result=[]
    for model,clock,axes,start in itertools.product(('sphere_rotating','sphere_still','flat_still'),
            ('nominal','variable'),(('latitude','longitude'),('height',)),('zero','opposed')):
        label='horizontal' if len(axes)==2 else 'height'
        result.append(dict(identity=f'{model}-{clock}-{label}-{start}',model=model,clock=clock,axes=list(axes),start=start))
    return result


def assess_fit(row):
    import numpy as np
    try:
        fit=row['fit'];cost=float(fit['residual_sum_squares']);truth=float(row['truth_cost'])
        error=np.asarray(row['prediction_error_m'],float);axes=tuple(row['axes'])
        if axes not in (('latitude','longitude'),('height',)) or error.ndim!=2 or error.shape[1]!=3 or len(error)<2:
            return False
        columns=[('latitude','longitude','height').index(a) for a in axes]
        maximum=float(np.max(abs(error[:,columns])))
        return bool(fit['converged'] and np.all(np.isfinite(error)) and math.isfinite(cost+truth)
            and cost>=0 and truth>=0 and maximum<.002 and cost<=truth+.01)
    except (KeyError,TypeError,ValueError):return False


def compare_pair(a,b):
    import numpy as np
    if (any(a.get(k)!=b.get(k) for k in ('model','clock','axes'))
            or {a.get('start'),b.get('start')}!={'zero','opposed'} or not assess_fit(a) or not assess_fit(b)):
        return dict(passed=False,reason='missing_or_unqualified_matching_pair')
    ca=float(a['fit']['residual_sum_squares']);cb=float(b['fit']['residual_sum_squares'])
    ea=np.asarray(a['prediction_error_m']);eb=np.asarray(b['prediction_error_m'])
    if ea.shape!=eb.shape:return dict(passed=False,reason='receiver_layout_mismatch')
    columns=[('latitude','longitude','height').index(v) for v in a['axes']]
    delta=(ea-eb)[:,columns]
    rms=np.sqrt(np.mean(delta**2,axis=0));maximum=np.max(abs(delta),axis=0)
    relative=abs(ca-cb)/max(ca,cb,1.)
    passed=relative<=1e-8 and np.all(rms<=.001) and np.all(maximum<=.01)
    return dict(passed=bool(passed),relative_cost_difference=relative,
        retained_prediction_rms_m=rms.tolist(),retained_prediction_maximum_m=maximum.tolist(),
        parameters_required_to_agree=False)
