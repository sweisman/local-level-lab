# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite nonlinear witnesses for the original generated training observations."""


def recipe():
    return dict(packets=96000,training_s=[2.,10.,30.,180.,290.],future_s=438.,
        search_batches=32,verification_batches=1,maximum_identity_seconds=1800.,
        training_allowance_m=1.,targets_m=[20.,20.,50.],numerical_error_m=1e-5,
        numerical_error_bound_qualified=False,future_observations_used=False,
        original_reads=0,physical_columns=27)


def validate_recipe(value):
    if value!=recipe():raise ValueError('unchanged original fixture and finite nonlinear search required')


def case_matrix(tasks):
    result={}
    for task in tasks:
        spec=task['payload'];key=(spec['model'],spec['profile'])
        if (type(key[0]) is not int or type(key[1]) is not bool or key in result
                or key[0] not in (0,1,2)):
            raise ValueError('distinct candidate and processing identities required')
        result[key]=task
    if set(result)!={(m,p) for m in range(3) for p in (False,True)}:
        raise ValueError('all six original candidate/processing cases required')
    return result


def validate_bundle(bundle,case,spec):
    from lll.ilvis0_receipt_journal import digest
    from lll.ilvis0_truth_probes import audit_pair
    settings=recipe();problem=bundle['problem'];config=case['configuration']
    binding=problem['binding'];records=bundle['initial_records'];initial=bundle['initial']
    if (len(records)!=5 or any(len(case[k])!=settings['packets'] for k in ('theta','dv','dt'))
            or (config['model'],config['profile'])!=(spec['model'],spec['profile'])
            or (binding['model'],binding['profile'])!=(spec['model'],spec['profile'])
            or binding['configuration_sha256']!=digest(config) or config['limits'][25]!=1.
            or problem['training_s']!=settings['training_s'] or problem['future_s']!=settings['future_s']
            or problem['allowance_m']!=[[settings['training_allowance_m']]*3]*5
            or problem['targets_m']!=settings['targets_m']
            or problem['numerical_error_m']!=[settings['numerical_error_m']]*3
            or problem['physical_lower']!=[-1.]*27 or problem['physical_upper']!=[1.]*27
            or type(spec['sign']) is not int or spec['sign'] not in (-1,1)
            or any(r['status']!=0 or r['point']!=initial or r['time_s']!=t
                for r,t in zip(records,settings['training_s'],strict=True))):
        raise ValueError('unchanged full history, calibration, clock and actual training observations required')
    # Only the five saved earlier predictions enter this initial feasibility check.
    record=dict(binding=binding,times_s=settings['training_s']+[settings['future_s']],
        point=initial,prediction=[r['prediction'] for r in records]+[[0.,0.,0.]],status=0)
    if not all(audit_pair(problem,record,record)['training_feasible']):
        raise ValueError('saved initial calibration must fit the original perturbed observations')
    return problem


