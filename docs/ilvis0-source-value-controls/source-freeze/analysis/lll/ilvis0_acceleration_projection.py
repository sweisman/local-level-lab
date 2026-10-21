# SPDX-License-Identifier: AGPL-3.0-or-later
"""Training-only exact support bounds for the combined reference acceleration.

These certify a supplied affine relaxation, not real-world error coverage. All
51 physical/shared coordinates remain in every support calculation.
"""
from dataclasses import dataclass
from fractions import Fraction as F
import hashlib
import json
import math


@dataclass
class Allowance:
    maximum_proposals: int
    maximum_supports: int
    persist: object
    proposals: int = 0
    supports: int = 0

    def __post_init__(self):
        if (type(self.maximum_proposals) is not int or self.maximum_proposals<0
                or type(self.maximum_supports) is not int or self.maximum_supports<0):
            raise ValueError('finite nonnegative integer allowances required')

    def reserve(self,proposals,supports):
        if (type(proposals) is not int or type(supports) is not int or min(proposals,supports)<0
                or self.proposals+proposals>self.maximum_proposals
                or self.supports+supports>self.maximum_supports):
            raise ValueError('projection allowance exhausted')
        self.persist(dict(lp_proposals=self.proposals+proposals,exact_supports=self.supports+supports))
        self.proposals+=proposals;self.supports+=supports


def _validate(training,reference,lower,upper):
    region=training['region'];acc=reference['acceleration'];parent=reference['parent']
    if (region['parameter_count']!=51 or len(region['center'])!=51
            or region['future_truth_used'] or region['binding']!=reference['binding']
            or region['source_id']!=parent['source_id']
            or acc['reference_binding']!=parent['binding']
            or acc['version']!='ilvis0-common-reference-acceleration-component-v1'):
        raise ValueError('complete source-bound training region required')
    if (len(lower)!=51 or len(upper)!=51 or len(region['lower'])!=51 or len(region['upper'])!=51
            or any(not a<=b<=c<=d for a,b,c,d in zip(region['lower'],lower,upper,region['upper']))
            or len(acc['center'])!=3 or len(acc['jacobian'])!=3
            or any(len(row)!=27 for row in acc['jacobian']) or len(acc['caps'])!=9
            or any(v<0 for v in acc['caps']) or acc['change']<0):
        raise ValueError('full ordered domain and signed acceleration coefficients required')
    values=lower+upper+region['center']+acc['center']+acc['caps']+[acc['change']]
    values += [v for row in acc['jacobian'] for v in row]
    if any(not math.isfinite(v) for v in values):raise ValueError('finite acceleration inputs required')
    return region,acc


def project(training,reference,lower,upper,*,reserve):
    from lll.ilvis0_affine_support import propose
    from lll.ilvis0_saved_prediction_audit import support,endpoint
    from lll.ilvis0_exact_scale import sqrt_upper
    region,acc=_validate(training,reference,lower,upper)
    design=region['inequality_design'];bound=region['inequality_upper'];axes=[]
    # No truth, future observations, or fitted future outcome enters this API.
    inputs=dict(training=training,reference=reference,lower=lower,upper=upper)
    binding=hashlib.sha256(json.dumps(inputs,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
    for i in range(3):
        objective=list(acc['jacobian'][i])+[0.]*24
        objective[39+i]=acc['caps'][6+i]
        shift=F(acc['center'][i])-sum((F(j)*F(z) for j,z in zip(objective[:27],region['center'][:27])),F(0))
        certificates=[]
        for sign in (1,-1):
            signed=[sign*v for v in objective]
            # Two exact checks inside propose (dual and full-box fallback),
            # followed by the independent standard-library verification below.
            reserve(1,3)
            certificate=propose(lower,upper,design,bound,signed)
            multipliers=[float(v) for v in certificate['multipliers']]
            verified=support(lower,upper,design,bound,signed,multipliers)
            if verified!=certificate['exact_upper']:raise ValueError('independent acceleration support disagrees')
            certificates.append(dict(sign=sign,exact_upper=str(verified),multipliers=multipliers,
                proposal_used=certificate['proposal_used']))
        low=shift-F(certificates[1]['exact_upper']);high=shift+F(certificates[0]['exact_upper'])
        if low>high:raise ValueError('training relaxation is contradictory')
        left=endpoint(low,False);right=endpoint(high,True)
        change=endpoint(max(abs(F(left)-F(acc['center'][i])),abs(F(right)-F(acc['center'][i]))),True)
        axes.append(dict(axis=i,objective=objective,shift=str(shift),certificates=certificates,
            exact_lower=str(low),exact_upper=str(high),lower=left,upper=right,change=change))
    radius=sqrt_upper(sum((F(row['change'])**2 for row in axes),F(0)))
    old=acc['change']
    return dict(version='ilvis0-training-acceleration-projection-v1',input_binding=binding,
        region_binding=region['binding'],acceleration_binding=acc['binding'],source_id=region['source_id'],
        parameter_count=51,axes=axes,norm_change=radius,source_norm_change=old,
        radius_ratio=radius/old if old else (0. if not radius else None),
        twofold_radius_reduction=F(radius)*2<=F(old),future_observations_used=False,
        known_anchor_used_for_bounds=False,prediction_method_qualified=False,
        observational_coverage_qualified=False,scientific_decision='abstain')


def evaluate(task,context):
    from lll.ilvis0_sharded_native import read
    from lll.ilvis0_control_shards import _check_continue
    from lll.ilvis0_feasible_witness import Region
    bundle=read(context.input_path());payload=task['payload']
    if payload['maximum_proposals']!=6 or payload['maximum_exact_supports']!=18:
        raise ValueError('six proposals and eighteen exact support reservations required')
    def persist(record):
        _check_continue(context.root,context.manifest)
        context.save(f"reservation-{record['lp_proposals']:02d}.json",record)
    allowance=Allowance(6,18,persist)
    result=project(**bundle,reserve=allowance.reserve)
    context.save('projection.json',result)
    # The separate anchor file is not even opened until the bounds are saved.
    point=read(context.input_path(payload['anchor_key']))['point']
    region=bundle['training']['region']
    slacks=Region(bundle['lower'],bundle['upper'],region['inequality_design'],region['inequality_upper']).slacks(point)
    feasible=max(slacks)<=0
    if len(point)!=51:raise ValueError('complete known anchor required')
    values=[F(row['shift'])+sum((F(a)*F(x) for a,x in zip(row['objective'],point)),F(0)) for row in result['axes']]
    contained=all(F(row['lower'])<=value<=F(row['upper']) for row,value in zip(result['axes'],values))
    context.save('anchor-check.json',dict(feasible=feasible,contained=contained,
        exact_acceleration=[str(v) for v in values],maximum_exact_slack=str(max(slacks))))
    return dict(result,identity=task['identity'],model=payload['model'],profile=payload['profile'],
        passed=feasible and contained,anchor_contained=contained,anchor_feasible=feasible,
        lp_proposals_reserved=allowance.proposals,exact_supports_reserved=allowance.supports,
        original_reads=0,native_evaluations=0,optimizer_starts=0)
