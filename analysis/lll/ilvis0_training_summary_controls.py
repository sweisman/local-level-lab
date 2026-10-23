# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved-source qualification of signed training-expression projections."""
from fractions import Fraction as F
import json
from pathlib import Path


def check_case(material,*,save):
    import time
    import numpy as np
    from lll.ilvis0_declared_training_rows import projected_training_rows
    from lll.ilvis0_summary_error_controls import fixed_weights
    started=time.monotonic();training=material['training'];reports=material['reports'];region=training['region']
    times=training['times_s'];n=len(times);count=3*n;noise=material['noise_allowance_m']
    if times!=[2.,10.,30.,180.,290.] or noise!=1.:
        raise ValueError('original five training epochs and one-metre bounded-error premise required')
    units=np.eye(count).tolist();common=dict(training=training,reports=reports,source_binding=material['source_binding'])
    coordinates=projected_training_rows(**common,weights=units,observation_allowance_m=[noise]*count)
    if (coordinates['design'][:count]!=[row+[0.]*(region['parameter_count']-51) for row in region['design']]
            or coordinates['upper'][:count]!=region['target_upper']
            or coordinates['upper'][count:]!=[-v for v in region['target_lower']]):
        raise ValueError('unit projections do not reproduce all saved coordinate inequalities')
    weights,_=fixed_weights(times,training_end_s=290.)
    from lll.ilvis0_saved_prediction_audit import endpoint
    allowances=[endpoint(sum((abs(F(float(v)))*F(noise) for v in row),F(0)),True) for row in weights]
    projected=projected_training_rows(**common,weights=weights.tolist(),observation_allowance_m=allowances)
    exact_rows=[]
    for index,w in enumerate(weights):
        coefficients=[sum((F(float(v))*F(region['design'][j][k]) for j,v in enumerate(w)),F(0)) for k in range(51)]
        shift=sum((v*F(c) for v,c in zip(coefficients,region['center'][:51],strict=True)),F(0))
        delta=F(0);remainder=F(0)
        for j,v in enumerate(w):
            epoch,axis=divmod(j,3);a=F(float(v));scale=F(region['coordinate_scale'][axis])
            delta+=a*(F(training['observations'][epoch][axis])-F(training['nominal'][epoch][axis]))*scale
            remainder+=abs(a)*(F(reports[epoch]['unshared_remainder'][axis])*scale+F(region['arithmetic_allowance']))
        rounding=sum((abs(F(v)-a)*max(abs(F(lo)),abs(F(hi))) for v,a,lo,hi in zip(
            projected['design'][index][:51],coefficients,region['lower'][:51],region['upper'][:51],strict=True)),F(0))
        radius=F(allowances[index])+remainder+rounding
        lo=shift+delta-radius;hi=shift+delta+radius
        if projected['upper'][index]!=endpoint(hi,True) or projected['upper'][index+12]!=-endpoint(lo,False):
            raise ValueError('signed projection differs from independent rational reconstruction')
        exact_rows.append(dict(lower=str(lo),upper=str(hi),unshared=str(remainder),coefficient_rounding=str(rounding)))
    save('coordinate-rows.json',coordinates);save('projected-rows.json',projected);save('exact-row-audit.json',exact_rows)
    return dict(identity=material['identity'],model=material['model'],profile=material['profile'],passed=True,
        coordinate_rows_reproduced=2*count,summary_rows=12,exact_rows_checked=24,
        parameter_count=region['parameter_count'],physical_parameter_count=27,
        source_id=material['source_binding']['source_id'],reference_binding=material['source_binding']['reference_binding'],
        training_epochs=n,complete_cadence=False,projected_training_id=projected['projected_training_id'],
        maximum_unshared_radius_m=max(projected['unshared_radius_m']),
        maximum_coefficient_rounding_radius_m=max(projected['coefficient_rounding_radius_m']),
        elapsed_s=time.monotonic()-started,native_evaluations=0,optimizer_starts=0,original_reads=0,
        future_observations_used=False,prediction_method_qualified=False,observational_coverage_qualified=False,
        scientific_decision='abstain')


