# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bounded long-history reuse comparison; no aircraft observations or refits."""
import ast
import json
from pathlib import Path


def recipe():
    return dict(identities=6,packets=96000,times_s=[290.,438.],workers=4,threads=1,
        maximum_cold_seconds=7200.,maximum_batch_seconds=14400.,maximum_wall_s=86400.,
        maximum_rss_bytes=1536*1024**2,oracle_arithmetic_allowance_m=1e-5,
        original_reads=0,optimizer_starts=0)


def batch_limits(n):
    return dict(preparation_packets=n,force_profile_packets=2*n,packet_steps=2*n,
        prefix_packet_steps=n,tail_packet_steps=2*n,cursor_copies=2,
        source_state_copies=6,source_query_checks=6)


def limits(*,reused_early=False):
    if type(reused_early) is not bool:raise ValueError('explicit early-reference policy required')
    return dict(reference_setups=1,conditional_proofs=1,exact_supports=6,
        reused_cold_reports=1+int(reused_early),cold_bound_queries=int(not reused_early),native_queries=2,
        report_comparisons=2,design_comparisons=2,**batch_limits(recipe()['packets']))


def validate_early_reference(record,certificate):
    """Check a sealed, complete original answer before allowing a saved read.

    ClosedStudy verifies the parent completion, envelope and artifact hashes at
    acquisition. The worker checks this binding again; compare separately checks
    the complete physical domain, expansion and reconstructed proof.
    """
    import math
    from lll.studies.artifacts import digest,encoded
    keys=('case_sha256','material_sha256','conditioning_sha256','reference_sha256',
        'original_cold_sha256','wrapper_sha256','compiler','environment')
    try:
        valid=(all(record['certificate'][k]==certificate[k] for k in keys)
            and all(isinstance(record.get(k),str) and record[k] for k in ('parent','manifest_sha256','result_sha256'))
            and record['report_sha256']==digest(encoded(record['report']))
            and record['report']['time_s']==recipe()['times_s'][0]
            and math.isfinite(record['work']['elapsed_s'])
            and 0<=record['work']['elapsed_s']<=recipe()['maximum_cold_seconds']
            and type(record['work']['peak_rss_bytes']) is int
            and 0<record['work']['peak_rss_bytes']<=recipe()['maximum_rss_bytes'])
    except (KeyError,TypeError,ValueError):valid=False
    if not valid:raise ValueError('saved early reference source/proof/time/resource binding differs')
    return record['report']


def early_from_study(study,identity,certificate,*,expected_adapter_sha):
    """Acquire an original cold answer, even if later bookkeeping failed.

    Successful numerical qualification is not inherited from the failed study.
    Only the complete, independently bound original answer is reused.
    """
    from lll.studies.closed import ClosedStudy
    from lll.studies.artifacts import digest,encoded
    adapter='analysis/lll/ilvis0_native_prefix_long.py'
    if (not isinstance(study,ClosedStudy) or study.manifest.get('adapter')!=adapter
            or study.manifest['sources'].get(adapter)!=expected_adapter_sha
            or study.manifest['environment']!=certificate['environment']):
        raise ValueError('early reference source or environment differs')
    study.read('source-freeze/'+adapter,expected_adapter_sha,raw=True)
    if digest(study.input('cold',raw=True))!=certificate['original_cold_sha256']:
        raise ValueError('early reference original source differs')
    if identity not in study.rows:return None
    envelope=study.envelope(identity);name='artifacts/'+identity+'/cold-00.json'
    charged=envelope['charged']
    if name not in envelope['artifacts']:
        if charged['bound_calls'] or charged['native_calls']:
            raise ValueError('charged early reference is incomplete; no retry in bookkeeping repair')
        return None
    if charged!=dict(native_calls=0,packet_visits=0,bound_calls=1,bound_steps=9*recipe()['packets']):
        raise ValueError('early reference original-call accounting differs')
    report=study.artifact(identity,'cold-00.json')
    record=dict(report=report,report_sha256=digest(encoded(report)),
        work=study.artifact(identity,'cold-work.json'),certificate=study.artifact(identity,'compatibility.json'),
        parent=study.prefix,identity=identity,manifest_sha256=study.completion['manifest_sha256'],
        result_sha256=study.rows[identity]['artifact_sha256'])
    validate_early_reference(record,certificate)
    return record


