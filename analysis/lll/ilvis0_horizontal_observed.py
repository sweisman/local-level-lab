# SPDX-License-Identifier: AGPL-3.0-or-later
"""Explicit observed-study selection and gates; no implicit fitting or input reads."""
import copy
import math

VERSION='ilvis0-horizontal-observed-v1'
CASES=('bias1_unsubtracted','bias1_profiled_removal')
MODELS=('sphere_rotating','sphere_still','flat_still')


def select(selection,inventory):
    groups={}
    for row in inventory:groups.setdefault(row['segment_id'],[]).append(row)
    expected={(c,m) for c in CASES for m in MODELS}
    candidates=[]
    for row in selection['selected']:
        segment=row['segment'];group=groups.get(segment['segment_id'],[])
        if (len(group)==6 and {(v['case_id'],v['model']) for v in group}==expected
                and all(v['status']=='ready' for v in group)):
            duration=float(segment['duration_s'])
            if not math.isfinite(duration) or duration<240:raise ValueError('complete frozen eligible interval required')
            candidates.append(row)
    chosen=[]
    for kind in (8,21):
        available=[r for r in candidates if r['segment']['imu_type']==kind]
        if not available:raise ValueError('complete artifacts required for each declared IMU configuration')
        chosen.append(min(available,key=lambda r:(r['segment']['duration_s'],r['filename'],r['segment']['start_s'],r['segment']['segment_id'])))
    return copy.deepcopy(chosen)


def plan(selected):
    if len(selected)!=2 or {r['segment']['imu_type'] for r in selected}!={8,21}:raise ValueError('two declared configurations required')
    tasks=[]
    for row in selected:
        sid=row['segment']['segment_id']
        for case in CASES:
            for model in MODELS:
                for role in ('primary','repeat'):
                    tasks.append(dict(identity='::'.join((sid,case,model,role)),segment_id=sid,case_id=case,
                        model=model,role=role,profile=case=='bias1_profiled_removal',axes=['latitude','longitude']))
    return dict(version=VERSION,tasks=tasks,maximum_starts=24,maximum_tangents_per_start=200,
        maximum_diagnostics_per_start=2,maximum_preflight_calls=12,maximum_native_evaluations=4860,
        numerical_threads=4,maximum_wall_s=28800,retries=0)


def reproduction(residual,jacobian,saved):
    import numpy as np
    r=np.asarray(residual,float);j=np.asarray(jacobian,float)
    old_r=np.asarray(saved['residual'],float);old_j=np.asarray(saved['jacobian'],float)
    if (r.ndim!=1 or j.ndim!=2 or j.shape[0]!=len(r) or r.shape!=old_r.shape or j.shape!=old_j.shape
            or any(not np.all(np.isfinite(v)) for v in (r,j,old_r,old_j))):
        raise ValueError('matched finite full residual and Jacobian systems required')
    cost=float(r@r);old_cost=float(old_r@old_r)
    dc=abs(cost-old_cost)/max(cost,old_cost,1.)
    dr=float(np.linalg.norm(r-old_r)/max(np.linalg.norm(r),np.linalg.norm(old_r),1.))
    dj=float(np.linalg.norm(j-old_j)/max(np.linalg.norm(j),np.linalg.norm(old_j),1.))
    return dict(passed=bool(dc<=1e-6 and dr<=1e-6 and dj<=1e-5),
                relative_cost_difference=dc,relative_residual_difference=dr,relative_jacobian_difference=dj,
                reproduced_cost=cost,reference_cost=old_cost,bit_identical=bool(np.array_equal(r,old_r) and np.array_equal(j,old_j)))


def repeat_check(a,b):
    import numpy as np
    if (any(a.get(k)!=b.get(k) for k in ('segment_id','model','case_id','axes'))
            or {a.get('role'),b.get('role')}!={'primary','repeat'}
            or not all(r.get('fit',{}).get('converged') is True for r in (a,b))):
        return dict(passed=False,reason='missing_or_unqualified_repeat')
    ca=float(a['fit']['residual_sum_squares']);cb=float(b['fit']['residual_sum_squares'])
    ea=np.asarray(a['prediction_error_m'],float);eb=np.asarray(b['prediction_error_m'],float)
    if (not math.isfinite(ca+cb) or min(ca,cb)<0 or ea.shape!=eb.shape or ea.ndim!=2
            or ea.shape[1]!=3 or len(ea)<2 or not np.all(np.isfinite(ea)) or not np.all(np.isfinite(eb))):
        raise ValueError('matched finite returned predictions required')
    delta=(ea-eb)[:,:2];rms=np.sqrt(np.mean(delta**2,axis=0));maximum=np.max(abs(delta),axis=0)
    difference=abs(ca-cb)/max(ca,cb,1.)
    passed=bool(difference<=1e-8 and np.all(rms<=.001) and np.all(maximum<=.01))
    return dict(passed=passed,relative_cost_difference=difference,retained_prediction_rms_m=rms.tolist(),
                retained_prediction_maximum_m=maximum.tolist(),parameters_required_to_agree=False)
