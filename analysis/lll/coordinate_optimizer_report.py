# SPDX-License-Identifier: AGPL-3.0-or-later
"""Verify saved optimizer controls; never regenerate inputs, fit or propagate."""
import json
from pathlib import Path


def audit_case(study,identity,*,spec,result,r):
    from lll.structured_noisy_publication import CASE_ARTIFACTS
    from lll.structured_noisy_report import check_case
    saved={name:study.artifact(identity,name) for name in CASE_ARTIFACTS}
    checked=check_case(spec,result,saved,r=r)
    passed=bool(checked['converged'] and checked['accurate'])
    if passed!=result['passed']:raise ValueError('numerical/physical pass label changed')
    return saved,dict(checked,passed=passed)


def compare_starts(records):
    import numpy as np
    from lll.airquantumgrav_scoring import receiver_errors
    from lll.ilvis0_solver_position import POLICY
    from lll.ilvis0_solver_refinement import POLICY as STOPPING
    if set(records)!={0,1}:return dict(passed=False,reason='missing_start')
    a,b=records[0],records[1]
    if a['binding']!=b['binding'] or a['training']!=b['training']:
        raise ValueError('matched starts used different measurements or weights')
    if not all(r['fit']['converged'] for r in (a,b)):
        return dict(passed=False,reason='unfinished_fit')
    ca,cb=(r['fit']['residual_sum_squares'] for r in (a,b))
    relative=abs(ca-cb)/max(ca,cb,1.)
    coordinates=a['training']['coordinates'];cut=len(coordinates)
    errors=[receiver_errors(r['forecast']['coordinates'][:cut],coordinates) for r in (a,b)]
    delta=errors[0]-errors[1];rms=np.sqrt(np.mean(delta*delta,axis=0));maximum=np.max(abs(delta),axis=0)
    passed=(relative<=STOPPING['relative_cost_tolerance']
        and np.all(rms<=POLICY['position_rms_tolerance_m']) and np.all(maximum<=POLICY['position_max_tolerance_m']))
    return dict(passed=bool(passed),reason='agreed' if passed else 'start_disagreement',
        relative_cost_difference=relative,training_rms_difference_neu_m=rms.tolist(),
        training_maximum_difference_neu_m=maximum.tolist(),
        relative_cost_limit=STOPPING['relative_cost_tolerance'],
        position_rms_limit_m=POLICY['position_rms_tolerance_m'],position_maximum_limit_m=POLICY['position_max_tolerance_m'])


