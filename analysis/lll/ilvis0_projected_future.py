# SPDX-License-Identifier: AGPL-3.0-or-later
"""One future-bound recomputation from sealed joint-coordinate certificates."""


def evaluate(task,context):
    import numpy as np
    from lll.ilvis0_sharded_native import read,plain
    from lll.ilvis0_orientation_cover import sector
    from lll import ilvis0_acceleration_native as native,ilvis0_acceleration_envelope as joint
    from lll.ilvis0_control_shards import _check_continue
    bundle=read(context.input_path());spec=task['payload'];case=read(context.input_path(spec['case_key']))
    prior=bundle['result'];saved=bundle['future'];config=case['configuration']
    if prior['identity']!=task['identity'] or len(case['dt'])!=spec['packets']:raise ValueError('saved future task/input mismatch')
    config={k:np.ascontiguousarray(v) if k in ('initial_c','initial_v','initial_r','limits') else v for k,v in config.items()}
    box=sector(prior['task']['sector']);theta=np.asarray(case['theta']);dv=np.asarray(case['dv']);dt=np.asarray(case['dt'])
    reference=native.make_reference(config,theta,dv,dt,lower=box['lower'],upper=box['upper'],center=box['center'])
    original=bundle['training']['region']
    if reference.binding!=original['binding'] or reference.reference.source_id!=original['source_id']:
        raise ValueError('fixed source/reference changed')
    region=joint.TrainingRegion(**{key:original[source] for key,source in dict(times='times_s',design='design',
        target_lower='target_lower',target_upper='target_upper',inequality_design='inequality_design',inequality_upper='inequality_upper',
        lower='lower',upper='upper',center='center',coordinate_scale='coordinate_scale',origin='origin',
        binding='binding',source_id='source_id',arithmetic_allowance='arithmetic_allowance').items()})
    parameters=bundle['parameters'];left=np.array([p['lower'] for p in parameters]);right=np.array([p['upper'] for p in parameters])
    if (left.shape!=(42,) or right.shape!=(42,) or np.any(left>right) or np.any(left<saved['lower']) or np.any(right>saved['upper'])):
        raise ValueError('certified full projected box must remain inside saved domain')
    hull_left=np.minimum(left[:27],box['center']);hull_right=np.maximum(right[:27],box['center'])
    if np.any(hull_left<box['lower']) or np.any(hull_right>box['upper']):raise ValueError('native hull escapes original sector')
    context.charge(bound_calls=1,bound_steps=len(dt))
    report=native.enclose(config,theta,dv,dt,time=saved['time_s'],lower=hull_left,upper=hull_right,reference=reference,
        maximum_seconds=spec['maximum_bound_seconds'])
    difference=float(np.max(abs(report.center-np.asarray(saved['nominal']))*region.coordinate_scale))
    context.save('bound.json',plain(dict(report.report(),reference=reference.report(),native_center_difference_m=difference)))
    # The qualified future API makes exactly six proposals; reserve them first.
    for ordinal in range(1,7):
        _check_continue(context.root,context.manifest)
        context.save(f'proposal-{ordinal:02d}.json',dict(ordinal=ordinal,maximum_exact_certificates=2,maximum_seconds=1.))
    envelope=joint.future(region,time=saved['time_s'],native_value=saved['nominal'],native_jacobian=saved['jacobian'],
        report=report,reference=reference,lower=left,upper=right)
    context.save('future.json',plain(dict(envelope,projected_lower=left,projected_upper=right)))
    retained=True;contained=True
    if prior['truth_in_sector']:
        truth=np.r_[bundle['physical_truth'],prior['known_shared_error']]
        retained=bool(np.all(left<=truth) and np.all(truth<=right))
        value=np.asarray(prior['future_truth_m']);contained=bool(np.all(envelope['lower']<=value) and np.all(value<=envelope['upper']))
    previous=np.array(prior['future_upper_m'])-np.array(prior['future_lower_m']);width=envelope['upper']-envelope['lower']
    return plain(dict(identity=task['identity'],passed=difference<=1e-6 and retained and contained,
        model=prior['task']['model'],profile=prior['task']['profile'],sector=prior['task']['sector'],
        parameter_count=42,previous_width_m=previous,new_width_m=width,width_ratio=width/previous,
        future_lower_m=envelope['lower'],future_upper_m=envelope['upper'],future_truth_m=prior['future_truth_m'],
        known_truth_checked=prior['truth_in_sector'],known_truth_retained=retained,known_future_contained=contained,
        maximum_center_difference_m=difference,lp_proposals_reserved=6,exact_certificate_ceiling=12,
        bound_evaluations=1,native_evaluations=0,original_reads=0,optimizer_starts=0,
        observational_coverage_qualified=False,scientific_decision='abstain'))