def prepare(root,identity='ilvis0-training-summary-controls-20261022'):
    from lll.studies.closed import ClosedStudy
    from lll.studies.artifacts import atomic,encoded,safe_path
    from lll.studies.dependencies import source_closure
    from lll.studies.runtime import Definition
    from lll.ilvis0_summary_error_controls import inspect as inspect_errors
    root=Path(root).resolve()
    if not inspect_errors(root,'data/ilvis0-summary-error-controls-20261022')['complete']:
        raise ValueError('close all four shared error-family controls first')
    base=safe_path(root,'data/ilvis0-source-point-development/training-summary-inputs')
    if base.exists() or safe_path(root,'data/'+identity).exists():raise ValueError('fresh saved-binding freeze required')
    adapter='analysis/lll/ilvis0_training_summary_controls.py';plan='docs/ilvis0-training-summary-controls/PLAN.md'
    sources=source_closure(root,[adapter,plan,'analysis/tests/test_ilvis0_training_summary_controls.py',
        'analysis/tests/test_ilvis0_projected_training_rows.py','analysis/tests/test_ilvis0_declared_training_rows.py'])
    prefix='data/ilvis0-long-staged-feasibility-v2-20261021';study=ClosedStudy(root,prefix)
    inputs={};tasks=[];base.mkdir(parents=True)
    try:
        for key,task in study.tasks.items():
            region=study.artifact(key,'stage-02-region.json')
            obs=study.artifact(key,'training-observations.json')
            reports=[study.artifact(key,f'training-bound-{i:02d}.json') for i in range(1,6)]
            native=[study.artifact(key,f'native-{i:02d}.json') for i in range(6,11)]
            if any(v['status']!=0 or v['time_s']!=t or v['point']!=region['center'][:27]
                for v,t in zip(native,obs['times_s'],strict=True)):
                raise ValueError('complete saved native expansion points required')
            binding={k:reports[0][k] for k in ('source_id','reference_binding','normalized_center','lower','upper')}
            if binding['reference_binding']!=region['binding'] or binding['source_id']!=region['source_id']:
                raise ValueError('saved physical-source/reference identity mismatch')
            training=dict(region=region,times_s=obs['times_s'],observations=obs['observations'],
                nominal=[v['prediction'] for v in native],jacobian=[v['jacobian'] for v in native],source_binding=binding)
            refs={name:sha for name,sha in study.envelope(key)['artifacts'].items()
                if any(token in name for token in ('training-bound-','training-observations','stage-02-region','native-0','native-10'))}
            value=dict(identity=key,model=task['payload']['model'],profile=task['payload']['profile'],
                training=training,reports=reports,source_binding=binding,noise_allowance_m=obs['allowance_m'],
                provenance=dict(parent=prefix,manifest_sha256=study.completion['manifest_sha256'],artifact_sha256=refs))
            path=base/(key+'.json');atomic(path,encoded(value));inputs[key]=path.relative_to(root).as_posix()
            tasks.append(dict(identity=key,input_key=key,payload=dict(model=value['model'],profile=value['profile']),
                limits=dict(native_calls=0,packet_visits=0,bound_calls=0,bound_steps=0)))
        if {(t['payload']['model'],t['payload']['profile']) for t in tasks}!={(m,p) for m in range(3) for p in (False,True)}:
            raise ValueError('all six original generated sources required')
        definition=dict(id=identity,adapter=adapter,sources=sources,inputs=inputs,tasks=tasks,workers=1,threads=1,maximum_wall_s=120.)
        atomic(base/'definition.json',encoded(definition));m=Definition.from_dict(definition,root).prepare(root)
        return dict(path='data/'+identity,identities=6,sources=len(m['sources']),allocation=m['allocation'],limits=m['limits'])
    finally:study.close()


