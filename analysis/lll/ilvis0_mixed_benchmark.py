# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite fixed-point arithmetic benchmark; no optimizer or observed inputs."""
import math

SCOPE='generated fixed-point mixed tangent benchmark; no fits or original/protected reads'


def recipe():
    from lll.airquantumgrav_training_controls import parameter_limits
    return dict(version='mixed-tangent-long-controls-v1',duration_s=1200.,rate_hz=300,queries=1200,
        query_start_s=.5,query_step_s=1.,pattern='fast',method='linear_points',limits=parameter_limits(),
        training_sigma_m=.05,relative_tolerance=2e-10,absolute_tolerance=2e-10,
        workers=1,threads=1,maximum_wall_s=7200.,optimizer_starts=0,original_reads=0,protected_reads=0,retries=0)


def tasks():
    return [dict(identity=f'{model}-{int(profile)}',input_key='recipe',native_kind='tangent',
        payload=dict(model=model,latitude_deg=55.,profile=profile,start=0),
        limits=dict(native_calls=2,packet_visits=864000000,bound_calls=0,bound_steps=0))
        for model in ('sphere_rotating','sphere_still','flat_still') for profile in (False,True)]


def construction_limits(r):
    n=round(r['duration_s']*r['rate_hz'])
    return dict(constructed_intervals=n,generated_samples=n+1+2*r['queries']//3+r['queries'])


def checks(arrays,*,boundaries):
    import numpy as np
    a,b=(arrays[k] for k in ('reference_jacobian','candidate_jacobian'));sd=arrays['standard_deviation']
    shape=arrays['reference_coordinates'].shape
    if (len(shape)!=2 or shape[1]!=3 or not 1<=shape[0]<=1200 or a.ndim!=2 or a.shape!=(3*shape[0],a.shape[1])
            or a.shape[1] not in (26,27) or b.shape!=a.shape or sd.shape!=(a.shape[0],)
            or np.any(sd<=0) or len(boundaries)!=2
            or any(v.dtype!=np.dtype('float64') or not np.all(np.isfinite(v)) for v in arrays.values())
            or any(arrays[k].shape!=shape for k in ('candidate_coordinates','reference_difference','candidate_difference'))):
        raise ValueError('complete finite values and all 26/27 derivative columns required')
    identical=lambda x,y:x.dtype==y.dtype and x.shape==y.shape and x.tobytes()==y.tobytes()
    values=identical(arrays['reference_coordinates'],arrays['candidate_coordinates'])
    differences=identical(arrays['reference_difference'],arrays['candidate_difference'])
    a,b=a/sd[:,None],b/sd[:,None];error=abs(a-b);allowed=2e-10+2e-10*abs(b)
    jac=bool(np.all(error<=allowed));same_boundary=boundaries[0]==boundaries[1]
    return dict(passed=bool(values and differences and jac and same_boundary),values_bitwise_identical=values,
        differences_bitwise_identical=differences,jacobian_within_tolerance=jac,boundary_counts_identical=same_boundary,
        maximum_normalized_jacobian_difference=float(error.max()),violating_jacobian_entries=int(np.count_nonzero(error>allowed)),
        relative_tolerance=2e-10,absolute_tolerance=2e-10)


def calculate(spec,r,*,kernel_factory,reserve,reserve_construction,save,save_bytes,check_continue):
    import io
    import time
    import numpy as np
    from lll.airquantumgrav_training_controls import generated_training,training_covariance,_spec
    from lll.airquantumgrav_observation_truth import receiver_samples
    from lll.ilvis0_training_forecast import training_problem
    from lll.ilvis0_wide_tangent import evaluate
    from lll.studies.artifacts import digest
    material=generated_training(spec,r,reserve=reserve_construction,height_profile='climb',gravity_model='inverse_square_height')
    times=material['times'];n=len(material['dt']);reserve_construction(generated_samples=len(times))
    arguments,sign=_spec(spec)
    answer=receiver_samples(times=times,sign=sign,**arguments,height_profile='climb',gravity_model='inverse_square_height')
    anchor=float(answer['coordinates'][0,2]);check_continue()
    base=training_problem(times,answer['coordinates'],**{k:material[k] for k in ('theta','dv','dt')},
        covariance=training_covariance(answer['coordinates'],spec['model'],sigma_m=r['training_sigma_m']),
        model=spec['model'],limits=r['limits'],profile=spec['profile'],clock='header_elapsed',
        maximum_interval_s=1.5/r['rate_hz'],kernel=None,tangent_kernel=None)
    point=np.linspace(-.02,.02,len(base.bounds.active));kernels,compilation=kernel_factory(anchor)
    save('compilation.json',compilation);arrays=dict(standard_deviation=np.diag(base.cholesky).copy());timing={};bounds={}
    hashes=lambda:{k:digest(np.asarray(material[k],dtype='<f8').tobytes()) for k in ('theta','dv','dt','times')}
    before=hashes();order=['candidate','reference'] if spec['profile'] else ['reference','candidate']
    for name in order:
        check_continue();reserve(native_calls=1,packet_visits=n*len(times));cpu=time.process_time_ns();wall=time.monotonic_ns()
        out,delta,jac,boundaries=evaluate(base,point,spec['model'],kernel=kernels[name])
        timing[name]=dict(cpu_s=(time.process_time_ns()-cpu)/1e9,wall_s=(time.monotonic_ns()-wall)/1e9)
        arrays.update({name+'_coordinates':out,name+'_difference':delta,name+'_jacobian':jac});bounds[name]=boundaries
    if hashes()!=before:raise ValueError('generated arrays changed during comparison')
    tested=checks(arrays,boundaries=[bounds['reference'],bounds['candidate']]);buffer=io.BytesIO()
    np.savez_compressed(buffer,**arrays);save_bytes('comparison.npz',buffer.getvalue())
    save('comparison.json',dict(checks=tested,timing=timing,boundaries=bounds,order=order,
        active_parameters=list(base.bounds.active),normalized_point=point.tolist(),input_sha256=before,
        raw_arrays_unchanged=True,native_packets=n,query_epochs=len(times),gravity_anchor_height_m=anchor))
    return dict(**spec,passed=tested['passed'],checks=tested,timing=timing,raw_arrays_unchanged=True,
        active_columns=len(base.bounds.active),native_calls=2,packet_visits=2*n*len(times),
        optimizer_starts=0,original_reads=0,protected_reads=0,scientific_decision='abstain')


def evaluate(task,context):
    import json
    from lll.airquantumgrav_inventory import environment
    from lll.ilvis0_control_shards import _check_continue
    from lll.studies.journal import Journal
    from lll.studies.artifacts import digest
    from lll import ilvis0_wide_tangent as reference
    from lll.ilvis0_mixed_tangent import load
    from pathlib import Path
    read=lambda key:json.loads(context.input_path(key).read_bytes());r=recipe()
    if (read('recipe')!=r or read('qualification-environment')!=environment() or context.manifest['scope']!=SCOPE
            or {t['identity']:t for t in tasks()}.get(task['identity'])!={k:v for k,v in task.items() if k not in ('index','shard')}
            or read('prototype-proof')['verified'] is not True or read('prototype-proof')['tests_passed']!=9):
        raise ValueError('unchanged finite scope and verified short prototype gate required')
    counts=construction_limits(r);journal=Journal(context.directory/'construction.sqlite',
        freeze=digest((context.root/'manifest.json').read_bytes()),limits={task['identity']:counts});journal.start(task['identity'])
    try:
        def check():_check_continue(context.root,context.manifest)
        def reserve(**work):
            check()
            for key,value in work.items():journal.reserve(task['identity'],key,value)
        directory=context.root/'shards'/f'{context.shard:03d}'/'kernels'
        source=context.manifest['sources']['analysis/lll/ilvis0_tangent.cpp']
        loader=context.manifest['sources']['analysis/lll/ilvis0_wide_tangent.py']
        def factory(anchor):
            a,am=reference.load(directory,gravity_anchor_height_m=anchor,expected_source_sha256=source)
            b,bm=load(directory,gravity_anchor_height_m=anchor,expected_source_sha256=source,expected_loader_sha256=loader)
            for key,metadata in (('reference',am),('candidate',bm)):
                binary=directory/('wide-tangent-'+metadata['source_sha256']+'.so')
                context.save_bytes(key+'-kernel.bin',binary.read_bytes())
            return dict(reference=a,candidate=b),dict(reference=am,candidate=bm)
        result=calculate(task['payload'],r,kernel_factory=factory,reserve=context.charge,reserve_construction=reserve,
            save=context.save,save_bytes=context.save_bytes,check_continue=check)
        journal.verify()
        if any(journal.count(task['identity'],key)!=value for key,value in counts.items()):raise ValueError('construction charges differ')
        return result
    finally:context.note_file(journal.path)


def inspect(root,prefix='data/mixed-tangent-long-controls-20261024'):
    from lll.studies.closed import ClosedStudy
    study=ClosedStudy(root,prefix)
    try:
        import io
        import numpy as np
        from lll.airquantumgrav_geographic_report import construction_counts
        from lll.airquantumgrav_observation_report import native_accounting
        from lll.studies.source_binding import verify
        from lll.airquantumgrav_inventory import environment
        from lll.studies.artifacts import encoded,digest
        from lll import ilvis0_wide_tangent as reference
        from lll.ilvis0_mixed_tangent import derive as mixed_derive,VERSION as MIXED_VERSION
        r=study.input('recipe')
        if r!=recipe() or study.input('qualification-environment')!=environment() or study.manifest['scope']!=SCOPE:
            raise ValueError('unchanged qualified fixed-point benchmark required')
        verify(root,declared=study.input('qualification-request')['sources'],manifest=study.manifest['sources'])
        proof=study.input('prototype-proof');parent_request=study.input('prototype-request',raw=True)
        parent_tests=study.input('prototype-tests',raw=True)
        import json
        parent=json.loads(parent_request)
        if (proof['verified'] is not True or proof['tests_passed']!=9 or proof['request_sha256']!=digest(parent_request)
                or proof['report_sha256']!=digest(parent_tests)
                or any(study.manifest['sources'].get(k)!=v for k,v in parent['sources'].items())):
            raise ValueError('short qualification source or report binding differs')
        if {k:{a:b for a,b in v.items() if a not in ('index','shard')} for k,v in study.tasks.items()}!={v['identity']:v for v in tasks()}:
            raise ValueError('complete six-case matrix required')
        ops=native_accounting(study.read('shards/000/charges/journal.sqlite',raw=True),
            study.completion['manifest_sha256'],set(study.tasks),per_call_visits=None)
        source='analysis/lll/ilvis0_tangent.cpp';raw=study.read('source-freeze/'+source,study.manifest['sources'][source],raw=True)
        wide_source=reference.derive(raw,expected_sha256=study.manifest['sources'][source])
        derived={'reference':wide_source,'candidate':mixed_derive(wide_source,expected_sha256=digest(wide_source))}
        rows=[];totals={k:0 for k in study.summary['charged']}
        for identity,task in study.tasks.items():
            if identity not in study.rows:rows.append(dict(identity=identity,complete=False));continue
            envelope=study.envelope(identity);result=envelope['result'];row=dict(identity=identity,complete='checks' in result,result=result)
            for k in totals:totals[k]+=envelope['charged'][k]
            for name,sha in envelope['artifacts'].items():study.read(name,sha,raw=True)
            if row['complete']:
                descriptor=study.artifact(identity,'comparison.json')
                with np.load(io.BytesIO(study.artifact(identity,'comparison.npz',raw=True)),allow_pickle=False) as archive:
                    arrays={key:archive[key] for key in archive.files}
                tested=checks(arrays,boundaries=[descriptor['boundaries'][k] for k in ('reference','candidate')])
                counts=construction_counts(study.artifact(identity,'construction.sqlite',raw=True),
                    study.completion['manifest_sha256'],identity,construction_limits(r))
                if (encoded(tested)!=encoded(result['checks']) or encoded(tested)!=encoded(descriptor['checks'])
                        or any(result[k]!=v for k,v in task['payload'].items())
                        or result['passed']!=tested['passed'] or ops[identity]['value'] or ops[identity]['tangent']!=2
                        or ops[identity]['packet_visits']!=864000000 or result['native_calls']!=2
                        or envelope['charged']['native_calls']!=2 or envelope['charged']['packet_visits']!=864000000
                        or descriptor['query_epochs']!=1200 or descriptor['native_packets']!=360000
                        or arrays['reference_jacobian'].shape!=(3600,26+int(task['payload']['profile']))
                        or result['active_columns']!=26+int(task['payload']['profile'])
                        or descriptor['normalized_point']!=np.linspace(-.02,.02,result['active_columns']).tolist()
                        or descriptor['order']!=(['candidate','reference'] if task['payload']['profile'] else ['reference','candidate'])
                        or encoded(descriptor['timing'])!=encoded(result['timing'])
                        or not descriptor['raw_arrays_unchanged'] or not result['raw_arrays_unchanged']
                        or any(result[k] for k in ('optimizer_starts','original_reads','protected_reads'))):
                    raise ValueError('saved benchmark checks, columns or charges differ')
                for key in ('reference','candidate'):
                    metadata=study.artifact(identity,'compilation.json')[key];sha=digest(derived[key])
                    binary=study.artifact(identity,key+'-kernel.bin',raw=True)
                    if (metadata['source_sha256']!=sha or metadata['binary_sha256']!=digest(binary)
                            or metadata['original_source_sha256']!=study.manifest['sources'][source]
                            or metadata['internal_mantissa_bits']<=53
                            or metadata['flags']!=['-O2','-std=c++17','-fPIC','-shared']
                            or metadata['compiler']!=study.input('qualification-environment')['compilers']['c++']
                            or metadata['gravity_anchor_height_m']!=descriptor['gravity_anchor_height_m']
                            or metadata['packet_clock_changed'] is not False
                            or metadata['residual_subtraction']!='before-binary64-cast'
                            or any(metadata[k]!='binary64-frozen' for k in ('clock_dispatch','profile_mapping','query_fraction','parameter_products'))
                            or metadata['version']!=(reference.VERSION if key=='reference' else MIXED_VERSION)):
                        raise ValueError('compiled arithmetic source, ABI or environment differs')
                    if key=='candidate' and (metadata['shared_loader_source_sha256']!=study.manifest['sources']['analysis/lll/ilvis0_wide_tangent.py']
                            or metadata['production_method_changed'] or not metadata['shared_loader_unchanged']):
                        raise ValueError('private shared-loader binding differs')
                    t=descriptor['timing'][key]
                    if any(not math.isfinite(t[k]) or t[k]<=0 for k in ('cpu_s','wall_s')):raise ValueError('positive measured times required')
                row['cpu_speed_ratio']=descriptor['timing']['reference']['cpu_s']/descriptor['timing']['candidate']['cpu_s']
            rows.append(row)
        if totals!=study.summary['charged']:raise ValueError('whole-study charges differ')
        return dict(verified=True,rows=rows,total=6,complete=sum(v['complete'] for v in rows),
            qualified=len(rows)==6 and all(v['complete'] and v['result']['passed'] for v in rows),
            elapsed_s=study.summary['elapsed_s'],charged=study.summary['charged'],
            manifest_sha256=study.completion['manifest_sha256'],summary_sha256=study.completion['summary_sha256'],
            optimizer_starts=0,original_reads=0,protected_reads=0,scientific_decision='abstain')
    finally:study.close()