def compatible_sources(previous,current,old_cold,new_wrapper):
    """Only the replaced orchestration and nonnumerical storage may differ.

    The original orchestration is executed from its sealed bytes. Every helper
    outside enclose remains AST-identical; all other numerical sources match.
    """
    from lll.studies.artifacts import digest
    name='analysis/lll/ilvis0_remainder_native.py'
    if previous.get(name)!=digest(old_cold) or current.get(name)!=digest(new_wrapper):
        raise ValueError('original/wrapper source hash mismatch')
    def helpers(raw):
        tree=ast.parse(raw);tree.body=[v for v in tree.body if not isinstance(v,ast.FunctionDef) or v.name!='enclose']
        return ast.dump(tree,include_attributes=False)
    if helpers(old_cold)!=helpers(new_wrapper):raise ValueError('original cold helpers changed')
    storage={'analysis/lll/studies/artifacts.py','analysis/lll/studies/publication.py'}
    tests={p for p in previous if p.startswith('analysis/tests/test_')}
    ignored=storage|tests|{name};unchanged=[]
    for path,sha in previous.items():
        if path in ignored:continue
        if current.get(path)!=sha:raise ValueError('saved numerical dependency changed: '+path)
        unchanged.append(path)
    return dict(original_cold_sha256=digest(old_cold),wrapper_sha256=digest(new_wrapper),
        unchanged_numerical_dependencies=sorted(unchanged),
        storage_only_changes=sorted(p for p in storage if p in previous and previous[p]!=current.get(p)),
        test_only_changes=sorted(p for p in tests if previous[p]!=current.get(p)))


def validate_saved(value,report,*,time):
    """Bind the reused report to the same full physical domain and proof."""
    import numpy as np
    ref=value['reference_report']
    if (report.get('time_s')!=time or report.get('reference_binding')!=ref['binding']
            or report.get('source_id')!=ref['parent']['source_id']
            or report.get('normalized_center')!=list(value['center'])
            or report.get('lower')!=list(value['lower']) or report.get('upper')!=list(value['upper'])
            or report.get('conditioning')!=value['proof_report']
            or any(np.asarray(report.get(k)).shape!=(3,n) for k,n in
                (('previous_coefficients',6),('acceleration_coefficients',9),('transform_coefficients',9)))):
        raise ValueError('saved cold reference/domain/clock/proof or coefficient columns changed')