def evaluate(task,context):
    value=json.loads(context.input_path().read_bytes())
    if value['identity']!=task['identity'] or any(value[k]!=v for k,v in task['payload'].items()):
        raise ValueError('fixed saved-source identity required')
    result=check_case(value,save=context.save);context.save('summary-binding.json',result);return result


def inspect(root,prefix):
    from lll.studies.closed import ClosedStudy
    study=ClosedStudy(root,prefix);rows=[]
    try:
        for identity in study.tasks:
            if identity not in study.rows:continue
            value=study.envelope(identity)['result']
            if value.get('passed'):
                for name in ('coordinate-rows.json','projected-rows.json','exact-row-audit.json'):
                    study.artifact(identity,name)
                if value!=study.artifact(identity,'summary-binding.json'):raise ValueError('saved binding result differs')
            rows.append(value)
        actual={(r.get('model'),r.get('profile')) for r in rows if r.get('passed')}
        return dict(rows=rows,complete=len(rows)==6 and actual=={(m,p) for m in range(3) for p in (False,True)},
            manifest_sha256=study.completion['manifest_sha256'],summary_sha256=study.completion['summary_sha256'],
            numerical_work=0,prediction_method_qualified=False)
    finally:study.close()


def render(report):
    text=['# Connecting training summaries to saved native predictions','',
        'This check applies the signed-summary interface to six sealed generated sources, covering '
        'all three candidates and both processing assumptions. It reuses the original five training '
        'epochs, native predictions, Jacobians and nonlinear bound reports. No integration or fit is repeated.',
        '', '| Candidate | Processing | Coordinate inequalities reproduced | Signed-summary inequalities audited | Result |',
        '|---|---|---:|---:|---|']
    labels=['Globe + field','Globe, zero field','Stationary disc']
    for r in report['rows']:
        if not r.get('passed'):
            text.append('| — | — | — | — | Failed |');continue
        text.append('| '+' | '.join([labels[r['model']],'Profiled removal' if r['profile'] else 'Zero removal',
            str(r['coordinate_rows_reproduced']),str(r['exact_rows_checked']),'Passed'])+' |')
    text+=['', 'Unit rows reproduce every original coordinate inequality. Twelve signed time-polynomial '
        'summaries are checked again with exact rational arithmetic. All 27 physical parameters and '
        '51 source-expression columns remain present. Unknown remainder signs are not canceled; '
        'rounded projected coefficients have a separate allowance over the full box.',
        '', 'This uses the original deterministic one-metre error premise and its conservative signed '
        'sum. It does not apply the dense-cadence Gaussian noise examples to these sparse observations, '
        'add observations, tighten calibration bounds or recalculate later positions.',
        '', '**The full prediction method remains unqualified.** The next scientific test needs complete '
        'training cadence, matched nonlinear source bounds and the declared error family, followed by '
        'whole-period prediction coverage. The 53-stretch findings remain unchanged.',
        '', '[Frozen scope](PLAN.md) · [Next step](../ilvis0-joint-projection-controls/NEXT_PLAN.md) · '
        '[Error assumptions](../PREDICTION_ERROR_ASSUMPTIONS.md)']
    return '\n'.join(text)+'\n'


def publish(root,prefix,output='docs/ilvis0-training-summary-controls'):
    from lll.ilvis0_control_publication import publish as package
    from lll.studies.artifacts import atomic,encoded,digest,safe_path
    from lll.studies.publication import archive_publication
    root=Path(root).resolve();data=safe_path(root,prefix);public=safe_path(root,output)
    if (public/'evidence-receipt.json').exists():raise ValueError('publication already sealed')
    report=inspect(root,prefix);package(data,public,render(report),plan='docs/ilvis0-training-summary-controls/PLAN.md')
    receipt=json.loads((public/'evidence-receipt.json').read_text());name='artifacts/publication/comparison.json'
    raw=encoded(report);atomic(public/name,raw);receipt['artifacts'][name]=digest(raw)
    atomic(public/'evidence-receipt.json',encoded(receipt))
    return dict(archive_publication(root,data,public),published=output,numerical_work=0)