def inspect(root,prefix):
    from lll.studies.closed import ClosedStudy
    from lll.studies.artifacts import encoded,digest
    from lll.airquantumgrav_geographic_report import construction_counts
    from lll.structured_noisy_publication import native_bindings,CASE_ARTIFACTS
    from lll.ilvis0_coordinate_precision import derive
    from lll.coordinate_optimizer_study import tasks,recipe,case_recipe,SCOPE,verify_gate
    from lll.structured_noisy_training import limits
    s=ClosedStudy(root,prefix)
    try:
        canonical={t['identity']:t for t in tasks()}
        actual={k:{n:v for n,v in t.items() if n not in ('index','shard')} for k,t in s.tasks.items()}
        if actual!=canonical or s.manifest['scope']!=SCOPE or s.input('recipe')!=recipe():
            raise ValueError('complete frozen 48-fit matrix required')
        verify_gate(s.input('arithmetic-gate'),s.input('arithmetic-binding'),s.manifest['sources'],s.input('qualification-environment'))
        bindings=native_bindings(s);cpp='analysis/lll/ilvis0_tangent.cpp'
        bindings['wide_sha256']=digest(derive(s.read('source-freeze/'+cpp,s.manifest['sources'][cpp],raw=True),
            expected_sha256=s.manifest['sources'][cpp]))
        rows=[];groups={};failures=[];replays=[];native=0;visits=0;evaluations=0;assets={}
        filenames=CASE_ARTIFACTS
        for identity,task in s.tasks.items():
            p=task['payload'];spec=p['case'];key=(p['draw_seed'],spec['law'],spec['model'],spec['profile'])
            groups.setdefault(key,{})
            if identity not in s.rows:
                failures.append(dict(identity=identity,reason='unexecuted'));continue
            envelope=s.envelope(identity);result=envelope['result'];base='artifacts/'+identity+'/'
            if base+'native-prepayment.json' in envelope['artifacts']:
                prepaid=s.artifact(identity,'native-prepayment.json');work=prepaid['attempted']
                native+=work['native_calls'];visits+=work['packet_visits']
            if not all(base+n in envelope['artifacts'] for n in (*filenames,'original-binding-replay.json')):
                failures.append(dict(identity=identity,reason=result.get('error','incomplete_artifacts')))
                if result['passed']:raise ValueError('incomplete result cannot pass')
                continue
            r=case_recipe(p['draw_seed'])
            saved,checked=audit_case(s,identity,spec=spec,result=result,r=r)
            expected=limits(r,spec['law'])[1]
            construction_counts(s.artifact(identity,'construction.sqlite',raw=True),
                s.completion['manifest_sha256'],identity,expected,complete=True)
            construction_counts(s.artifact(identity,'worker-build-journal.sqlite',raw=True),
                s.completion['manifest_sha256'],'worker',dict(builds=2),complete=True)
            operations=saved['native-operation-summary.json']
            if (prepaid['state']!='complete' or prepaid['prepaid']!={k:envelope['charged'][k] for k in ('native_calls','packet_visits')}
                    or prepaid['attempted']!={k:operations[k] for k in ('native_calls','packet_visits')}):
                raise ValueError('prepayment and actual native work differ')
            meta=s.artifact(identity,'compilation.json');tm=meta['tangent'];nm=meta['noise_bridge']
            if (tm['source_sha256']!=bindings['wide_sha256'] or nm['source_sha256']!=bindings['bridge_sha256']
                    or tm['compiler']!=bindings['compiler'] or nm['compiler']!=bindings['compiler']
                    or tm['original_source_sha256']!=s.manifest['sources'][cpp]
                    or tm['gravity_anchor_height_m']!=saved['input-binding.json']['gravity_anchor_height_m']
                    or tm['internal_mantissa_bits']<=53 or nm['internal_mantissa_bits']!=tm['internal_mantissa_bits']
                    or tm['version']!='compensated-coordinate-tangent-v1'):
                raise ValueError('compiled arithmetic differs from qualified source/environment')
            cache=f"shards/{task['shard']:03d}/kernels/"
            for m in (tm,nm):
                for filename,sha in ((m['source_file'],m['source_sha256']),(m['binary_file'],m['binary_sha256'])):
                    s.read(cache+filename,sha,raw=True);assets[cache+filename]=sha
                metadata=cache+str(Path(m['binary_file']).with_suffix('.json'))
                raw=s.read(metadata,raw=True);stored=json.loads(raw)
                if any(stored[k]!=m[k] for k in ('source_sha256','binary_sha256','compiler','cache_sha256')):
                    raise ValueError('compiled cache metadata differs')
                assets[metadata]=digest(raw)
            assets[cache+'builds.sqlite']=digest(s.read(cache+'builds.sqlite',raw=True))
            replay=s.artifact(identity,'original-binding-replay.json')
            if not replay['exact'] or replay['original_labels_changed']:raise ValueError('original replay changed')
            replays.extend(replay['matched_identities']);fit=saved['fit.json'];evaluations+=fit['evaluations']
            for old in s.input('saved-points'):
                if old['identity'] in replay['matched_identities']:
                    if old['payload']['draw_seed']!=p['draw_seed'] or old['payload']['case']!=spec:
                        raise ValueError('wrong original point replay')
                    if any(encoded(saved[n])!=encoded(v) for n,v in old['artifacts'].items()):
                        raise ValueError('original input/error binding changed')
            groups[key][spec['start']]=dict(fit=fit,forecast=saved['forecast.json'],
                training=saved['training-observations.json'],binding=saved['input-binding.json'])
            row=dict(identity=identity,seed=p['draw_seed'],**spec,converged=fit['converged'],passed=checked['passed'],
                cost=fit['residual_sum_squares'],evaluations=fit['evaluations'],
                at_bounds=[n for n,v in zip(fit['active_parameters'],fit['normalized_parameters'],strict=True) if abs(v)>=1-r['bound_margin']],
                prediction_horizontal_rms_m=result['prediction']['horizontal_rms_m'],
                prediction_height_rms_m=result['prediction']['vertical_rms_m'],original_labels_changed=False)
            rows.append(row)
        expected_replays={p['identity'] for p in s.input('saved-points')}
        replay_exact=len(replays)==4 and set(replays)==expected_replays
        pairs=[dict(seed=k[0],law=k[1],model=k[2],profile=k[3],**compare_starts(v)) for k,v in groups.items()]
        qualified=(len(rows)==48 and not failures and all(r['passed'] for r in rows)
            and len(pairs)==24 and all(p['passed'] for p in pairs) and replay_exact)
        return dict(complete=len(rows),selected=48,failures=failures,rows=rows,pairs=pairs,
            candidate_qualified=qualified,original_binding_replays=len(replays),original_binding_replays_exact=replay_exact,
            evaluations=evaluations,actual_native=dict(native_calls=native,packet_visits=visits),charged=s.summary['charged'],native_assets=assets,
            elapsed_s=s.summary['elapsed_s'],manifest_sha256=s.completion['manifest_sha256'],summary_sha256=s.completion['summary_sha256'],
            completed_optimizer_starts=len(rows),returned_tasks=len(s.rows),original_labels_changed=False,original_reads=0,protected_reads=0,
            confidence_calibrated=False,scientific_decision='abstain')
    finally:s.close()