def closed_cases(root,parent):
    import json
    from lll.studies.artifacts import ArchiveStore,digest as byte_hash,safe_path
    from lll.ilvis0_receipt_journal import digest
    store=ArchiveStore(root);catalog=store.catalog()
    def read(name,expected=None):
        safe_path(root,parent+'/'+name)
        raw=store._read(parent+'/'+name,catalog)
        if expected is not None and byte_hash(raw)!=expected:raise ValueError('closed parent hash mismatch')
        return json.loads(raw),raw
    completion,_=read('completion.json')
    manifest,_=read('manifest.json',completion['manifest_sha256'])
    summary,_=read('summary.json',completion['summary_sha256'])
    if summary['completed']!=6 or len(summary['results'])!=6:
        raise ValueError('six closed original cases required')
    matrix=case_matrix(manifest['tasks']);rows={r['identity']:r for r in summary['results']}
    if set(rows)!={t['identity'] for t in manifest['tasks']}:
        raise ValueError('complete distinct original results required')
    out=[];settings=recipe()
    for (model,profile),task in sorted(matrix.items()):
        identity=task['identity'];row=rows[identity]
        envelope,_=read(row['artifact'],row['artifact_sha256']);result=envelope['result']
        if (envelope['manifest_sha256']!=completion['manifest_sha256']
                or envelope['identity']!=identity or result.get('numerical_checks_passed') is not True
                or result['packets']!=settings['packets']):
            raise ValueError('numerically checked complete original history required')
        def artifact(name):
            path='artifacts/'+identity+'/'+name
            return read(path,envelope['artifacts'][path])[0]
        original=manifest['inputs'][task['input_key']]
        old,_=read(original['path'],original['sha256'])
        if (old['packets']!=settings['packets'] or old['training_s']!=settings['training_s']
                or old['future_s']!=settings['future_s'] or old['noise_allowance_m']!=1.
                or old['width_target_m']!=settings['targets_m']):
            raise ValueError('original training problem changed')
        observed=artifact('training-observations.json')
        if (observed['times_s']!=settings['training_s'] or observed['allowance_m']!=1.
                or observed['future_observations_used'] is not False):
            raise ValueError('original perturbed observations required')
        source_case=manifest['inputs'][task['payload']['case_key']]
        case,case_bytes=read(source_case['path'],source_case['sha256'])
        problem=dict(binding=dict(case_sha256=source_case['sha256'],
            source_sha256=manifest['sources']['analysis/lll/ilvis0_tangent.cpp'],
            configuration_sha256=digest(case['configuration']),model=model,profile=profile),
            training_s=settings['training_s'],future_s=settings['future_s'],
            observations=observed['observations'],allowance_m=[[1.]*3]*5,
            numerical_error_m=[settings['numerical_error_m']]*3,targets_m=settings['targets_m'],
            coordinate_scale=task['payload']['coordinate_scale'],physical_lower=[-1.]*27,
            physical_upper=[1.]*27,future_observations_used=False)
        bundle=dict(problem=problem,initial=old['truth'],
            initial_records=[artifact(f'native-{i:02d}.json') for i in range(1,6)],
            provenance=dict(parent=parent,manifest_sha256=completion['manifest_sha256'],
                result_sha256=row['artifact_sha256'],original_case=source_case,
                training_artifact_sha256=envelope['artifacts']['artifacts/'+identity+'/training-observations.json']))
        spec=dict(model=model,profile=profile,sign=1,compiler=task['payload']['compiler'])
        validate_bundle(bundle,case,spec)
        out.append(dict(model=model,profile=profile,bundle=bundle,case_bytes=case_bytes,
            compiler=spec['compiler']))
    return out


def prepare(root,identity='ilvis0-nonlinear-witnesses-20261022'):
    from pathlib import Path
    from lll.ilvis0_receipt_journal import encoded,durable_write
    from lll.studies.artifacts import safe_path
    from lll.studies.dependencies import source_closure
    from lll.studies.runtime import Definition
    from lll.ilvis0_prediction_publication import inspect
    root=Path(root).resolve()
    prior=inspect(root,'data/ilvis0-long-remainder-feasibility-20261022')
    if prior['completed']!=6 or prior['numerical_checks']!=6:
        raise ValueError('close the complete remainder comparison before successor preparation')
    records=closed_cases(root,'data/ilvis0-long-staged-feasibility-v2-20261021')
    adapter='analysis/lll/ilvis0_witness_search.py'
    sources=source_closure(root,[adapter,'analysis/lll/ilvis0_tangent.cpp',
        'analysis/tests/test_ilvis0_witness_search.py','analysis/tests/test_ilvis0_truth_probes.py',
        'analysis/tests/test_ilvis0_native_box_bounds.py','analysis/tests/test_study_dependencies.py',
        'docs/ilvis0-nonlinear-witnesses/PLAN.md'])
    expected=records[0]['bundle']['problem']['binding']['source_sha256']
    from lll.studies.artifacts import digest as byte_hash
    if byte_hash((root/'analysis/lll/ilvis0_tangent.cpp').read_bytes())!=expected:
        raise ValueError('native source differs from the independently checked original')
    base=safe_path(root,'data/ilvis0-source-point-development/witness-search-inputs')
    if base.exists() or safe_path(root,'data/'+identity).exists():
        raise ValueError('successor preparation must have a fresh identity and input directory')
    base.mkdir(parents=True);inputs={};tasks=[]
    def save(key,value,raw=False):
        path=base/(key+'.json');durable_write(path,value if raw else encoded(value))
        inputs[key]=path.relative_to(root).as_posix()
    save('recipe',recipe())
    for record in records:
        model=record['model'];profile=record['profile'];name=f'{model}-{int(profile)}'
        save('case-'+name,record['case_bytes'],raw=True);save('bundle-'+name,record['bundle'])
        for sign in (-1,1):
            tasks.append(dict(identity=f'witness-{name}-'+('negative' if sign<0 else 'positive'),input_key='recipe',
                limits=dict(native_calls=33,packet_visits=33*6*96000,bound_calls=0,bound_steps=0),
                payload=dict(model=model,profile=profile,sign=sign,compiler=record['compiler'],
                    bundle_key='bundle-'+name,case_key='case-'+name)))
    definition=dict(id=identity,adapter=adapter,sources=sources,inputs=inputs,tasks=tasks,
        workers=4,threads=1,maximum_wall_s=3600.)
    durable_write(base/'definition.json',encoded(definition))
    manifest=Definition.from_dict(definition,root).prepare(root)
    return dict(path='data/'+identity,identities=len(tasks),sources=len(manifest['sources']),
        limits=manifest['limits'],allocation=manifest['allocation'])


