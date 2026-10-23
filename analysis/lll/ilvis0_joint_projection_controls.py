# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite known-answer and long-record checks for joint-error projections."""
import json
from pathlib import Path


def recipe():
    return dict(small_times_s=[2.,10.,30.,180.,290.],long_epochs=64080,long_step_s=.5,
        summary_degrees=4,seed=57,maximum_workspace_bytes=128*1024*1024,
        dense_relative_tolerance=3e-10,dense_absolute_tolerance=2e-10,
        long_roundtrip_relative_tolerance=1e-6,long_roundtrip_maximum_tolerance=1e-4,
        duality_relative_tolerance=1e-10,psd_relative_tolerance=1e-10,
        original_reads=0,native_calls=0,optimizer_starts=0,uncertainty_qualified=False)


def prepare(root,identity='ilvis0-joint-projection-controls-20261022'):
    from lll.studies.artifacts import atomic,encoded,safe_path
    from lll.studies.dependencies import source_closure
    from lll.studies.runtime import Definition
    root=Path(root).resolve();base=safe_path(root,'data/ilvis0-source-point-development/joint-projection-inputs')
    if base.exists() or safe_path(root,'data/'+identity).exists():raise ValueError('new finite controls required')
    adapter='analysis/lll/ilvis0_joint_projection_controls.py'
    sources=source_closure(root,[adapter,'analysis/tests/test_ilvis0_joint_error_operator.py',
        'docs/ilvis0-joint-projection-controls/PLAN.md'])
    base.mkdir(parents=True);atomic(base/'recipe.json',encoded(recipe()))
    tasks=[dict(identity=kind,input_key='recipe',payload=dict(kind=kind),
        limits=dict(native_calls=0,packet_visits=0,bound_calls=0,bound_steps=0)) for kind in ('small','long')]
    definition=dict(id=identity,adapter=adapter,sources=sources,
        inputs={'recipe':(base/'recipe.json').relative_to(root).as_posix()},tasks=tasks,
        workers=1,threads=1,maximum_wall_s=300.)
    atomic(base/'definition.json',encoded(definition));m=Definition.from_dict(definition,root).prepare(root)
    return dict(path='data/'+identity,identities=2,sources=len(m['sources']),limits=m['limits'],allocation=m['allocation'])


def evaluate(task,context):
    import time
    import hashlib
    import resource
    import numpy as np
    from lll.ilvis0_control_shards import _check_continue
    from lll.ilvis0_error_model import Spec,factor
    from lll.ilvis0_inertial_error import joint_covariance
    from lll.ilvis0_joint_error_operator import Operator
    settings=json.loads(context.input_path().read_bytes())
    if settings!=recipe():raise ValueError('fixed joint projection controls required')
    kind=task['payload']['kind']
    if kind not in ('small','long'):raise ValueError('two fixed software identities required')
    started=time.monotonic();small=kind=='small'
    times=np.asarray(settings['small_times_s']) if small else 2.+np.arange(settings['long_epochs'])*settings['long_step_s']
    n=len(times);columns=27 if small else 2;rng=np.random.default_rng(settings['seed'])
    z=rng.normal(size=(3*n,columns));weights_probe=rng.normal(size=(3*n,columns))
    spec=Spec(np.array([[.2,.03,0.],[.03,.3,.01],[0.,.01,.4]]),
        components=((3.,np.eye(3)*.07),(80.,np.eye(3)*.02)),offset=np.eye(3)*.1,
        drift=np.eye(3)*.02,drift_origin_s=0.,drift_span_s=438. if small else float(times[-1]))
    options=dict(origin_s=0.,accel_psd=np.diag([1.,2.,3.])*1e-7,
        gyro_psd=np.diag([1.,2.,.5])*1e-11,coupling=np.array([[0.,-9.81,0.],[9.81,0.,0.],[0.,0.,0.]]))
    _check_continue(context.root,context.manifest);op=Operator(times,spec,**options)
    _check_continue(context.root,context.manifest);carried=op.unwhiten(z);roundtrip=op.whiten(carried)
    _check_continue(context.root,context.manifest);adjoint=op.unwhiten_transpose(weights_probe)
    left=float(np.sum(carried*weights_probe));right=float(np.sum(z*adjoint))
    denominator=max(1.,float(np.linalg.norm(carried)*np.linalg.norm(weights_probe)))
    dual_error=abs(left-right)/denominator
    x=(times-times[0])/(times[-1]-times[0])*2.-1.
    basis=np.polynomial.legendre.legvander(x,3)
    basis/=np.linalg.norm(basis,axis=0)
    weights=np.zeros((12,3*n))
    for degree in range(4):
        for axis in range(3):weights[3*degree+axis,axis::3]=basis[:,degree]
    _check_continue(context.root,context.manifest);covariance=op.project_covariance(weights)
    eigenvalues=np.linalg.eigvalsh(covariance);spectral=max(1.,float(np.max(abs(eigenvalues))))
    relative=float(np.linalg.norm(roundtrip-z)/np.linalg.norm(z));maximum=float(np.max(abs(roundtrip-z)))
    dense_errors=None
    if small:
        dense=joint_covariance(times,spec,**options);lower=factor(dense)
        expected=[lower@z,lower.T@weights_probe,weights@dense@weights.T]
        actual=[carried,adjoint,covariance]
        for a,b in zip(actual,expected,strict=True):
            np.testing.assert_allclose(a,b,rtol=settings['dense_relative_tolerance'],atol=settings['dense_absolute_tolerance'])
        dense_errors=[float(np.max(abs(a-b))) for a,b in zip(actual,expected,strict=True)]
    # Include the extra temporary factor used inside project_covariance.
    workspace=op.storage_bytes+sum(a.nbytes for a in (z,weights_probe,carried,roundtrip,adjoint,basis,weights,covariance))+weights.nbytes
    passed=(relative<=settings['long_roundtrip_relative_tolerance']
        and maximum<=settings['long_roundtrip_maximum_tolerance']
        and dual_error<=settings['duality_relative_tolerance']
        and float(eigenvalues[0])>=-settings['psd_relative_tolerance']*spectral
        and workspace<=settings['maximum_workspace_bytes'])
    result=dict(identity=task['identity'],passed=passed,epochs=n,probe_columns=columns,summary_rows=12,
        operator_storage_bytes=op.storage_bytes,accounted_workspace_bytes=workspace,
        roundtrip_relative_error=relative,roundtrip_maximum_error=maximum,duality_relative_error=dual_error,
        minimum_projected_eigenvalue=float(eigenvalues[0]),dense_reference_maximum_errors=dense_errors,
        whole_covariance_constructed=small,elapsed_s=time.monotonic()-started,
        peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        generated_input_sha256={name:hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
            for name,a in (('z',z),('probe',weights_probe),('summary_weights',weights))},
        native_evaluations=0,optimizer_starts=0,original_reads=0,uncertainty_qualified=False,
        scientific_decision='abstain')
    context.save('projection-covariance.json',dict(covariance=covariance.tolist(),settings=settings))
    context.save('projection-checks.json',result);return result