def render(report):
    passed=sum(r['passed'] for r in report['rows']);pairs=sum(p['passed'] for p in report['pairs'])
    return '\n'.join(['# Compensated optimizer qualification','',
        f"Completed {report['complete']}/48 development fits; {passed} pass numerical and physical checks.",
        f"Matched starts agree in {pairs}/24 settings; original saved bindings replay in {report['original_binding_replays']}/4 cases.",
        f"The optimizer qualification {'passes' if report['candidate_qualified'] else 'does not pass'}.",'',
        'These generated examples reuse two exposed noise families, including the earlier failure.',
        'They are software qualification, not independent evidence or a calibrated confidence test.',
        'The original fits retain their labels; the stopped calibration campaign remains closed.','',
        '[All fits](results.csv) · [Matched starts](start-pairs.csv) · [Frozen plan](PLAN.md) · [Next analyses](../NEXT_STEPS.md).',''])


def publication_sources(root):
    from lll.studies.dependencies import source_closure
    return source_closure(root,['analysis/lll/coordinate_optimizer_report.py',
        'analysis/tests/test_coordinate_optimizer_report.py'])


def publish(root,prefix,output,*,qualification):
    from lll.ilvis0_control_publication import publish as package,check
    from lll.studies.artifacts import atomic,encoded,digest
    from lll.timing_arithmetic_report import csv_bytes
    from lll.studies.native_publication import include_native_caches
    from lll.studies.qualification import checked
    from lll.airquantumgrav_inventory import environment
    root=Path(root).resolve();public=root/output
    if (public/'evidence-receipt.json').exists():raise ValueError('immutable publication already exists')
    request,tests=checked(root,qualification,sources=publication_sources(root),environment=environment(),
        minimum_tests=8,required_tests=['test_optimizer_report_preserves_failed_or_missing_start_pairs',
            'test_optimizer_case_audit_loads_full_shared_bundle_and_combines_status[True-True]',
            'test_optimizer_case_audit_loads_full_shared_bundle_and_combines_status[False-True]',
            'test_optimizer_case_audit_loads_full_shared_bundle_and_combines_status[True-False]'])
    report=inspect(root,prefix);package(root/prefix,public,render(report),plan='docs/COMPENSATED_OPTIMIZER_PLAN.md')
    if report['native_assets']:
        include_native_caches(root,root/prefix,public,
            entries=[dict(path=n,sha256=sha) for n,sha in sorted(report['native_assets'].items())],maximum_bytes=64*1024**2)
    receipt=json.loads((public/'evidence-receipt.json').read_bytes())
    extras={'results.csv':csv_bytes(report['rows']),'start-pairs.csv':csv_bytes(report['pairs']),
        'artifacts/publication/verified-report.json':encoded(report),
        'artifacts/publication/reporter-source.py':Path(__file__).read_bytes(),
        'artifacts/publication/reporter-tests.py':Path(__file__).parents[1].joinpath('tests/test_coordinate_optimizer_report.py').read_bytes(),
        'artifacts/publication/qualification-request.json':request,'artifacts/publication/qualification-report.xml':tests}
    if (public/'INTERPRETATION.md').exists():extras['INTERPRETATION.md']=(public/'INTERPRETATION.md').read_bytes()
    for name,raw in extras.items():atomic(public/name,raw);receipt['artifacts'][name]=digest(raw)
    atomic(public/'evidence-receipt.json',encoded(receipt));check(root/prefix,public)
    if encoded(inspect(root,output))!=encoded(report):raise ValueError('public replay differs')
    return dict(path=output,qualified=report['candidate_qualified'],new_fits=0)
