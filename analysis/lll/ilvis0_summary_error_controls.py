# SPDX-License-Identifier: AGPL-3.0-or-later
"""Fixed training summaries and one simultaneous declared-law error family."""
import hashlib
import json
from pathlib import Path


def recipe():
    from lll.ilvis0_receiver_distance import joint_recipe
    return dict(joint_recipe(),mode='summary-error-certificate',identities=4,
        times_s=list(map(float,range(2,291)))+list(map(float,range(292,439))),
        training_end_s=290.,summary_degrees=4,summary_rows=12,future_epochs=147,
        scalar_family_count=453,clock_interval_s=[-1.,1.],scale_upper=1.,alpha='.05',
        original_reads=0,future_observations_used=False,maximum_wall_s=600.)


def fixed_weights(times,*,training_end_s):
    """Twelve time-only Legendre rows; later columns are exactly zero."""
    import numpy as np
    t=np.asarray(times,float)
    if (t.ndim!=1 or not len(t) or not np.all(np.isfinite(t)) or np.any(np.diff(t)<=0.)
            or not np.isfinite(training_end_s)):
        raise ValueError('ordered finite epochs and training boundary required')
    indices=np.flatnonzero(t<=training_end_s)
    if len(indices)<4:raise ValueError('four distinct training epochs required for four summaries')
    earlier=t[indices];x=2*(earlier-earlier[0])/(earlier[-1]-earlier[0])-1.
    basis=np.polynomial.legendre.legvander(x,3);basis/=np.linalg.norm(basis,axis=0)
    weights=np.zeros((12,3*len(t)));ids=[]
    for degree in range(4):
        for axis,name in enumerate(('north','east','up')):
            weights[3*degree+axis,3*indices+axis]=basis[:,degree]
            ids.append(f'training:legendre-{degree}:{name}')
    weights.setflags(write=False);return weights,ids


