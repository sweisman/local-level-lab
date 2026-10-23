# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite generated-history checks of data-independent starting enclosures."""
import json
from pathlib import Path


def recipe():
    return dict(identities=6,packets=96000,time_s=2.,physical_parameters=27,
        workers=4,threads=1,maximum_bound_s=600.,maximum_wall_s=3600.,
        maximum_rss_bytes=1536*1024**2,oracle_arithmetic_allowance_m=1e-5,
        original_reads=0,optimizer_starts=0)


def raw_layout(case):
    required={'configuration','theta','dv','dt'}
    return required<=set(case)<=required|{'center','provenance'}


def setup(case,*,reserve):
    if not raw_layout(case):
        raise ValueError('only raw generated inputs; no old training material permitted')
    import numpy as np
    from lll.ilvis0_transform_native import make_reference
    from lll.ilvis0_directional_acceleration import DirectionalAcceleration
    configuration={k:np.ascontiguousarray(v,float) if k in ('initial_c','initial_v','initial_r','limits') else v
        for k,v in case['configuration'].items()}
    theta,dv,dt=(np.ascontiguousarray(case[k],float) for k in ('theta','dv','dt'))
    lower=np.full(27,-1.);upper=np.ones(27);center=np.zeros(27)
    reserve(reference_setups=1)
    reference=make_reference(configuration,theta,dv,dt,lower=lower,upper=upper,center=center)
    reserve(physical_proofs=1);proof=DirectionalAcceleration(reference,lower,upper)
    return dict(configuration=configuration,theta=theta,dv=dv,dt=dt,lower=lower,upper=upper,
        center=center,reference=reference,conditioning=proof)


def auxiliary_limits():return dict(reference_setups=1,physical_proofs=1,native_queries=1,cold_queries=1)


def check(value,*,tangent,cold_kernels,reserve,charge,save,checkpoint):
    import ctypes
    import resource
    import time
    import numpy as np
    from lll.ilvis0_remainder_native import enclose
    from lll.ilvis0_packet_boundary_flags import validate
    r=recipe();n=len(value['dt']);c=value['configuration'];started=time.monotonic()
    if n!=r['packets'] or not np.all(value['dt']==.005) or abs(c['limits'][25])>1.:
        raise ValueError('unchanged 96,000-packet 200-Hz history and supported clock required')
    proof=value['conditioning'].report();save('reference.json',value['reference'].report());save('physical-proof.json',proof)
    if (proof['uses_training_data'] is not False or proof['applies_only_to_physical_domain'] is not True
            or proof['lower']!=[-1.]*27 or proof['upper']!=[1.]*27):
        raise ValueError('full independent physical-domain proof required')
    checkpoint();reserve(native_queries=1);charge(native_calls=1,packet_visits=n)
    out=np.empty((1,3));jac=np.empty((3,27));flag=ctypes.c_int()
    code=tangent(n,value['theta'],value['dv'],value['dt'],1,np.array([r['time_s']]),
        c['initial_c'],c['initial_v'],c['initial_r'],c['limits'],value['center'],
        c['model'],int(c['profile']),c['gravity'],c['radius'],out,jac,ctypes.byref(flag))
    boundary=validate(status=int(code),counter=flag.value,dt=value['dt'],time_s=r['time_s'],clock_offset_s=0.)
    if not np.all(np.isfinite(out)) or not np.all(np.isfinite(jac)):raise ValueError('finite independent point check required')
    save('native.json',dict(time_s=r['time_s'],point=value['center'].tolist(),prediction=out[0].tolist(),
        jacobian=jac.tolist(),status=int(code),warning=flag.value,boundary=boundary))
    checkpoint();reserve(cold_queries=1);charge(bound_calls=1,bound_steps=9*n);bound_started=time.monotonic()
    try:
        bound=enclose(c,value['theta'],value['dv'],value['dt'],time=r['time_s'],lower=value['lower'],upper=value['upper'],
            reference=value['reference'],conditioning=value['conditioning'],maximum_seconds=r['maximum_bound_s'],**cold_kernels)
    finally:
        elapsed=time.monotonic()-bound_started
        save('bound-work.json',dict(elapsed_s=elapsed,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024))
    report=bound.report();save('bound.json',report);matrix=bound.design(jac,value['reference'])
    error=abs((bound.center-out[0])*np.array([6371000.,6371000.,1.]))
    if (report['conditioning']!=proof or report['lower']!=[-1.]*27 or report['upper']!=[1.]*27
            or report['normalized_center']!=[0.]*27 or report['time_s']!=r['time_s']
            or report['source_id']!=value['reference'].parent.source_id
            or report['reference_binding']!=value['reference'].binding or matrix.shape!=(3,51)
            or max(error)>r['oracle_arithmetic_allowance_m'] or elapsed>r['maximum_bound_s']
            or resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024>r['maximum_rss_bytes']):
        raise ValueError('independent full-domain starting bound failed its frozen checks')
    save('columns.json',dict(matrix=matrix.tolist(),native_center_error_m=error.tolist()))
    return dict(passed=True,initial_root_supported=True,model=c['model'],profile=bool(c['profile']),
        time_s=r['time_s'],packets=n,physical_parameter_count=27,design_columns_checked=51,
        maximum_native_center_error_m=float(max(error)),bound_elapsed_s=elapsed,elapsed_s=time.monotonic()-started,
        uses_training_data=False,native_evaluations=1,bound_evaluations=1,original_reads=0,optimizer_starts=0,
        complete_cadence_qualified=False,prediction_method_qualified=False,observational_coverage_qualified=False,
        scientific_decision='abstain')