def compare(value,saved_report,*,original,prefix_kernels,cold_kernels,tangent,reserve,charge,save,
            maximum_cold_seconds,maximum_batch_seconds,maximum_packet_steps,maximum_rss_bytes,
            checkpoint=lambda:None,saved_early_report=None):
    import ctypes
    import resource
    import time
    import numpy as np
    from lll.ilvis0_native_prefix import enclose_many
    from lll.ilvis0_packet_boundary_flags import validate
    from lll.studies.artifacts import save_phase,reports_equal
    config=value['configuration'];times=value['times'];n=len(value['dt']);r=recipe()
    if len(times)!=2 or times[0]>=times[1]:raise ValueError('two fixed increasing queries required')
    validate_saved(value,saved_report,time=times[1]);reserve(reused_cold_reports=1)
    theta,dv,dt=(np.ascontiguousarray(value[k],float) for k in ('theta','dv','dt'))
    ref=value['reference'];center=np.ascontiguousarray(value['center'],float)
    common=dict(lower=value['lower'],upper=value['upper'],reference=ref,conditioning=value['conditioning'])
    def check_resources():
        checkpoint()
        if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024>maximum_rss_bytes:
            raise ValueError('frozen peak-memory allowance exceeded')
    check_resources();started=time.monotonic()
    if saved_early_report is None:
        reserve(cold_bound_queries=1);charge(bound_calls=1,bound_steps=9*n)
        save_phase(save,0,'cold reference',time_s=times[0])
        cold_started=time.monotonic()
        try:
            cold=original.enclose(config,theta,dv,dt,time=times[0],maximum_seconds=maximum_cold_seconds,
                **common,**cold_kernels)
        finally:
            cold_elapsed=time.monotonic()-cold_started
            save('cold-work.json',dict(elapsed_s=cold_elapsed,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024))
        early=cold.report()
        if cold_elapsed>maximum_cold_seconds:raise ValueError('frozen cold time allowance exceeded')
    else:
        validate_saved(value,saved_early_report,time=times[0]);reserve(reused_cold_reports=1)
        save_phase(save,0,'reused cold reference',time_s=times[0])
        early=saved_early_report;cold_elapsed=0.
        save('cold-work.json',dict(elapsed_s=0.,reused=True,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024))
    save('cold-00.json',early)
    save('cold-01-reused.json',saved_report);check_resources()
    expected=[early,saved_report];native=[];jacobians=[]
    for i,t in enumerate(times):
        save_phase(save,1+i,'independent point check',time_s=t)
        reserve(native_queries=1);charge(native_calls=1,packet_visits=n)
        out=np.empty((1,3));jac=np.empty((3,27));flag=ctypes.c_int()
        code=tangent(n,theta,dv,dt,1,np.array([t]),config['initial_c'],config['initial_v'],config['initial_r'],
            config['limits'],center,config['model'],int(config['profile']),config['gravity'],config['radius'],
            out,jac,ctypes.byref(flag))
        boundary=validate(status=int(code),counter=flag.value,dt=dt,time_s=t,
            clock_offset_s=float(config['limits'][25]*center[25]))
        if code or not np.all(np.isfinite(out)) or not np.all(np.isfinite(jac)):
            raise ValueError('independent native point query failed')
        native.append(out[0].copy());jacobians.append(jac.copy())
        save(f'native-{i:02d}.json',dict(time_s=t,point=center.tolist(),prediction=out[0].tolist(),
            jacobian=jac.tolist(),status=int(code),warning=flag.value,boundary=boundary))
        check_resources()
    # Prepay the entire finite batch once. Local work counters enforce the same
    # limits before each step, avoiding hundreds of thousands of fsyncs. An
    # interrupted batch retains the whole reservation, never a refundable balance.
    prepaid=batch_limits(n);prepaid['packet_steps']=maximum_packet_steps
    reserve(**prepaid);charge(bound_calls=1,bound_steps=9*maximum_packet_steps);used={k:0 for k in prepaid}
    def spend(**counts):
        for k,amount in counts.items():
            if k not in used or type(amount) is not int or amount<=0 or used[k]+amount>prepaid[k]:
                raise ValueError('prepaid batch allowance exceeded')
        for k,amount in counts.items():used[k]+=amount
        if 'packet_steps' not in counts or used['packet_steps']%256==0:check_resources()
    batch_started=time.monotonic()
    save_phase(save,3,'batched bounds',times_s=list(times))
    try:
        result=enclose_many(config,theta,dv,dt,times=times,prefix_kernels=prefix_kernels,
            maximum_packet_steps=maximum_packet_steps,reserve=spend,maximum_seconds=maximum_batch_seconds,**common)
    finally:
        batch_elapsed=time.monotonic()-batch_started
        save('batch-progress.json',dict(elapsed_s=batch_elapsed,actual_prepaid_work=used,reservations=prepaid,
            peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024))
    reports=[actual.report() for actual in result['bounds']]
    for i,report in enumerate(reports):save(f'batched-{i:02d}.json',report)
    save('batch-work.json',dict(work=result['work'],actual_prepaid_work=used,reservations=prepaid,binding=result['binding']))
    if batch_elapsed>maximum_batch_seconds:raise ValueError('frozen batch time allowance exceeded')
    check_resources();errors=[]
    scale=np.array([6371000.,6371000.,1.])
    for i,(actual,old,jac,point) in enumerate(zip(result['bounds'],expected,jacobians,native,strict=True)):
        report=reports[i];reserve(report_comparisons=1)
        if not reports_equal(report,old):raise ValueError('complete long report differs from sealed cold reference')
        reserve(design_comparisons=1);design=actual.design(jac,ref)
        expected_design=np.c_[jac,old['previous_coefficients'],old['acceleration_coefficients'],old['transform_coefficients']]
        if design.shape!=(3,51) or not np.array_equal(design,expected_design):
            raise ValueError('physical/shared coefficient design changed')
        error=np.abs((actual.center-point)*scale);errors.append(error.tolist())
        save(f'design-{i:02d}.json',dict(matrix=design.tolist(),native_center_error_m=error.tolist()))
        if float(np.max(error))>r['oracle_arithmetic_allowance_m']:
            raise ValueError('center differs from independent native oracle')
    save_phase(save,4,'complete',elapsed_s=time.monotonic()-started)
    return dict(passed=True,packets=n,model=config['model'],profile=bool(config['profile']),times_s=list(times),
        complete_reports_equal=2,design_columns_checked=51,maximum_native_center_error_m=float(np.max(errors)),
        oracle_arithmetic_allowance_m=r['oracle_arithmetic_allowance_m'],work=result['work'],
        cold_elapsed_s=cold_elapsed,batch_elapsed_s=batch_elapsed,elapsed_s=time.monotonic()-started,
        peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
        native_evaluations=2,bound_evaluations=2-int(saved_early_report is not None),
        reused_cold_reports=1+int(saved_early_report is not None),cold_reference_reused=saved_early_report is not None,
        original_reads=0,optimizer_starts=0,
        long_history_qualified=False,observational_coverage_qualified=False,scientific_decision='abstain')


