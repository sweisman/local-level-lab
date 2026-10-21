# SPDX-License-Identifier: AGPL-3.0-or-later
"""Full 42-coordinate saved-polytope diagnosis; exact dual bounds, no integration."""
from fractions import Fraction as F
import math

import numpy as np
from lll import ilvis0_affine_support as support


def evaluate(task,context):
    import json
    case=json.loads(context.input_path().read_text());result=case['result'];training=case['training']['region'];future=case['future']
    if result['identity']!=task['identity'] or training['parameter_count']!=42:raise ValueError('complete saved joint identity required')
    calls=0
    def before():
        nonlocal calls
        from lll.ilvis0_control_shards import _check_continue
        _check_continue(context.root,context.manifest)
        if calls>=84:raise ValueError('frozen coordinate proposal allowance exhausted')
        calls+=1;context.save(f'proposal-{calls:02d}.json',dict(ordinal=calls,maximum_exact_certificates=2,maximum_seconds=1.))
    parameters=project(future['lower'],future['upper'],training['inequality_design'],training['inequality_upper'],before_proposal=before)
    retained=True
    if result['truth_in_sector']:
        truth=np.r_[case['physical_truth'],result['known_shared_error']]
        if truth.shape!=(42,):raise ValueError('complete known physical/common control vector required')
        retained=all(F(float(p['lower']))<=F(float(value))<=F(float(p['upper'])) for p,value in zip(parameters,truth,strict=True))
    def plain(value):
        if isinstance(value,np.ndarray):return value.tolist()
        if isinstance(value,np.generic):return value.item()
        if isinstance(value,dict):return {k:plain(v) for k,v in value.items()}
        if isinstance(value,list):return [plain(v) for v in value]
        return value
    return plain(dict(passed=bool(retained),identity=task['identity'],model=result['task']['model'],profile=result['task']['profile'],
        sector=result['task']['sector'],parameters=parameters,parameter_count=42,lp_proposals=calls,exact_certificate_ceiling=2*calls,
        known_truth_checked=result['truth_in_sector'],known_truth_retained=retained,
        native_evaluations=0,original_reads=0,optimizer_starts=0,observational_coverage_qualified=False,scientific_decision='abstain'))


def project(lower,upper,design,bound,*,before_proposal):
    lo=np.asarray(lower,float);hi=np.asarray(upper,float)
    if lo.shape!=(42,) or hi.shape!=lo.shape:raise ValueError('all 42 physical and shared coordinates required')
    rows=[]
    for axis in range(42):
        objective=np.zeros(42);objective[axis]=1.
        before_proposal();high=support.propose(lo,hi,design,bound,objective)
        before_proposal();low=support.propose(lo,hi,design,bound,-objective)
        left=max(float(lo[axis]),-low['upper']);right=min(float(hi[axis]),high['upper'])
        if left>right:raise ValueError('contradictory exact coordinate support requires diagnosis')
        rows.append(dict(parameter_index=axis,previous_lower=float(lo[axis]),previous_upper=float(hi[axis]),
            lower=left,upper=right,upper_certificate=str(high['exact_upper']),negated_lower_certificate=str(low['exact_upper']),
            upper_multipliers=high['multipliers'],lower_multipliers=low['multipliers'],
            upper_proposal_used=high['proposal_used'],lower_proposal_used=low['proposal_used'],
            width_ratio=(right-left)/(hi[axis]-lo[axis]) if hi[axis]>lo[axis] else 1.,
            narrowed=bool(right-left<(hi[axis]-lo[axis])*(1.-1e-6))))
    return rows