def prepare(root,identity='ilvis0-dense-physical-roots-v1-20261023'):
    import subprocess
    from lll.ilvis0_native_prefix_repair_study import inspect as reuse_inspect
    from lll.studies.closed import ClosedStudy
    from lll.studies.artifacts import atomic,encoded,digest,safe_path
    from lll.studies.dependencies import source_closure
    from lll.studies.runtime import Definition
    root=Path(root).resolve();base=safe_path(root,'data/ilvis0-source-point-development/'+identity+'-inputs')
    if base.exists() or safe_path(root,'data/'+identity).exists():raise ValueError('fresh physical-root freeze required')
    reuse=reuse_inspect(root)
    if not reuse['complete']:raise ValueError('complete long-prefix comparison required first')
    prior=ClosedStudy(root,'data/ilvis0-long-remainder-feasibility-20261022')
    try:
        base.mkdir(parents=True);inputs={};tasks=[];compiler=subprocess.check_output(['c++','--version'],text=True).splitlines()[0]
        for old_id,task in prior.tasks.items():
            spec=task['payload'];raw=prior.input(spec['case_key'],raw=True);case=json.loads(raw);r=recipe()
            if (not raw_layout(case) or any(len(case[k])!=r['packets'] for k in ('theta','dv','dt'))
                    or any(t!=.005 for t in case['dt']) or abs(case['configuration']['limits'][25])>1.
                    or case['configuration']['model']!=spec['model'] or bool(case['configuration']['profile'])!=spec['profile']):
                raise ValueError('fixed raw generated history changed')
            name=f'physical-root-{spec["model"]}-{int(spec["profile"])}';atomic(base/(name+'.json'),raw)
            inputs[name]=str((base/(name+'.json')).relative_to(root))
            tasks.append(dict(identity=name,input_key=name,payload=dict(model=spec['model'],profile=spec['profile'],
                compiler=compiler,case_sha256=digest(raw),recipe=r,auxiliary_limits=auxiliary_limits()),
                limits=dict(native_calls=1,packet_visits=r['packets'],bound_calls=1,bound_steps=9*r['packets'])))
        if len(tasks)!=6 or {(t['payload']['model'],t['payload']['profile']) for t in tasks}!={(m,p) for m in range(3) for p in (False,True)}:
            raise ValueError('all six unchanged model/processing cases required')
        provenance=dict(parent=prior.prefix,manifest_sha256=prior.completion['manifest_sha256'],
            reuse_manifest_sha256=reuse['manifest_sha256'],recipe=recipe())
        atomic(base/'provenance.json',encoded(provenance));inputs['provenance']=str((base/'provenance.json').relative_to(root))
        adapter='analysis/lll/ilvis0_dense_root_controls.py';plan='docs/ilvis0-dense-physical-roots/PLAN.md'
        sources=source_closure(root,[adapter,plan,'analysis/tests/test_ilvis0_dense_root_controls.py'])
        definition=dict(id=identity,adapter=adapter,sources=sources,inputs=inputs,tasks=tasks,
            workers=4,threads=1,maximum_wall_s=recipe()['maximum_wall_s'])
        atomic(base/'definition.json',encoded(definition));m=Definition.from_dict(definition,root).prepare(root)
        return dict(path='data/'+identity,identities=6,sources=len(m['sources']),allocation=m['allocation'],limits=m['limits'])
    finally:prior.close()