def restore(material,case,*,reserve):
    import numpy as np
    from lll.ilvis0_coupled_map import restore_static_reference
    from lll.ilvis0_conditioned_acceleration import ConditionedAcceleration
    saved=material['saved'];bundle=material['proof_input'];region=bundle['training']['region']
    if (saved['parameter_count']!=51 or saved['reference']!=bundle['reference']
            or saved['lower']!=region['lower'] or saved['upper']!=region['upper']
            or saved['fixed_center']!=region['center'][:27] or saved['time_s']!=recipe()['times_s'][-1]
            or bundle['lower']!=region['lower'] or bundle['upper']!=region['upper']
            or len(region['inequality_design'])!=30
            or case['configuration']['model']!=material['model']
            or bool(case['configuration']['profile'])!=material['profile']
            or any(len(case[k])!=recipe()['packets'] for k in ('theta','dv','dt'))):
        raise ValueError('unchanged full-history conditioning and source case required')
    config={k:np.ascontiguousarray(v,float) if k in ('initial_c','initial_v','initial_r','limits') else v
        for k,v in case['configuration'].items()}
    lo=np.asarray(region['lower'][:27]);hi=np.asarray(region['upper'][:27])
    reserve(reference_setups=1)
    ref=restore_static_reference(config,case['dv'][0],float(case['dt'][0]),lower=lo,upper=hi,
        center=saved['fixed_center'],expected_report=saved['reference'])
    reserve(conditional_proofs=1)
    proof=ConditionedAcceleration(bundle,material['conditioning_certificate'],reserve=lambda n:reserve(exact_supports=n))
    return dict(configuration=config,theta=case['theta'],dv=case['dv'],dt=case['dt'],center=ref.parent.center,
        lower=lo,upper=hi,reference=ref,conditioning=proof,times=recipe()['times_s'],
        reference_report=ref.report(),proof_report=proof.report())