def inspect(root,prefix):
    from lll.studies.closed import ClosedStudy
    study=ClosedStudy(root,prefix);rows=[]
    try:
        if study.input('recipe')!=recipe():raise ValueError('fixed projection recipe required')
        for identity in study.tasks:
            if identity not in study.rows:continue
            value=study.envelope(identity)['result']
            if value['passed']:
                if value!=study.artifact(identity,'projection-checks.json'):raise ValueError('projection checks differ')
                study.artifact(identity,'projection-covariance.json')
            rows.append(value)
        return dict(rows=rows,complete=len(rows)==2 and all(r['passed'] for r in rows),numerical_work=0,
            manifest_sha256=study.completion['manifest_sha256'],summary_sha256=study.completion['summary_sha256'],
            uncertainty_qualified=False)
    finally:study.close()


def render(report):
    text=['# Joint error covariance for training summaries','',
        'The shared operator can now propagate its supplied receiver-plus-IMU error law through fixed '
        'averages and trends without forming a whole-record covariance matrix. These are software '
        'controls with generated inputs, not aircraft fits or estimates of device noise.',
        '', '| Control | Epochs | Probe columns | Summary rows | Accounted workspace (MiB) | Time (s) | Result |',
        '|---|---:|---:|---:|---:|---:|---|']
    for r in report['rows']:
        if 'epochs' not in r:
            text.append('| '+r.get('identity','Unknown')+' | — | — | — | — | — | Failed |');continue
        text.append('| '+' | '.join([r['identity'],str(r['epochs']),str(r['probe_columns']),str(r['summary_rows']),
            f"{r['accounted_workspace_bytes']/1024**2:.2f}",f"{r['elapsed_s']:.2f}",
            'Passed' if r['passed'] else 'Failed'])+' |')
    text+=['', 'Small controls compare inverse, transpose and projected covariance against an independent '
        'dense reference, including cross-axis and time correlations. The long control checks inverse '
        'round-trip stability, transpose duality and linear-memory operation at 64,080 epochs. '
        'It does not build that record’s dense covariance.',
        '', 'The twelve summary rows are fixed functions of time. They do not discard physical calibration '
        'parameters or estimate a noise law. Correct propagation under the supplied linear law is separate '
        'from nonlinear calibration uncertainty, numerical interval certification and observed coverage. '
        '**V01 remains unqualified.**',
        '', '[Frozen checks and limits](PLAN.md) · [Error assumptions](../PREDICTION_ERROR_ASSUMPTIONS.md) · '
        '[Roadmap](../ANALYSIS_ROADMAP.md)']
    return '\n'.join(text)+'\n'


def publish(root,prefix,output='docs/ilvis0-joint-projection-controls'):
    from lll.ilvis0_control_publication import publish as package
    from lll.studies.artifacts import atomic,encoded,digest,safe_path
    from lll.studies.publication import archive_publication
    root=Path(root).resolve();data=safe_path(root,prefix);public=safe_path(root,output)
    if (public/'evidence-receipt.json').exists():raise ValueError('publication already sealed')
    report=inspect(root,prefix);package(data,public,render(report),plan='docs/ilvis0-joint-projection-controls/PLAN.md')
    receipt=json.loads((public/'evidence-receipt.json').read_text());name='artifacts/publication/comparison.json'
    raw=encoded(report);atomic(public/name,raw);receipt['artifacts'][name]=digest(raw)
    atomic(public/'evidence-receipt.json',encoded(receipt))
    return dict(archive_publication(root,data,public),published=output,numerical_work=0)