def evaluate(task,context):
    import subprocess
    from lll.ilvis0_control_shards import _check_continue
    from lll.studies.artifacts import digest
    from lll.studies.journal import Journal
    from lll.ilvis0_batched_transport import configure_backend
    from lll.ilvis0_source_stream import load_stream
    from lll.ilvis0_source_derivative_intervals import load_kernel as interval_kernel
    from lll.ilvis0_source_point_derivatives import load_kernel as point_kernel
    from lll.ilvis0_shape import load_tangent
    spec=task['payload'];raw=context.input_path().read_bytes();case=json.loads(raw)
    if (spec['recipe']!=recipe() or spec['auxiliary_limits']!=auxiliary_limits() or digest(raw)!=spec['case_sha256']
            or any(case['configuration'][k]!=spec[k] for k in ('model','profile'))
            or spec['compiler']!=subprocess.check_output(['c++','--version'],text=True).splitlines()[0]):
        raise ValueError('fixed physical-root scope or compiler differs')
    path=context.directory/'allowance.sqlite';journal=Journal(path,
        freeze=digest((context.root/'manifest.json').read_bytes()),limits={task['identity']:auxiliary_limits()})
    journal.start(task['identity'])
    def checkpoint():_check_continue(context.root,context.manifest)
    def reserve(**values):
        checkpoint()
        for key,n in values.items():journal.reserve(task['identity'],key,n)
    try:
        value=setup(case,reserve=reserve);source=context.root/'source-freeze/analysis/lll'
        directory=context.root/'shards'/f'{context.shard:03d}'/'kernels';backend=configure_backend(directory,source_directory=source)
        kernels={};metadata={'backend':backend}
        for key,loader in (('source_kernel',load_stream),('derivative_kernel',interval_kernel),('point_kernel',point_kernel)):
            kernels[key],metadata[key]=loader(directory,source_directory=source)
        for meta in metadata.values():
            if meta['compiler']!=spec['compiler'] or any(context.manifest['sources'].get('analysis/lll/'+n)!=h for n,h in meta['sources'].items()):
                raise ValueError('compiled physical-root source changed')
        tangent,tmeta=load_tangent(directory)
        if tmeta['compiler']!=spec['compiler'] or tmeta['source_sha256']!=context.manifest['sources']['analysis/lll/ilvis0_tangent.cpp']:
            raise ValueError('independent tangent source changed')
        context.save('compilation.json',dict(components=metadata,tangent=tmeta))
        result=check(value,tangent=tangent,cold_kernels=kernels,reserve=reserve,charge=context.charge,save=context.save,checkpoint=checkpoint)
        counts={k:journal.count(task['identity'],k) for k in auxiliary_limits()}
        if counts!=auxiliary_limits():raise ValueError('physical-root accounting differs')
        context.save('accounting.json',counts);result=dict(result,identity=task['identity'],charged_auxiliary=counts)
        context.save('root-checks.json',result);return result
    finally:journal.verify();context.note_file(path)