def prepare(root,identity='ilvis0-native-prefix-long-v2-20261022'):
    import subprocess
    from lll.studies.closed import ClosedStudy
    from lll.studies.artifacts import atomic,encoded,digest,safe_path
    from lll.studies.dependencies import source_closure
    from lll.studies.runtime import Definition
    from lll.ilvis0_control_shards import runtime_environment
    from lll.ilvis0_native_prefix_controls import inspect as inspect_short
    root=Path(root).resolve();prefix='data/'+identity
    base=safe_path(root,'data/ilvis0-source-point-development/'+identity+'-inputs')
    if base.exists() or safe_path(root,prefix).exists():raise ValueError('fresh long-prefix freeze required')
    short=inspect_short(root,'data/ilvis0-native-prefix-controls-v2-20261022')
    if not short['complete']:raise ValueError('complete short qualification required')
    prior=ClosedStudy(root,'data/ilvis0-long-remainder-feasibility-20261022')
    short_study=ClosedStudy(root,'data/ilvis0-native-prefix-controls-v2-20261022',store=prior.store)
    attempt=ClosedStudy(root,'data/ilvis0-native-prefix-long-20261022',store=prior.store)
    try:
        if attempt.summary.get('passed'):raise ValueError('a passed long comparison needs no repair')
        if prior.manifest['environment']!=runtime_environment():raise ValueError('saved numerical environment differs')
        if len(prior.tasks)!=6 or len(prior.rows)!=6:raise ValueError('all six sealed histories required')
        cold_name='analysis/lll/ilvis0_remainder_native.py';sha=prior.manifest['sources'][cold_name]
        cold=prior.read('source-freeze/'+cold_name,sha,raw=True)
        if sha!=short_study.input('recipe')['cold_sha256']:raise ValueError('short and long original references differ')
        # All numeric implementation used by the passed short comparison is
        # identical. Current storage/test/plan additions do not replace it.
        for name,h in short_study.manifest['sources'].items():
            if name.startswith('analysis/lll/') and '/studies/' not in name and digest((root/name).read_bytes())!=h:
                raise ValueError('short-qualified numerical source changed: '+name)
        current={n:digest((root/n).read_bytes()) for n in prior.manifest['sources']}
        compatibility=compatible_sources(prior.manifest['sources'],current,cold,(root/cold_name).read_bytes())
        compatible_sources(prior.manifest['sources'],attempt.manifest['sources'],cold,
            attempt.read('source-freeze/'+cold_name,attempt.manifest['sources'][cold_name],raw=True))
        early_tasks={(t['payload']['model'],t['payload']['profile']):t['identity'] for t in attempt.tasks.values()}
        if set(early_tasks)!={(m,p) for m in range(3) for p in (False,True)}:
            raise ValueError('initial long comparison candidate coverage differs')
        compiler=subprocess.check_output(['c++','--version'],text=True).splitlines()[0]
        base.mkdir(parents=True);atomic(base/'cold.py',cold)
        inputs={'cold':(base/'cold.py').relative_to(root).as_posix()};tasks=[];seen=set();history=[]
        for old_id,task in prior.tasks.items():
            spec=task['payload'];material=prior.input(task['input_key']);case_key=spec['case_key']
            if (spec['packets']!=recipe()['packets'] or spec['future_s']!=recipe()['times_s'][-1]
                    or spec['compiler']!=compiler or material['model']!=spec['model']
                    or material['profile']!=spec['profile']):raise ValueError('fixed six-case history mismatch')
            pair=(spec['model'],spec['profile'])
            if pair in seen:raise ValueError('duplicate model/processing history')
            seen.add(pair);raw=prior.artifact(old_id,'raw-bound.json');compilation=prior.artifact(old_id,'compilation.json')
            for item in compilation.values():
                if item['compiler']!=compiler or any(current.get('analysis/lll/'+n)!=h for n,h in item['sources'].items()):
                    raise ValueError('saved cold compilation differs')
            report=raw['report'];saved=material['saved']
            # Cheap static reconstruction rejects a mismatched proof before any
            # hours-long task is frozen. It performs no packet integration.
            case_bytes=prior.input(case_key,raw=True);preflight_counts={}
            def preflight_reserve(**values):
                for name,n in values.items():preflight_counts[name]=preflight_counts.get(name,0)+n
            value=restore(material,json.loads(case_bytes),reserve=preflight_reserve)
            validate_saved(value,report,time=recipe()['times_s'][-1])
            if preflight_counts!=dict(reference_setups=1,conditional_proofs=1,exact_supports=6):
                raise ValueError('static preparation work differs')
            # This certificate binds source bytes and all numerical prerequisites;
            # the worker independently reconstructs and checks the full proof.
            certificate=dict(compatibility,parent=prior.prefix,parent_manifest_sha256=prior.completion['manifest_sha256'],
                parent_result_sha256=prior.rows[old_id]['artifact_sha256'],environment=prior.manifest['environment'],
                compiler=compiler,case_sha256=prior.manifest['inputs'][case_key]['sha256'],
                material_sha256=prior.manifest['inputs'][task['input_key']]['sha256'],
                saved_report_sha256=digest(encoded(report)),conditioning_sha256=digest(encoded(material['conditioning_certificate'])),
                reference_sha256=digest(encoded(saved['reference'])),saved_elapsed_s=raw['elapsed_s'])
            early=early_from_study(attempt,early_tasks[pair],certificate,
                expected_adapter_sha='a8c8f7109dce5b99f8f1be3b9721ca6706e0f7e53dfc77c07c3c8c4a6db69a68')
            reused=early is not None
            if reused:validate_saved(value,early['report'],time=recipe()['times_s'][0])
            key=f'case-{spec["model"]}-{int(spec["profile"])}';name='prefix-long-'+key
            atomic(base/(key+'.json'),case_bytes)
            atomic(base/(key+'-reference.json'),encoded(dict(material=material,report=report,certificate=certificate,early_reference=early)))
            inputs[key]=(base/(key+'.json')).relative_to(root).as_posix()
            inputs[key+'-reference']=(base/(key+'-reference.json')).relative_to(root).as_posix()
            tasks.append(dict(identity=name,input_key=key,payload=dict(model=spec['model'],profile=spec['profile'],
                reference_key=key+'-reference',recipe=recipe(),reused_early=reused,limits=limits(reused_early=reused)),
                limits=dict(native_calls=2,packet_visits=2*recipe()['packets'],bound_calls=2-int(reused),
                    bound_steps=(27-9*int(reused))*recipe()['packets'])))
            history.append(dict(identity=name,certificate=certificate,early_reference=early))
        if seen!={(m,p) for m in range(3) for p in (False,True)}:raise ValueError('incomplete fixed candidate coverage')
        # With four reusable references, give the two double-task shards only
        # cached cases. The two more expensive fresh-reference cases each get
        # a single-task shard. This changes scheduling, never inputs or outcomes.
        reused_tasks=[t for t in tasks if t['payload']['reused_early']]
        fresh_tasks=[t for t in tasks if not t['payload']['reused_early']]
        if len(reused_tasks)==4:tasks=reused_tasks[:2]+fresh_tasks+reused_tasks[2:]
        atomic(base/'compatibility.json',encoded(dict(cases=history,short_manifest_sha256=short['manifest_sha256'])))
        inputs['compatibility']=(base/'compatibility.json').relative_to(root).as_posix()
        adapter='analysis/lll/ilvis0_native_prefix_long.py'
        seeds=list(prior.manifest['sources'])+[
            adapter,'analysis/lll/ilvis0_source_prefix_reference.cpp','analysis/lll/ilvis0_source_prefix_intervals.cpp',
            'analysis/tests/test_ilvis0_native_prefix_long.py','analysis/tests/test_ilvis0_native_prefix_reuse.py',
            'analysis/tests/test_study_runtime.py','docs/ilvis0-native-prefix-long/V2_PLAN.md']
        sources=source_closure(root,seeds)
        definition=dict(id=identity,adapter=adapter,sources=sources,inputs=inputs,tasks=tasks,
            workers=recipe()['workers'],threads=recipe()['threads'],maximum_wall_s=recipe()['maximum_wall_s'])
        atomic(base/'definition.json',encoded(definition));manifest=Definition.from_dict(definition,root).prepare(root)
        return dict(path=prefix,identities=len(tasks),sources=len(manifest['sources']),allocation=manifest['allocation'],
            limits=manifest['limits'],preparation_definition=(base/'definition.json').relative_to(root).as_posix())
    finally:attempt.close();short_study.close();prior.close()


