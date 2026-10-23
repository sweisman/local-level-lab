# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite independent cold-source comparisons for typed reusable prefixes."""
import json
from pathlib import Path


def recipe():
    return dict(identities=18,packets=16,prefix_packets=[2,8],query_variants=3,
        source_steps_per_identity=174,fork_attempts_per_identity=9,
        frame_checks_per_identity=66,isolation_checks_per_identity=6,
        native_calls=0,optimizer_starts=0,original_reads=0,
        whole_native_prefix_qualified=False,maximum_wall_s=600.)


def limits():
    r=recipe();return dict(source_steps=r['source_steps_per_identity'],fork_attempts=r['fork_attempts_per_identity'],
        frame_checks=r['frame_checks_per_identity'],isolation_checks=r['isolation_checks_per_identity'])


def case(model,profile):
    import numpy as np
    from scipy.linalg import expm
    if model not in (0,1,2) or type(profile) is not bool:raise ValueError('fixed generated case required')
    angle=np.array([.03,-.05,.08])*(model+1)
    x,y,z=angle;mount=expm(np.array([[0.,-z,y],[z,0.,-x],[-y,x,0.]]))
    sizes=np.full(27,.01);sizes[25]=1/1024
    point=np.linspace(-.04,.06,27);point[25]=.125 if profile else -.125
    lo=point-.005;hi=point+.007;lo[25]=-.3;hi[25]=.7
    dt=np.tile([.004,.006,.005,.007],4)
    raw=np.arange(48,dtype=float).reshape(16,3)
    theta=np.sin(raw*.27+model)*.0005;dv=np.tile([.001,-.002,-.05],(16,1))
    dv+=np.cos(raw*.17+int(profile))*.0001
    value=dict(configuration=dict(initial_r=mount,limits=sizes,model=model,profile=profile),theta=theta,dv=dv,dt=dt)
    return value,point,lo,hi


def compare(left,right):
    import numpy as np
    keys=set(left)-{'state_bytes'}
    if keys!=set(right)-{'state_bytes'}:raise ValueError('source output schema differs')
    arrays=0
    for key in keys:
        if isinstance(left[key],np.ndarray):
            if not np.array_equal(left[key],right[key]):raise ValueError('source array differs: '+key)
            arrays+=1
        elif left[key]!=right[key]:raise ValueError('source metadata differs: '+key)
    return arrays


def check(kind,model,profile,*,kernels,cold_kernels,reserve,charge,save):
    import time
    import numpy as np
    from lll.ilvis0_source_prefix import make_stream,fork_stream
    from lll.ilvis0_source_stream import SourceStream
    from lll.ilvis0_source_derivative_intervals import Stream as Intervals
    from lll.ilvis0_source_point_derivatives import Stream as Point
    value,z,lo,hi=case(model,profile);n=len(value['dt']);settings=recipe();started=time.monotonic()
    tags=[0.]
    for dt in value['dt']:tags.append(tags[-1]+float(dt))
    reference=f'generated-{model}-{int(profile)}';latest=tags[-1]-.002
    clock=float(value['configuration']['limits'][25]*z[25]);center=tags[12]-clock
    queries=[float(np.nextafter(center,-np.inf)),center,float(np.nextafter(center,np.inf))]
    arguments=dict(lower=lo,upper=hi,reference_binding=reference,maximum_packets=n)
    def fresh(time):return make_stream(kernels,kind,value,z,time,**arguments)
    def cold(time):
        k=cold_kernels[kind]
        if kind=='reference':return SourceStream(k,value,z,time,maximum_packets=n)
        if kind=='point':return Point(k,value,z,time,maximum_packets=n)
        return Intervals(k,value,z,lo,hi,time,maximum_packets=n)
    def advance(s):reserve(source_steps=1);charge(bound_calls=1,bound_steps=1);return s.append()
    def fork(s,time,ref=reference):reserve(fork_attempts=1);return fork_stream(s,time,reference_binding=ref)
    arrays=0;comparisons=[]
    for prefix in settings['prefix_packets']:
        parent=fresh(latest)
        for _ in range(prefix):advance(parent)
        before=bytes(parent._buffer)
        for query in queries:
            child=fork(parent,query);original=cold(query)
            for _ in range(prefix):advance(original)
            for _ in range(prefix,n):
                a=advance(child);b=advance(original);reserve(frame_checks=1);arrays+=compare(a,b)
            reserve(isolation_checks=1)
            if bytes(parent._buffer)!=before:raise ValueError('fork changed canonical source prefix')
            if child.visits!=n or child.maximum_packets!=n or child.prefix_reused_packets!=prefix:
                raise ValueError('fork reset its original packet position or allowance')
            comparisons.append(dict(prefix_packets=prefix,query_time_s=query,tail_frames=n-prefix,
                exact_outputs=True,parent_unchanged=True))
            child.close();original.close()
        # Keep only the final complete prefix for the boundary/rebinding checks.
        if prefix!=settings['prefix_packets'][-1]:parent.close()
    clipped=fresh(tags[1]+.0002);advance(clipped);advance(clipped)
    rejected=[]
    for label,s,query_time,ref in (('clipped',clipped,latest,reference),
            ('prefix_boundary',parent,tags[8],reference),('reference_binding',parent,latest,'different')):
        try:fork(s,query_time,ref)
        except ValueError:rejected.append(label)
        else:raise ValueError('unsafe source fork accepted: '+label)
    parent.close();clipped.close()
    save('source-comparisons.json',comparisons)
    save('generated-source.json',dict(configuration={k:v.tolist() if isinstance(v,np.ndarray) else v
        for k,v in value['configuration'].items()},theta=value['theta'].tolist(),dv=value['dv'].tolist(),
        dt=value['dt'].tolist(),point=z.tolist(),lower=lo.tolist(),upper=hi.tolist()))
    return dict(passed=True,kind=kind,model=model,profile=profile,source_frames_checked=66,
        exact_arrays_checked=arrays,successful_forks=6,expected_rejections=rejected,
        prefix_state_bytes=kernels[kind].state_bytes,elapsed_s=time.monotonic()-started,
        native_evaluations=0,optimizer_starts=0,original_reads=0,whole_native_prefix_qualified=False,
        observational_coverage_qualified=False,scientific_decision='abstain')