def evaluate(task,context):
    import time
    import numpy as np
    from lll import ilvis0_control_shards as runner
    from lll.ilvis0_density_native_probes import query
    from lll.ilvis0_shape import load_tangent
    from lll.ilvis0_sharded_native import plain
    from lll.ilvis0_truth_probes import audit_pair,search_witness
    started=time.monotonic();settings=runner._load(context.input_path());validate_recipe(settings)
    spec=task['payload'];bundle=runner._load(context.input_path(spec['bundle_key']))
    path=context.input_path(spec['case_key']);case=runner._load(path)
    source=context.manifest['sources']['analysis/lll/ilvis0_tangent.cpp']
    if (bundle['problem']['binding']['case_sha256']!=context.manifest['inputs'][spec['case_key']]['sha256']
            or runner._sha(path)!=bundle['problem']['binding']['case_sha256']
            or bundle['problem']['binding']['source_sha256']!=source):
        raise ValueError('original case and native source bindings changed')
    problem=validate_bundle(bundle,case,spec)
    directory=context.root/'shards'/f'{context.shard:03d}'/'kernels';directory.mkdir(parents=True,exist_ok=True)
    kernel,metadata=load_tangent(directory)
    if metadata['compiler']!=spec['compiler'] or metadata['source_sha256']!=source:
        raise ValueError('frozen compiler or native source changed')
    context.save('kernel.json',metadata)
    config={k:np.ascontiguousarray(v,float) if k in ('initial_c','initial_v','initial_r','limits') else v
        for k,v in case['configuration'].items()}
    theta,dv,dt=(np.ascontiguousarray(case[k],float) for k in ('theta','dv','dt'))
    times=settings['training_s']+[settings['future_s']];calls=0
    def reserve():
        nonlocal calls
        runner._check_continue(context.root,context.manifest)
        if (time.monotonic()-started>=settings['maximum_identity_seconds']
                or calls>=settings['search_batches']+settings['verification_batches']):
            raise runner.BudgetStopped('fixed nonlinear-witness allowance exhausted')
        context.charge(native_calls=1,packet_visits=len(times)*len(dt));calls+=1
    def accounting(count,visits):
        if count!=len(times) or visits!=len(times)*len(dt):
            raise ValueError('native work differs from its advance reservation')
    def oracle(point):
        return query(kernel,config,theta,dv,dt,times,point,accounting,
            lambda record:context.save(f'native-raw-{calls:03d}.json',plain(record)))
    def save(kind,record):context.save(f'{kind}-{record["index"]:03d}.json',plain(record))
    result=search_witness(problem,bundle['initial'],oracle,sign=spec['sign'],
        max_queries=settings['search_batches'],reserve=reserve,save=save)
    context.save('selected-before-verification.json',result)
    reserve()
    context.save('verification-point.json',dict(point=result['best_point'],saved_before_native=True))
    replay=oracle(result['best_point'])
    context.save('verification-output.json',plain(replay))
    if (replay['status']!=0 or not replay['classification']['counter_verified']
            or not np.array_equal(replay['prediction'],result['best_record']['prediction'])
            or calls!=result['native_queries']+1):
        raise ValueError('selected native witness failed its separately charged replay')
    record=dict(result['best_record'],prediction=replay['prediction'].tolist())
    audit=audit_pair(problem,record,record)
    if not all(audit['training_feasible']):raise ValueError('selected witness failed exact training audit')
    context.save('verified-witness.json',dict(problem=problem,record=record,audit=audit,
        source_hashes_verified=True,bitwise_native_replay=True))
    return dict(identity=task['identity'],passed=True,model=spec['model'],profile=spec['profile'],
        sign=spec['sign'],native_evaluations=calls,search_batches=result['native_queries'],
        optimizer_success=result['optimizer_success'],stopping_reason=result['stopping_reason'],
        training_margin_exact=audit['training_margin_exact'][0],bitwise_native_replay=True,
        physical_parameter_count=27,future_observations_used=False,source_hashes_verified=True,
        outer_bound_qualified=False,numerical_error_bound_qualified=False,
        observational_coverage_qualified=False,original_reads=0,scientific_decision='abstain')


