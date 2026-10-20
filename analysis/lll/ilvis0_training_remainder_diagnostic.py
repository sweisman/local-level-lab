# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite last-training-epoch bound diagnostic, with unchanged reference."""
from fractions import Fraction as F
import math


def compare(*,old_lower,old_upper,scale,old_center,new_center,old_design,new_design,
            remainder,noise,arithmetic):
    vectors=(old_lower,old_upper,scale,old_center,new_center,remainder)
    if (any(len(v)!=3 for v in vectors) or len(old_design)!=3 or len(new_design)!=3
            or not old_design[0] or any(len(r)!=len(old_design[0]) for r in old_design+new_design)):
        raise ValueError('complete matching three-axis expression required')
    values=[v for row in vectors for v in row]+[noise,arithmetic]+[v for row in old_design+new_design for v in row]
    if (any(not math.isfinite(v) for v in values) or any(v<=0 for v in scale)
            or any(v<0 for v in remainder+[noise,arithmetic])
            or any(a>=b for a,b in zip(old_lower,old_upper))):
        raise ValueError('finite positive scales/intervals and nonnegative allowances required')
    previous=[(F(b)-F(a))/2 for a,b in zip(old_lower,old_upper)]
    new=[F(r)*F(s)+F(noise)+F(arithmetic) for r,s in zip(remainder,scale)]
    error=max(abs(F(a)-F(b))*F(s) for a,b,s in zip(old_center,new_center,scale))
    equal=old_design==new_design
    return dict(passed=error<=F(1,1000000) and equal,maximum_center_difference_m=float(error),
        all_coefficients_unchanged=equal,old_half_width_m=list(map(float,previous)),
        new_half_width_m=list(map(float,new)),width_ratio=[float(a/b) for a,b in zip(new,previous)],
        observational_coverage_qualified=False,scientific_decision='abstain')


def evaluate(task,context):
    import numpy as np
    from lll.ilvis0_sharded_native import read,plain
    from lll import ilvis0_transform_native as native
    from lll.ilvis0_orientation_cover import sector
    bundle=read(context.input_path());spec=task['payload'];case=read(context.input_path(spec['case_key']))
    training=bundle['training'];future=bundle['future'];region=training['region']
    if (spec['sector']!=4 or spec['child']!=0 or region['parameter_count']!=78
            or len(case['dt'])!=1600 or spec['packets']!=1600):
        raise ValueError('fixed sector/child and original full generated input required')
    lo=future['lower'][:27];hi=future['upper'][:27];box=sector(4)
    if any(not a<=b<=c<=d for a,b,c,d in zip(box['lower'],lo,hi,box['upper'],strict=True)):
        raise ValueError('contained physical subdomain required')
    config={k:np.ascontiguousarray(v) if k in ('initial_c','initial_v','initial_r','limits') else v
        for k,v in case['configuration'].items()}
    context.save('reference-setup-reservation.json',dict(setups=1,maximum=1))
    reference=native.make_reference(config,case['theta'],case['dv'],case['dt'],
        lower=box['lower'],upper=box['upper'],center=box['center'])
    if reference.report()!=training['reference'] or reference.report()!=future['reference']:
        raise ValueError('original complete reference changed')
    context.charge(bound_calls=1,bound_steps=3200)
    report=native.enclose(config,case['theta'],case['dv'],case['dt'],time=training['times_s'][-1],
        lower=lo,upper=hi,reference=reference,maximum_seconds=120.)
    context.save('bound.json',plain(report.report()))
    augmented=report.design(np.asarray(training['jacobian'][-1]),reference).tolist()
    if any(len(r)!=51 for r in augmented):raise ValueError('all 51 expression columns required')
    answer=compare(old_lower=region['target_lower'][-3:],old_upper=region['target_upper'][-3:],
        scale=region['coordinate_scale'],old_center=training['nominal'][-1],new_center=report.center.tolist(),
        old_design=region['design'][-3:],new_design=augmented,remainder=report.unshared_remainder.tolist(),
        noise=.001,arithmetic=region['arithmetic_allowance'])
    return dict(answer,identity=task['identity'],model=spec['model'],profile=spec['profile'],sector=4,child=0,
        bound_calls=1,bound_steps=3200,reference_setups=1,native_evaluations=0,optimizer_starts=0,original_reads=0,
        parameter_count=78,original_expression_columns=51,training_constraints_replaced=False)