def prepare(root,identity='ilvis0-prefix-source-controls-v2-20261022'):
    from lll.studies.artifacts import safe_path,atomic,encoded
    from lll.studies.dependencies import source_closure
    from lll.studies.runtime import Definition
    root=Path(root).resolve();base=safe_path(root,'data/ilvis0-source-point-development/'+identity+'-inputs')
    if base.exists() or safe_path(root,'data/'+identity).exists():raise ValueError('new finite source-prefix freeze required')
    adapter='analysis/lll/ilvis0_source_prefix_controls.py'
    sources=source_closure(root,[adapter,'docs/ilvis0-prefix-source-controls/PLAN.md',
        'docs/ilvis0-prefix-reuse/DESIGN.md','analysis/tests/test_ilvis0_source_prefix.py',
        'analysis/tests/test_ilvis0_source_prefix_controls.py','analysis/lll/ilvis0_source_prefix_reference.cpp',
        'analysis/lll/ilvis0_source_prefix_intervals.cpp'])
    base.mkdir(parents=True);atomic(base/'recipe.json',encoded(recipe()));tasks=[]
    for kind in ('reference','interval','point'):
        for model in range(3):
            for profile in (False,True):
                tasks.append(dict(identity=f'prefix-{kind}-{model}-{int(profile)}',input_key='recipe',
                    payload=dict(kind=kind,model=model,profile=profile,limits=limits()),
                    limits=dict(native_calls=0,packet_visits=0,bound_calls=174,bound_steps=174)))
    definition=dict(id=identity,adapter=adapter,sources=sources,inputs={'recipe':(base/'recipe.json').relative_to(root).as_posix()},
        tasks=tasks,workers=1,threads=1,maximum_wall_s=recipe()['maximum_wall_s'])
    atomic(base/'definition.json',encoded(definition));manifest=Definition.from_dict(definition,root).prepare(root)
    return dict(path='data/'+identity,identities=18,sources=len(manifest['sources']),allocation=manifest['allocation'],limits=manifest['limits'])


def evaluate(task,context):
    from lll.ilvis0_control_shards import _check_continue
    from lll.ilvis0_source_prefix import load_kernels
    from lll.ilvis0_source_stream import load_stream
    from lll.ilvis0_source_derivative_intervals import load_kernel as interval_kernel
    from lll.ilvis0_source_point_derivatives import load_kernel as point_kernel
    from lll.studies.artifacts import digest
    from lll.studies.journal import Journal
    settings=json.loads(context.input_path().read_bytes());spec=task['payload']
    if settings!=recipe() or spec['limits']!=limits():raise ValueError('fixed finite source-prefix controls required')
    path=context.directory/'allowance.sqlite';journal=Journal(path,
        freeze=digest((context.root/'manifest.json').read_bytes()),limits={task['identity']:limits()})
    journal.start(task['identity'])
    def reserve(**values):
        _check_continue(context.root,context.manifest)
        for key,v in values.items():journal.reserve(task['identity'],key,v)
    directory=context.root/'shards'/f'{context.shard:03d}'/'kernels';source=context.root/'source-freeze/analysis/lll'
    try:
        kernels,meta=load_kernels(directory,source_directory=source);cold={}
        for kind,loader in (('reference',load_stream),('interval',interval_kernel),('point',point_kernel)):
            k,m=loader(directory,source_directory=source);cold[kind]=k;meta['cold-'+kind]=m
        for m in meta.values():
            if any(context.manifest['sources'].get('analysis/lll/'+name)!=sha for name,sha in m['sources'].items()):
                raise ValueError('compiled source differs from freeze')
        context.save('compilation.json',meta)
        result=check(spec['kind'],spec['model'],spec['profile'],kernels=kernels,cold_kernels=cold,
            reserve=reserve,charge=context.charge,save=context.save)
        counts={k:journal.count(task['identity'],k) for k in limits()}
        if counts!=limits():raise ValueError('incomplete source-prefix accounting')
        result=dict(result,identity=task['identity'],work=counts);context.save('prefix-checks.json',result);return result
    finally:journal.verify();context.note_file(path)