def check_reference(source,output,times):
    """Additional queries must preserve every original represented epoch value."""
    table=dict(zip(times,output['prediction'],strict=True))
    if len(table)!=len(times):raise ValueError('distinct fixed prediction times required')
    if any(t not in table or table[t]!=value for t,value in
            zip(source['times_s'],source['prediction'],strict=True)):
        raise ValueError('original sparse epoch values changed')


def evaluate_fixed(task,context):
    """Shared, single-batch evaluator for frozen calibration points; no fitting."""
    import time
    import numpy as np
    from lll import ilvis0_control_shards as runner
    from lll.ilvis0_shape import load_tangent
    from lll.ilvis0_density_native_probes import query
    from lll.ilvis0_sharded_native import plain
    from lll.ilvis0_truth_probes import audit_pair
    started=time.monotonic();settings=runner._load(context.input_path());spec=task['payload']
    bundle=runner._load(context.input_path(spec['bundle_key']))
    source=runner._load(context.input_path(spec['point_key']))['record'];times=settings['times_s']
    path=context.input_path(spec['case_key']);case=runner._load(path)
    expected=context.manifest['sources']['analysis/lll/ilvis0_tangent.cpp']
    if (bundle['problem']['binding']['case_sha256']!=context.manifest['inputs'][spec['case_key']]['sha256']
            or runner._sha(path)!=bundle['problem']['binding']['case_sha256']
            or bundle['problem']['binding']['source_sha256']!=expected):
        raise ValueError('unchanged source case required')
    problem=validate_bundle(bundle,case,dict(spec,sign=1))
    if not all(audit_pair(problem,source,source)['training_feasible']):
        raise ValueError('fixed calibration fails original observed constraints')
    def check():
        runner._check_continue(context.root,context.manifest)
        if time.monotonic()-started>=settings['maximum_identity_seconds']:
            raise runner.BudgetStopped('fixed prediction clock allowance exhausted')
    check();directory=context.root/'shards'/f'{context.shard:03d}'/'kernels';directory.mkdir(parents=True,exist_ok=True)
    kernel,metadata=load_tangent(directory)
    if metadata['source_sha256']!=expected or metadata['compiler']!=spec['compiler']:
        raise ValueError('frozen native source or compiler changed')
    context.save('kernel.json',metadata)
    config={k:np.ascontiguousarray(v,float) if k in ('initial_c','initial_v','initial_r','limits') else v
        for k,v in case['configuration'].items()}
    theta,dv,dt=(np.ascontiguousarray(case[k],float) for k in ('theta','dv','dt'))
    if len(dt)!=settings['packets']:raise ValueError('unchanged complete packet history required')
    check();visits=len(times)*len(dt);context.charge(native_calls=1,packet_visits=visits)
    context.save('point-before-native.json',dict(point=source['point'],saved_before_native=True))
    def accounting(count,work):
        if (count,work)!=(len(times),visits):raise ValueError('native work differs from advance reservation')
    native=query(kernel,config,theta,dv,dt,times,source['point'],accounting,
        lambda raw:context.save('native-raw.json',plain(raw)))
    context.save('native-output.json',plain(native))
    if native['status']!=0 or not native['classification']['counter_verified']:
        raise ValueError('successful classified fixed prediction required')
    check_reference(source,plain(native),times)
    context.save('reference-check.json',dict(original_epochs=len(source['times_s']),bitwise_match=True))
    return dict(identity=task['identity'],passed=True,model=spec['model'],profile=spec['profile'],role=spec['role'],
        native_evaluations=1,epochs=len(times),packet_visits=visits,source_hashes_verified=True,
        original_epochs_bitwise_match=True,physical_parameter_count=27,optimizer_starts=0,
        future_observations_used=False,observational_coverage_qualified=False,
        numerical_error_bound_qualified=False,original_reads=0,scientific_decision='abstain')