def evaluate(task,context):
    import subprocess
    from lll.studies.closed import load_python_reference
    from lll.studies.artifacts import digest,encoded
    from lll.studies.journal import Journal
    from lll.ilvis0_control_shards import _check_continue,runtime_environment
    from lll.ilvis0_source_prefix import load_kernels
    from lll.ilvis0_source_stream import load_stream
    from lll.ilvis0_source_derivative_intervals import load_kernel as interval_kernel
    from lll.ilvis0_source_point_derivatives import load_kernel as point_kernel
    from lll.ilvis0_shape import load_tangent
    from lll.ilvis0_batched_transport import configure_backend
    spec=task['payload']
    reused=spec['reused_early'];allowance=limits(reused_early=reused)
    if spec['recipe']!=recipe() or spec['limits']!=allowance:raise ValueError('fixed finite long-prefix recipe required')
    record=json.loads(context.input_path(spec['reference_key']).read_bytes());cert=record['certificate']
    early=record['early_reference']
    if reused!=(early is not None):raise ValueError('frozen early-reference reuse policy differs')
    saved_early=None if early is None else validate_early_reference(early,cert)
    case_bytes=context.input_path().read_bytes();cold=context.input_path('cold').read_bytes()
    if (digest(case_bytes)!=cert['case_sha256'] or digest(encoded(record['report']))!=cert['saved_report_sha256']
            or digest(encoded(record['material']))!=cert['material_sha256']
            or digest(encoded(record['material']['conditioning_certificate']))!=cert['conditioning_sha256']
            or cert['environment']!=runtime_environment() or context.manifest['environment']!=cert['environment']
            or cert['compiler']!=subprocess.check_output(['c++','--version'],text=True).splitlines()[0]
            or context.manifest['sources']['analysis/lll/ilvis0_remainder_native.py']!=cert['wrapper_sha256']):
        raise ValueError('reused cold input, proof, source or numerical environment changed')
    original=load_python_reference(cold,name='lll._sealed_long_prefix_'+cert['original_cold_sha256'][:16],
        sha256=cert['original_cold_sha256'])
    journal_path=context.directory/'allowance.sqlite';journal=Journal(journal_path,
        freeze=digest((context.root/'manifest.json').read_bytes()),limits={task['identity']:allowance})
    journal.start(task['identity'])
    def checkpoint():_check_continue(context.root,context.manifest)
    def reserve(**values):
        checkpoint()
        for key,n in values.items():journal.reserve(task['identity'],key,n)
    try:
        value=restore(record['material'],json.loads(case_bytes),reserve=reserve)
        if value['configuration']['model']!=spec['model'] or bool(value['configuration']['profile'])!=spec['profile']:
            raise ValueError('fixed model/processing identity differs')
        validate_saved(value,record['report'],time=recipe()['times_s'][-1]);context.save('compatibility.json',cert)
        if early is not None:context.save('early-reference.json',early)
        source=context.root/'source-freeze/analysis/lll';directory=context.root/'shards'/f'{context.shard:03d}'/'kernels'
        backend=configure_backend(directory,source_directory=source);prefix,metadata=load_kernels(directory,source_directory=source)
        cold_kernels={}
        for name,loader in (('source_kernel',load_stream),('derivative_kernel',interval_kernel),('point_kernel',point_kernel)):
            kernel,meta=loader(directory,source_directory=source);cold_kernels[name]=kernel;metadata[name]=meta
        metadata['backend']=backend
        for meta in metadata.values():
            if meta['compiler']!=cert['compiler'] or any(context.manifest['sources'].get('analysis/lll/'+name)!=h
                    for name,h in meta['sources'].items()):raise ValueError('compiled long-prefix source differs')
        tangent,tmeta=load_tangent(directory)
        if (tmeta['source_sha256']!=context.manifest['sources']['analysis/lll/ilvis0_tangent.cpp']
                or tmeta['compiler']!=cert['compiler']):raise ValueError('native point oracle differs')
        context.save('compilation.json',dict(components=metadata,tangent=tmeta))
        result=compare(value,record['report'],original=original,prefix_kernels=prefix,cold_kernels=cold_kernels,
            tangent=tangent,reserve=reserve,charge=context.charge,save=context.save,
            maximum_cold_seconds=recipe()['maximum_cold_seconds'],maximum_batch_seconds=recipe()['maximum_batch_seconds'],
            maximum_packet_steps=allowance['packet_steps'],maximum_rss_bytes=recipe()['maximum_rss_bytes'],
            checkpoint=checkpoint,saved_early_report=saved_early)
        counts={k:journal.count(task['identity'],k) for k in allowance}
        if counts!=allowance:raise ValueError('long comparison charged work differs from frozen reservation')
        context.save('accounting.json',counts)
        result=dict(result,identity=task['identity'],charged_auxiliary=counts,
            saved_cold_elapsed_s=cert['saved_elapsed_s'],long_history_qualified=True)
        context.save('long-prefix-checks.json',result);return result
    finally:journal.verify();context.note_file(journal_path)


