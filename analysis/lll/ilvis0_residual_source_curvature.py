# SPDX-License-Identifier: AGPL-3.0-or-later
"""Derivative diagnostic after removing the known shared-source expression."""
from fractions import Fraction as F


def compare(maps,probe_jacobian,point,source,source_center,source_jacobian,center_source_jacobian,actual):
    import numpy as np
    m=np.asarray(maps,float);jp=np.asarray(probe_jacobian,float);p=np.asarray(point,float)
    g=np.asarray(source,float);g0=np.asarray(source_center,float)
    dg=np.asarray(source_jacobian,float);dg0=np.asarray(center_source_jacobian,float)
    try:
        truth=[[F(v) if isinstance(v,str) else F(float(v)) for v in row] for row in actual]
        values=np.array(truth,float)
    except (ValueError,TypeError,OverflowError):raise ValueError('finite saved changes required') from None
    if (m.ndim!=3 or m.shape[1:]!=(3,51) or jp.shape!=(len(m),3,27) or p.shape!=(27,)
            or g.shape!=(24,) or g0.shape!=(24,) or dg.shape!=(24,27) or dg0.shape!=(24,27)
            or values.shape!=(len(m),3) or len(m)<1
            or any(not np.all(np.isfinite(v)) for v in (m,jp,p,g,g0,dg,dg0,values))):
        raise ValueError('complete finite 27+24 source values, maps and derivatives required')
    p=list(map(F,map(float,p)));g=list(map(F,map(float,g)));g0=list(map(F,map(float,g0)))
    derivative_step=[sum(((F(float(a))+F(float(b)))*x for a,b,x in zip(row,base,p,strict=True)),F(0))
        for row,base in zip(dg,dg0,strict=True)]
    original=[];anchored=[];corrected=[];corrections=[];center_response=[]
    for epoch,(rows,derivatives) in enumerate(zip(m,jp,strict=True)):
        old=[];base=[];after=[];added=[];offset=[]
        for axis,(row,derivative) in enumerate(zip(rows,derivatives,strict=True)):
            row=list(map(F,map(float,row)));derivative=list(map(F,map(float,derivative)))
            physical=sum((a*x for a,x in zip(row[:27],p,strict=True)),F(0))
            shared=sum((a*x for a,x in zip(row[27:],g,strict=True)),F(0))
            at_center=sum((a*x for a,x in zip(row[27:],g0,strict=True)),F(0))
            derivative_change=sum(((a-b)*x for a,b,x in zip(derivative,row[:27],p,strict=True)),F(0))
            source_change=sum((a*x for a,x in zip(row[27:],derivative_step,strict=True)),F(0))
            correction=(derivative_change-source_change)/2
            error=truth[epoch][axis]-physical-shared
            old.append(float(error));base.append(float(error+at_center));after.append(float(error+at_center-correction))
            added.append(float(correction));offset.append(float(at_center))
        original.append(old);anchored.append(base);corrected.append(after);corrections.append(added);center_response.append(offset)
    anchored=np.array(anchored);corrected=np.array(corrected)
    return dict(physical_parameter_count=27,source_parameter_count=24,epochs=len(m),
        source_error_m=original,anchored_error_m=anchored.tolist(),corrected_error_m=corrected.tolist(),
        correction_m=corrections,source_center_response_m=center_response,
        rms_anchored_error_m=float(np.sqrt(np.mean(anchored**2))),
        rms_corrected_error_m=float(np.sqrt(np.mean(corrected**2))),
        maximum_anchored_error_m=float(np.max(abs(anchored))),maximum_corrected_error_m=float(np.max(abs(corrected))),
        conditioned_radii_transferred=False,numerical_coverage_qualified=False,coefficients_fitted=False)


def evaluate(task,context):
    from pathlib import Path
    import numpy as np
    from lll import ilvis0_control_shards as runner
    from lll.ilvis0_coupled_map_controls import Allowance,analytic_jacobian
    from lll.ilvis0_transform_native import make_reference
    from lll.ilvis0_sharded_native import plain
    bundle=runner._load(context.input_path());pointer=bundle['pointer'];name=pointer['filename']
    if name!=Path(name).name:raise ValueError('documented generated input filename required')
    path=context.root.parents[1]/'docs/ilvis0-recording-duration-controls/inputs'/name
    if runner._sha(path)!=pointer['sha256']:raise ValueError('frozen generated input changed')
    case=runner._load(path);events=0
    if len(case['dt'])!=96000 or case['configuration']['profile']!=task['payload']['profile']:
        raise ValueError('complete unchanged generated source required')
    maximum=dict(reference_setups=1,source_jacobian_oracles=7,reference_source_oracles=1,comparisons=6)
    def persist(record):
        nonlocal events
        runner._check_continue(context.root,context.manifest);events+=1
        context.save(f'reservation-{events:02d}.json',record)
    budget=Allowance(maximum,persist);budget.reserve(dict(reference_setups=1))
    reference=make_reference(case['configuration'],case['theta'],case['dv'],case['dt'],
        lower=-np.ones(27),upper=np.ones(27),center=np.zeros(27))
    if plain(reference.report())!=bundle['reference']:raise ValueError('source/reference/normalization changed')
    budget.reserve(dict(source_jacobian_oracles=1,reference_source_oracles=1))
    g0=reference.normalized_values_at(reference.parent.center);dg0=analytic_jacobian(reference,reference.parent.center)
    context.save('source-at-reference.json',plain(dict(value=g0,jacobian=dg0,reference=reference.report())))
    rows=[]
    for ordinal,probe in enumerate(bundle['probes']):
        budget.reserve(dict(source_jacobian_oracles=1,comparisons=1));p=np.array(probe['point'])
        dg=analytic_jacobian(reference,p)
        result=compare(bundle['maps'],probe['native_jacobian_m'],p,probe['source'],g0,dg,dg0,probe['actual_delta_m'])
        old=np.array(probe['shared_error_m'])
        if old.shape!=(6,3) or np.max(abs(np.array(result['source_error_m'])-old))>1e-6:
            raise ValueError('saved shared-source expression changed beyond frozen numerical crosscheck')
        record=dict(identity=probe['identity'],point=probe['point'],source_jacobian=dg.tolist(),**result)
        context.save(f'probe-{ordinal:02d}.json',record);rows.append(record)
    if len(rows)!=6 or budget.counts!=maximum:raise ValueError('complete fixed source-Jacobian accounting required')
    context.save('accounting.json',budget.counts)
    return dict(identity=task['identity'],passed=True,profile=task['payload']['profile'],probes=6,epochs_per_probe=6,
        physical_parameter_count=27,source_parameter_count=24,work=budget.counts,
        rms_anchored_error_m=float(np.sqrt(np.mean([r['rms_anchored_error_m']**2 for r in rows]))),
        rms_corrected_error_m=float(np.sqrt(np.mean([r['rms_corrected_error_m']**2 for r in rows]))),
        maximum_corrected_error_m=max(r['maximum_corrected_error_m'] for r in rows),
        probes_improved=sum(r['rms_corrected_error_m']<r['rms_anchored_error_m'] for r in rows),
        native_evaluations=0,original_reads=0,optimizer_starts=0,conditioned_radii_transferred=False,
        numerical_coverage_qualified=False,observational_coverage_qualified=False,scientific_decision='abstain')