def inspect(root,prefix='data/ilvis0-dense-physical-roots-v1-20261023'):
    from lll.studies.closed import ClosedStudy
    study=ClosedStudy(root,prefix);rows=[]
    try:
        for identity,task in study.tasks.items():
            if identity not in study.rows:
                rows.append(dict(identity=identity,passed=False,reason='not started',**{k:task['payload'][k] for k in ('model','profile')}));continue
            envelope=study.envelope(identity);row=dict(envelope['result'])
            for name,sha in envelope['artifacts'].items():study.read(name,sha,raw=True)
            if row.get('passed'):
                if row!=study.artifact(identity,'root-checks.json') or envelope['charged']!=task['limits']:
                    raise ValueError('saved physical-root result or charges changed')
                if study.artifact(identity,'accounting.json')!=auxiliary_limits():raise ValueError('root work differs')
            row.update(identity=identity,model=task['payload']['model'],profile=task['payload']['profile']);rows.append(row)
        complete=len(rows)==6 and {(r['model'],r['profile']) for r in rows if r.get('passed')}=={
            (m,p) for m in range(3) for p in (False,True)}
        return dict(rows=rows,complete=complete,manifest_sha256=study.completion['manifest_sha256'],
            summary_sha256=study.completion['summary_sha256'],numerical_work=0,complete_cadence_qualified=False,
            prediction_method_qualified=False,observational_coverage_qualified=False,scientific_decision='abstain')
    finally:study.close()


def render(report):
    labels=['Globe + field','Globe, zero field','Stationary disc']
    lines=['# Starting prediction bounds without old training assumptions','',
        'Six fixed generated histories test the first training query with the full physical '
        'calibration range and no older one-metre training constraints. No aircraft original or future receiver observation is used.',
        '', '| Candidate | Processing | Starting calculation |','|---|---|---|']
    for row in report['rows']:
        state='Supported' if row.get('passed') else 'Not qualified: '+row.get('reason','failed')
        lines.append('| '+' | '.join([labels[row['model']],'Profiled removal' if row['profile'] else 'Zero removal',state])+' |')
    count=sum(r.get('passed') is True for r in report['rows'])
    lines+=['',f'**{count}/6 starting calculations passed.**',
        '', 'This tests support at two seconds, not complete-cadence prediction or empirical noise coverage. '
        'An unsupported calculation is a software limitation and does not reject an Earth candidate. '
        'Earlier aircraft findings and all frozen failures remain unchanged.',
        '', '[Frozen limits](PLAN.md) · [Complete-cadence requirements](../ilvis0-joint-projection-controls/NEXT_PLAN.md)']
    return '\n'.join(lines)+'\n'


def publish(root,prefix='data/ilvis0-dense-physical-roots-v1-20261023',output='docs/ilvis0-dense-physical-roots'):
    from lll.ilvis0_control_publication import publish as package
    from lll.studies.artifacts import atomic,encoded,digest,safe_path
    from lll.studies.publication import archive_publication
    root=Path(root).resolve();data=safe_path(root,prefix);public=safe_path(root,output)
    if (public/'evidence-receipt.json').exists():raise ValueError('physical-root publication already sealed')
    report=inspect(root,prefix);package(data,public,render(report),plan='docs/ilvis0-dense-physical-roots/PLAN.md')
    receipt=json.loads((public/'evidence-receipt.json').read_bytes());name='artifacts/publication/comparison.json'
    raw=encoded(report);atomic(public/name,raw);receipt['artifacts'][name]=digest(raw)
    atomic(public/'evidence-receipt.json',encoded(receipt))
    return dict(archive_publication(root,data,public),published=output,numerical_work=0)