def inspect(root,prefix):
    from lll.studies.closed import ClosedStudy
    study=ClosedStudy(root,prefix);rows=[]
    try:
        for identity in study.tasks:
            spec=study.tasks[identity]['payload']
            if identity not in study.rows:
                rows.append(dict(identity=identity,model=spec['model'],profile=spec['profile'],
                    passed=False,not_started=True,error_type='Not started',saved_cold_report=False))
                continue
            envelope=study.envelope(identity);row=dict(envelope['result'])
            if row.get('passed'):
                if row!=study.artifact(identity,'long-prefix-checks.json'):raise ValueError('saved result differs')
                for name in ('compatibility.json','accounting.json','compilation.json','batch-work.json','cold-00.json','cold-01-reused.json'):
                    study.artifact(identity,name)
                for i in range(2):
                    for name in ('batched','native','design'):study.artifact(identity,f'{name}-{i:02d}.json')
            if any(k in row and row[k]!=spec[k] for k in ('model','profile')):
                raise ValueError('published candidate differs from frozen identity')
            row.update(identity=identity,model=spec['model'],profile=spec['profile'],not_started=False)
            name='artifacts/'+identity+'/cold-00.json'
            row['saved_cold_report']=name in envelope['artifacts']
            if not row.get('passed') and row['saved_cold_report']:
                study.artifact(identity,'cold-00.json');work=study.artifact(identity,'cold-work.json')
                row.update(cold_elapsed_s=work['elapsed_s'],peak_rss_bytes=work['peak_rss_bytes'])
            rows.append(row)
        complete=len(rows)==6 and {(r.get('model'),r.get('profile')) for r in rows if r.get('passed')}=={
            (m,p) for m in range(3) for p in (False,True)}
        return dict(rows=rows,complete=complete,completed=len(study.rows),not_started=len(study.tasks)-len(study.rows),
            numerical_work=0,manifest_sha256=study.completion['manifest_sha256'],
            summary_sha256=study.completion['summary_sha256'],observational_coverage_qualified=False)
    finally:study.close()


