# SPDX-License-Identifier: AGPL-3.0-or-later
"""Independent known-generated controls for the complete interval source map."""
from fractions import Fraction as F


class Allowance:
    def __init__(self,limits,persist):
        if not limits or any(type(v)!=int or v<0 for v in limits.values()):raise ValueError('finite named allowance required')
        self.limits=dict(limits);self.counts=dict.fromkeys(limits,0);self.persist=persist

    def reserve(self,increase):
        if (not increase or any(k not in self.counts or type(v)!=int or v<1 for k,v in increase.items())):
            raise ValueError('positive named work reservation required')
        counts={k:v+increase.get(k,0) for k,v in self.counts.items()}
        if any(v>self.limits[k] for k,v in counts.items()):raise ValueError('control allowance exhausted')
        self.persist(dict(increase=increase,counts=counts));self.counts=counts


def analytic_jacobian(reference,point):
    """Separate explicit calculus using SciPy Frechet derivatives, not interval AD."""
    import numpy as np
    from scipy.linalg import expm,expm_frechet
    from lll.ilvis0_shared_reference_terms import _skew
    r=reference.parent;a=reference.acceleration;m=reference.transform
    x=np.asarray(point,float);p=r.limits*x;c=r.limits*r.center
    rotation=r.initial_r@expm(_skew(p[:3]));dr=np.zeros((3,3,27));dr0=np.zeros((3,3,27))
    for j in range(3):
        direction=np.zeros(3);direction[j]=r.limits[j]
        dr[:,:,j]=r.initial_r@expm_frechet(_skew(p[:3]),_skew(direction),compute_expm=False)
        dr0[:,:,j]=r.initial_r@expm_frechet(_skew(c[:3]),_skew(direction),compute_expm=False)
    clock=r.limits[25]*(x[25]-r.center[25]);dc=np.zeros(27);dc[25]=r.limits[25]
    velocity=np.zeros((3,27))
    for i in range(3):
        velocity[i,3+i]=r.limits[3+i]*clock
        velocity[i,25]=r.limits[3+i]*(x[3+i]-r.center[3+i])*r.limits[25]
    lever=np.einsum('ijk,j->ik',dr,p[21:24])-np.einsum('ijk,j->ik',dr0,r._lever_center)
    for j in range(3):lever[:,21+j]+=(rotation[:,j]-r._r_center[:,j])*r.limits[21+j]
    denominator=1+p[18:21];force=(a.raw_delta_v-p[12:15]*a.period)/denominator/a.period
    actual=rotation@force+np.array([0.,0.,a.gravity+p[24]])
    ja=np.einsum('ijk,j->ik',dr,force)
    for j in range(3):
        ja[:,12+j]=-rotation[:,j]*r.limits[12+j]/denominator[j]
        ja[:,18+j]=-rotation[:,j]*force[j]*r.limits[18+j]/denominator[j]
    ja[2,24]=r.limits[24]
    jm=dr/denominator[None,:,None]
    for j in range(3):jm[:,j,18+j]=-rotation[:,j]*r.limits[18+j]/denominator[j]**2
    square=.5*ja*clock**2+actual[:,None]*clock*dc[None,:]
    cross=ja*clock+(actual-a.center)[:,None]*dc[None,:]
    raw=np.r_[velocity,lever,square,cross,ja-a.jacobian,(jm-m.jacobian).reshape(9,27)]
    caps=np.r_[r.caps,a.caps,m.caps];result=np.zeros((24,27));nonzero=caps>0.
    result[nonzero]=raw[nonzero]/caps[nonzero,None]
    return result


def check_probe(bounds,cuts,point,actual,jacobian,*,derivative_tolerance):
    import math
    import numpy as np
    values=np.asarray(actual,float);jac=np.asarray(jacobian,float)
    if (len(bounds)!=24 or len(point)!=27 or values.shape!=(24,) or jac.shape!=(24,27)
            or not np.all(np.isfinite(values)) or not np.all(np.isfinite(jac))
            or not math.isfinite(derivative_tolerance) or derivative_tolerance<0.
            or len(cuts['design'])!=48 or any(len(row)!=51 for row in cuts['design'])):
        raise ValueError('complete source-map values, derivatives and inequalities required')
    value_gap=gradient_gap=0.
    for i,bound in enumerate(bounds):
        value_gap=max(value_gap,bound.value.lo-values[i],values[i]-bound.value.hi)
        for j,g in enumerate(bound.derivative):
            gradient_gap=max(gradient_gap,g.lo-derivative_tolerance-jac[i,j],jac[i,j]-g.hi-derivative_tolerance)
    x=list(map(F,point))+list(map(F,values));slacks=[]
    for row,right in zip(cuts['design'],cuts['upper'],strict=True):
        slacks.append(sum((F(a)*v for a,v in zip(row,x,strict=True)),F(0))-F(right))
    maximum=max(F(0),max(slacks))
    return dict(passed=value_gap<=0. and gradient_gap<=0. and maximum<=0,
        maximum_value_violation=float(value_gap),maximum_derivative_violation=float(gradient_gap),
        maximum_exact_coupling_violation=str(maximum),value_inequalities=48,
        derivative_inequalities=1296,coupled_inequalities=48,scalar_inequalities=1392)