def inspect(root,prefix):
    from lll.studies.closed import ClosedStudy
    study=ClosedStudy(root,prefix);rows=[]
    try:
        if study.input('recipe')!=recipe():raise ValueError('fixed prefix-source recipe required')
        for identity in study.tasks:
            if identity not in study.rows:continue
            value=study.envelope(identity)['result']
            if value.get('passed'):
                if value!=study.artifact(identity,'prefix-checks.json'):raise ValueError('saved prefix result differs')
                for name in ('source-comparisons.json','generated-source.json','compilation.json'):study.artifact(identity,name)
                if value['work']!=limits() or value['whole_native_prefix_qualified']:raise ValueError('source-only scope changed')
            rows.append(value)
        actual={(r.get('kind'),r.get('model'),r.get('profile')) for r in rows if r.get('passed')}
        expected={(kind,m,p) for kind in ('reference','interval','point') for m in range(3) for p in (False,True)}
        return dict(rows=rows,complete=len(rows)==18 and actual==expected,
            manifest_sha256=study.completion['manifest_sha256'],summary_sha256=study.completion['summary_sha256'],
            numerical_work=0,whole_native_prefix_qualified=False)
    finally:study.close()


def render(report):
    text=['# Reusing a verified source prefix','',
        'The reference, interval-derivative and point-derivative source streams can now copy a '
        'complete prefix and finish a different query without repeating its earlier packets. '
        'The comparison uses generated sources and independent original cold kernels.',
        '', '| Source stream | Cases passed | Tail frames checked | Exact array comparisons |',
        '|---|---:|---:|---:|']
    for kind in ('reference','interval','point'):
        rows=[r for r in report['rows'] if r.get('kind')==kind and r.get('passed')]
        text.append(f"| {kind} | {len(rows)}/6 | {sum(r['source_frames_checked'] for r in rows)} | "
            f"{sum(r['exact_arrays_checked'] for r in rows)} |")
    if not report['complete']:
        reasons=sorted({r.get('reason','Unspecified failure') for r in report['rows'] if not r.get('passed')})
        text+=['', '**Qualification did not pass.** Saved failure reasons: '+ '; '.join(reasons)+'. '
            'The failed freeze and its charged identities are preserved; no retry follows within that allowance.']
    text+=['', 'The planned checks cover nonuniform packet periods, nonzero/asymmetric clock support, query knots '
        'and adjacent values, every parameter column and both midpoint/end phases. Copying must leave '
        'the parent unchanged. Clipped histories, a query reaching back into its prefix and changed '
        'reference bindings must be rejected. Packet allowances are preserved.',
        '', '**Scope: source copying only; complete native reuse remains unqualified.** The source calculations are shared by the '
        'Earth candidates; this is not a model-comparison result. The complete geographic, velocity, '
        'force-integral, common-clock and conditioning states still need equivalent treatment. '
        'No aircraft integration or fit was performed. V01 remains unqualified.',
        '', '[Fixed scope](PLAN.md) · [Design](../ilvis0-prefix-reuse/DESIGN.md) · '
        '[Remaining complete-state work](../ilvis0-long-remainder-feasibility/PREFIX_REUSE_PLAN.md)']
    return '\n'.join(text)+'\n'


def publish(root,prefix,output='docs/ilvis0-prefix-source-controls'):
    from lll.ilvis0_control_publication import publish as package
    from lll.studies.artifacts import atomic,encoded,digest,safe_path
    from lll.studies.publication import archive_publication
    root=Path(root).resolve();data=safe_path(root,prefix);public=safe_path(root,output)
    if (public/'evidence-receipt.json').exists():raise ValueError('publication already sealed')
    report=inspect(root,prefix);package(data,public,render(report),plan='docs/ilvis0-prefix-source-controls/PLAN.md')
    receipt=json.loads((public/'evidence-receipt.json').read_text());name='artifacts/publication/comparison.json'
    raw=encoded(report);atomic(public/name,raw);receipt['artifacts'][name]=digest(raw)
    atomic(public/'evidence-receipt.json',encoded(receipt))
    return dict(archive_publication(root,data,public),published=output,numerical_work=0)