def render(report):
    lines=['# Long-history reuse comparison','',
        'Six fixed generated histories test whether reusing earlier calculations preserves the complete '
        'prediction bounds. These are software controls, not aircraft fits. Queries are at 290 and 438 seconds.',
        '', '| Candidate | Processing | Result | Cold 290 s (s) | Batched two queries (s) | Peak memory (MiB) |',
        '|---|---|---|---:|---:|---:|']
    labels=['Globe + field','Globe, zero field','Stationary disc']
    for r in report['rows']:
        label=labels[r['model']];processing='Profiled removal' if r['profile'] else 'Zero removal'
        if not r.get('passed'):
            status='Not started' if r.get('not_started') else ('Reference saved; comparison stopped' if r.get('saved_cold_report')
                else 'Failed: '+r.get('error_type','incomplete'))
            cold=f"{r['cold_elapsed_s']:.1f}" if r.get('saved_cold_report') else '—'
            memory=f"{r['peak_rss_bytes']/1024**2:.1f}" if 'peak_rss_bytes' in r else '—'
            lines.append('| '+' | '.join([label,processing,status,cold,'—',memory])+' |');continue
        cold='Reused' if r.get('cold_reference_reused') else f"{r['cold_elapsed_s']:.1f}"
        lines.append('| '+' | '.join([label,processing,'Equal',cold,
            f"{r['batch_elapsed_s']:.1f}",f"{r['peak_rss_bytes']/1024**2:.1f}"])+' |')
    lines+=['', '**'+('All six comparisons passed.' if report['complete'] else 'Long-history reuse is not qualified.')+'**',
        '', 'The original 438-second results are reused only after checking their inputs, proof, source code, '
        'numerical dependencies, compiler and environment. A fresh original calculation at 290 seconds '
        'uses the same final conditioning proof. Complete reports and all 51 coefficient columns must agree.',
        '', 'Historical elapsed times are not a controlled same-run speed benchmark. Packet-work counts '
        'and actual peak memory are reported separately. No uncertainty target, physical bound or flight '
        'selection changes to obtain a pass. Whole-record prediction uncertainty remains a separate gate.',
        '', '[Frozen scope](PLAN.md) · [Short controls](../ilvis0-native-prefix-controls/README.md) · '
        '[Prediction gates](../ilvis0-joint-projection-controls/NEXT_PLAN.md)']
    return '\n'.join(lines)+'\n'


def publish(root,prefix,output='docs/ilvis0-native-prefix-long-v2',*,plan='docs/ilvis0-native-prefix-long/V2_PLAN.md'):
    from lll.ilvis0_control_publication import publish as package
    from lll.studies.artifacts import atomic,encoded,digest,safe_path
    from lll.studies.publication import archive_publication
    root=Path(root).resolve();data=safe_path(root,prefix);public=safe_path(root,output)
    if (public/'evidence-receipt.json').exists():raise ValueError('publication already sealed')
    report=inspect(root,prefix);package(data,public,render(report),plan=plan)
    receipt=json.loads((public/'evidence-receipt.json').read_text());name='artifacts/publication/comparison.json'
    raw=encoded(report);atomic(public/name,raw);receipt['artifacts'][name]=digest(raw)
    atomic(public/'evidence-receipt.json',encoded(receipt))
    return dict(archive_publication(root,data,public),published=output,numerical_work=0)