def calculate(times,*,correlation_s,gyro_psd):
    import time
    import numpy as np
    from lll.ilvis0_receiver_distance import receiver_spec
    from lll.ilvis0_joint_error_operator import Operator
    from lll.ilvis0_joint_variance_bounds import projected_variance_bounds,marginal_variance_bounds
    from lll.ilvis0_gaussian_allowances import linear_allowances
    from lll.ilvis0_bounded_prediction import known_scale
    started=time.monotonic();settings=recipe();t=np.asarray(times,float)
    if gyro_psd not in settings['gyro_psd_choices']:raise ValueError('predeclared software gyro PSD required')
    spec=receiver_spec(correlation_s);weights,ids=fixed_weights(t,training_end_s=settings['training_end_s'])
    future=np.flatnonzero(t>settings['training_end_s'])
    if not len(future):raise ValueError('later prediction epochs required in the same error family')
    options=dict(receiver=spec,origin_s=settings['noise_origin_s'],accel_psd=np.eye(3)*settings['accel_psd'],
        gyro_psd=np.eye(3)*gyro_psd,coupling=settings['coupling'],clock_interval_s=settings['clock_interval_s'])
    bounds=projected_variance_bounds(t,weights,**options);marginal=marginal_variance_bounds(t,**options)
    if bounds['covariance_id']!=marginal['covariance_id']:raise ValueError('one full-period parent law required')
    variance=np.concatenate((bounds['variance_upper_m2'],marginal['variance_upper_m2'][future].ravel()))
    row_ids=ids+[f'future:{float(t[i])}:{axis}' for i in future for axis in ('north','east','up')]
    family=dict(summary_projection_id=bounds['projection_id'],future_times_s=t[future].tolist(),
        covariance_id=bounds['covariance_id'],row_ids=row_ids)
    projection_id=hashlib.sha256(json.dumps(family,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    scale=known_scale(settings['scale_upper'],source_id='declared-software-scale',covariance_id=bounds['covariance_id'])
    error=linear_allowances(variance,row_ids=row_ids,projection_id=projection_id,scale=scale,
        covariance_id=bounds['covariance_id'],alpha=settings['alpha'],error_distribution='gaussian')
    matrix_options={k:v for k,v in options.items() if k not in ('receiver','clock_interval_s')}
    reference=[]
    for shift in settings['clock_interval_s']:
        op=Operator(t+shift,spec,**matrix_options);reference.append(np.diag(op.project_covariance(weights)))
    reference=np.asarray(reference)
    if not np.all(bounds['variance_upper_m2']>=reference-1e-9*np.maximum(1.,abs(reference))):
        raise ValueError('certified summary variance below independent matrix-free check')
    radii=error['radius_m'];error=dict(error,radius_m=radii.tolist())
    return dict(passed=error['supported'],correlation_s=correlation_s,gyro_psd=gyro_psd,
        epochs=len(t),training_epochs=int(np.count_nonzero(t<=settings['training_end_s'])),
        summary_rows=12,future_epochs=len(future),scalar_family_count=len(variance),
        covariance_id=bounds['covariance_id'],summary_projection_id=bounds['projection_id'],
        family_projection_id=projection_id,exact_summary_variance_upper_m2=bounds['exact_variance_upper_m2'],
        summary_variance_upper_m2=bounds['variance_upper_m2'].tolist(),
        reference_summary_variances_m2=reference.tolist(),
        variance_upper_m2=variance.tolist(),allowances=error,
        summary_radius_range_m=[float(min(radii[:12])),float(max(radii[:12]))],
        future_radius_range_m=[float(min(radii[12:])),float(max(radii[12:]))],
        certified_variance_above_operator=True,law=bounds['law'],clock_interval_covered=True,
        elapsed_s=time.monotonic()-started,native_evaluations=0,optimizer_starts=0,original_reads=0,
        future_observations_used=False,noise_values_are_device_estimates=False,
        uncertainty_qualified=False,scientific_decision='abstain')


def prepare(root,identity='ilvis0-summary-error-controls-20261022'):
    from lll.studies.artifacts import atomic,encoded,safe_path
    from lll.studies.dependencies import source_closure
    from lll.studies.runtime import Definition
    root=Path(root).resolve();base=safe_path(root,'data/ilvis0-source-point-development/summary-error-inputs')
    if base.exists() or safe_path(root,'data/'+identity).exists():raise ValueError('new finite summary controls required')
    adapter='analysis/lll/ilvis0_summary_error_controls.py';plan='docs/ilvis0-summary-error-controls/PLAN.md'
    sources=source_closure(root,[adapter,plan,'analysis/tests/test_ilvis0_summary_error_controls.py',
        'analysis/tests/test_ilvis0_joint_projection_bounds.py','analysis/tests/test_ilvis0_gaussian_allowances.py'])
    settings=recipe();base.mkdir(parents=True);atomic(base/'recipe.json',encoded(settings));tasks=[]
    for tau in settings['correlation_s']:
        for i,q in enumerate(settings['gyro_psd_choices']):
            tasks.append(dict(identity=f'summary-{tau}-{i}',input_key='recipe',
                payload=dict(correlation_s=tau,gyro_psd=q),
                limits=dict(native_calls=0,packet_visits=0,bound_calls=0,bound_steps=0)))
    definition=dict(id=identity,adapter=adapter,sources=sources,inputs={'recipe':(base/'recipe.json').relative_to(root).as_posix()},
        tasks=tasks,workers=1,threads=1,maximum_wall_s=settings['maximum_wall_s'])
    atomic(base/'definition.json',encoded(definition));manifest=Definition.from_dict(definition,root).prepare(root)
    return dict(path='data/'+identity,identities=4,sources=len(manifest['sources']),
        allocation=manifest['allocation'],limits=manifest['limits'])


def evaluate(task,context):
    value=json.loads(context.input_path().read_bytes())
    if value!=recipe():raise ValueError('unchanged complete-period error family required')
    result=dict(calculate(value['times_s'],**task['payload']),identity=task['identity'])
    if result['scalar_family_count']!=value['scalar_family_count']:raise ValueError('complete simultaneous family required')
    context.save('summary-errors.json',result);return result


def inspect(root,prefix):
    from lll.studies.closed import ClosedStudy
    study=ClosedStudy(root,prefix);rows=[]
    try:
        if study.input('recipe')!=recipe():raise ValueError('fixed complete-period recipe required')
        for identity,task in study.tasks.items():
            if identity not in study.rows:continue
            value=study.envelope(identity)['result']
            if value.get('passed'):
                if value!=study.artifact(identity,'summary-errors.json'):raise ValueError('sealed summary artifact differs')
                if any(value[k]!=v for k,v in task['payload'].items()):raise ValueError('summary law identity differs')
                if value['scalar_family_count']!=453 or value['future_observations_used'] or value['uncertainty_qualified']:
                    raise ValueError('summary certificate scope changed')
            rows.append(value)
        expected={(tau,q) for tau in recipe()['correlation_s'] for q in recipe()['gyro_psd_choices']}
        actual={(r.get('correlation_s'),r.get('gyro_psd')) for r in rows if r.get('passed')}
        return dict(rows=rows,complete=len(rows)==4 and actual==expected,numerical_work=0,
            manifest_sha256=study.completion['manifest_sha256'],summary_sha256=study.completion['summary_sha256'],
            uncertainty_qualified=False)
    finally:study.close()


def render(report):
    text=['# Error bounds for fixed training summaries','',
        'Twelve fixed averages and trends now have outward error bounds under a supplied joint '
        'receiver-and-IMU noise law. Their error budget also covers all 147 later prediction epochs. '
        'These are generated software controls; they do not estimate actual instrument noise or fit aircraft data.',
        '', '| Receiver correlation (s) | Example gyro PSD (rad²/s) | Scalar errors covered together | '
        'Training-summary radius range (m) | Later-coordinate radius range (m) | Time (s) | Result |',
        '|---:|---:|---:|---:|---:|---:|---|']
    for r in report['rows']:
        if not r.get('passed'):
            text.append('| — | — | — | — | — | — | Failed |');continue
        ranges=['–'.join(f'{v:.3f}' for v in r[key]) for key in ('summary_radius_range_m','future_radius_range_m')]
        text.append('| '+' | '.join([str(r['correlation_s']),f"{r['gyro_psd']:.0e}",str(r['scalar_family_count']),
            *ranges,f"{r['elapsed_s']:.2f}",'Passed'])+' |')
    text+=['', 'The summaries depend only on timestamps. Later observations are never read. Signed weights '
        'retain shared offsets, drift and time correlations. Exact polynomial integration accounts for '
        'accumulated acceleration and gyro noise; certified exponential bounds account for correlated '
        'receiver error. A common ±1-second clock uncertainty is covered without resetting the noise origin.',
        '', 'Each law uses one Gaussian error budget of 0.05 for twelve summaries and 441 later coordinates. '
        'The declared scale is one. The four laws are sensitivity examples, not four independent trials. '
        'Summary weights have unit length, so their metre radii describe weighted measurements, not '
        'per-epoch position accuracy.',
        '', '**V01 remains unqualified.** Binding these summaries to complete nonlinear calibration bounds '
        'and establishing an adequate observation law remain separate requirements. No new observed fits '
        'were performed; the 53-stretch findings are unchanged.',
        '', '[Frozen scope](PLAN.md) · [Next step](../ilvis0-joint-projection-controls/NEXT_PLAN.md) · '
        '[Error assumptions](../PREDICTION_ERROR_ASSUMPTIONS.md)']
    return '\n'.join(text)+'\n'


def publish(root,prefix,output='docs/ilvis0-summary-error-controls'):
    from lll.ilvis0_control_publication import publish as package
    from lll.studies.artifacts import atomic,encoded,digest,safe_path
    from lll.studies.publication import archive_publication
    root=Path(root).resolve();data=safe_path(root,prefix);public=safe_path(root,output)
    if (public/'evidence-receipt.json').exists():raise ValueError('publication already sealed')
    report=inspect(root,prefix);package(data,public,render(report),plan='docs/ilvis0-summary-error-controls/PLAN.md')
    receipt=json.loads((public/'evidence-receipt.json').read_text());name='artifacts/publication/comparison.json'
    raw=encoded(report);atomic(public/name,raw);receipt['artifacts'][name]=digest(raw)
    atomic(public/'evidence-receipt.json',encoded(receipt))
    return dict(archive_publication(root,data,public),published=output,numerical_work=0)