def domain(family):
    import numpy as np
    if family=='sector':
        from lll.ilvis0_orientation_cover import sector
        box=sector(4)
        return {k:box[k] for k in ('lower','upper','center')}
    if family=='fixed':return dict(lower=np.full(27,.1),upper=np.full(27,.1),center=np.full(27,.1))
    lo=-np.ones(27);hi=np.ones(27);center=np.zeros(27)
    if family=='gain-boundary':lo[18]=hi[18]=center[18]=1.
    elif family!='full':raise ValueError('one predeclared physical domain required')
    return dict(lower=lo,upper=hi,center=center)


def evaluate(task,context):
    import gzip
    import json
    import numpy as np
    from lll.ilvis0_control_shards import _check_continue
    from lll.ilvis0_sharded_native import read,plain
    from lll.ilvis0_receipt_journal import durable_write
    from lll.ilvis0_transform_native import make_reference
    from lll.ilvis0_coupled_map import StaticMap
    from lll.ilvis0_interval_calibration import couple
    case=read(context.input_path());spec=task['payload'];family=spec['family']
    count=1 if family=='fixed' else 64
    limits=dict(setups=1,intervals=2,oracles=count,jacobians=count,checks=1392*count)
    if (spec['maximum_probes']!=count or spec['limits']!=limits
            or case['configuration']['model']!=spec['model'] or case['configuration']['profile']!=spec['profile']):
        raise ValueError('complete generated identity and fixed finite limits required')
    events=[]
    def persist(record):
        _check_continue(context.root,context.manifest)
        context.save(f'reservation-{len(events)+1:03d}.json',record);events.append(record)
    budget=Allowance(limits,persist);box=domain(family)
    budget.reserve(dict(setups=1))
    reference=make_reference(case['configuration'],case['theta'],case['dv'],case['dt'],**box)
    model=StaticMap(reference,expected_report=reference.report(),numerical_allowance=3e-10)
    budget.reserve(dict(intervals=1));bounds=model.bound(box['lower'],box['upper'])
    center=(box['lower']+box['upper'])/2
    budget.reserve(dict(intervals=1));origin=model.bound(center,center)
    cuts=couple(bounds,origin,box['lower'],box['upper'],center)
    context.save('source-map.json',dict(reference=reference.report(),map=model.report(),domain=plain(box)))
    context.save('bounds.json',dict(values=[[v.value.lo,v.value.hi] for v in bounds],
        derivatives=[[[d.lo,d.hi] for d in v.derivative] for v in bounds],
        center_values=[[v.value.lo,v.value.hi] for v in origin]))
    context.save('coupling.json',cuts)
    seed=[2026102025,spec['model'],int(spec['profile']),('full','sector','fixed','gain-boundary').index(family)]
    rng=np.random.default_rng(np.random.SeedSequence(seed))
    points=[center] if count==1 else [box['lower'],box['upper'],center]+[
        rng.uniform(box['lower'],box['upper']) for _ in range(count-3)]
    records=[]
    for point in points:
        budget.reserve(dict(oracles=1,jacobians=1,checks=1392))
        try:
            actual=reference.normalized_values_at(point);jac=analytic_jacobian(reference,point)
            checked=check_probe(bounds,cuts,point,actual,jac,derivative_tolerance=3e-8)
            records.append(dict(point=point,values=actual,analytic_jacobian=jac,**checked))
        except (ValueError,ArithmeticError) as error:
            records.append(dict(point=point,passed=False,reason=str(error)))
    artifact=context.directory/'probes.json.gz';artifact.parent.mkdir(parents=True,exist_ok=True)
    durable_write(artifact,gzip.compress(json.dumps(plain(records),sort_keys=True,separators=(',',':'),allow_nan=False).encode(),mtime=0))
    context.note_file(artifact)
    return dict(identity=task['identity'],passed=len(records)==count and all(r['passed'] for r in records),
        model=spec['model'],profile=spec['profile'],family=family,probes=count,seed=seed,
        work=budget.counts,checked_value_inequalities=sum(r.get('value_inequalities',0) for r in records),
        checked_derivative_inequalities=sum(r.get('derivative_inequalities',0) for r in records),
        checked_coupled_inequalities=sum(r.get('coupled_inequalities',0) for r in records),
        maximum_value_violation=max(r.get('maximum_value_violation',0.) for r in records),
        maximum_derivative_violation=max(r.get('maximum_derivative_violation',0.) for r in records),
        numerical_value_allowance=3e-10,derivative_comparison_tolerance=3e-8,
        whole_program_roundoff_qualified=False,original_reads=0,native_evaluations=0,optimizer_starts=0,
        observational_coverage_qualified=False,scientific_decision='abstain')
