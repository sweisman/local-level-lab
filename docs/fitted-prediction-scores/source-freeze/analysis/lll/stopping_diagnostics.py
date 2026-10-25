# SPDX-License-Identifier: AGPL-3.0-or-later
"""Explain saved stopping checks without executing a solver or changing labels.

This metadata-only helper imports no numerical library. Thresholds come from
the study's verified frozen source, never a current solver's imported globals.
"""
import ast
import math


def _number(value,*,positive=False):
    if (type(value) not in (float,int) or not math.isfinite(value)
            or value<0 or (positive and value==0)):
        raise ValueError('finite nonnegative value and positive tolerance required')
    return value


def _keywords(source,names):
    try:
        assignments=[n.value for n in ast.parse(source).body if isinstance(n,ast.Assign)
            and any(isinstance(t,ast.Name) and t.id=='POLICY' for t in n.targets)]
        if len(assignments)!=1:raise ValueError('one frozen POLICY assignment required')
        call=assignments[0]
        if not isinstance(call,ast.Call) or not isinstance(call.func,ast.Name) or call.func.id!='dict':
            raise ValueError('direct literal policy keywords required')
        found={}
        for key in names:
            values=[v.value for v in call.keywords if v.arg==key]
            if len(values)!=1:raise ValueError('one literal value per requested policy key required')
            found[key]=_number(ast.literal_eval(values[0]),positive=True)
        return found
    except (SyntaxError,TypeError,ValueError) as error:
        raise ValueError('unsupported frozen policy declaration') from error


def frozen_policy(refinement_source,position_source):
    return dict(_keywords(refinement_source,('relative_cost_tolerance','stationarity_tolerance')),
        **_keywords(position_source,('position_rms_tolerance_m','position_max_tolerance_m')))


def components(fit,policy):
    """Classify the conjuncts of an ordinary saved fresh-position probe only.

    A list of satisfied checks is not a revised convergence decision. Other
    stopping procedures remain explicitly unclassified by this helper.
    """
    if type(fit.get('converged')) is not bool:raise ValueError('original boolean stopping label required')
    result=dict(saved_converged=fit['converged'],reclassified=False,scientific_decision='abstain',
        confidence_calibrated=False,available=False)
    probe=fit.get('stability_probe')
    required=('actual_cost_change','fresh_stationarity','position_rms_neu_m','position_max_abs_neu_m',
        'position_rms_tolerance_m','position_max_tolerance_m','passed')
    if fit.get('near_zero_probe') is not None or not isinstance(probe,dict) or not all(k in probe for k in required):
        return dict(result,reason='different_or_incomplete_saved_stopping_probe')
    for key in ('relative_cost_tolerance','stationarity_tolerance','position_rms_tolerance_m','position_max_tolerance_m'):
        _number(policy[key],positive=True)
    if (fit.get('stationarity_tolerance')!=policy['stationarity_tolerance']
            or probe['position_rms_tolerance_m']!=policy['position_rms_tolerance_m']
            or probe['position_max_tolerance_m']!=policy['position_max_tolerance_m']
            or type(probe['passed']) is not bool):raise ValueError('saved and frozen stopping policies differ')
    vectors=[]
    for key in ('position_rms_neu_m','position_max_abs_neu_m'):
        values=probe[key]
        if not isinstance(values,list) or len(values)!=3:raise ValueError('all three saved physical axes required')
        vectors.append([_number(v) for v in values])
    checks={}
    for name,value,limit in [('relative_cost_change',probe['actual_cost_change'],policy['relative_cost_tolerance']),
            ('fresh_stationarity',probe['fresh_stationarity'],policy['stationarity_tolerance']),
            ('position_rms',max(vectors[0]),policy['position_rms_tolerance_m']),
            ('position_maximum',max(vectors[1]),policy['position_max_tolerance_m'])]:
        value=_number(value);checks[name]=dict(value=value,tolerance=limit,passed=value<=limit)
    passed=all(v['passed'] for v in checks.values())
    if probe['passed']!=passed:raise ValueError('saved probe label contradicts its frozen component checks')
    return dict(result,available=True,kind='fresh_position',all_components_satisfied=passed,components=checks,
        failed_components=[name for name,value in checks.items() if not value['passed']],
        position_rms_neu_m=vectors[0],position_max_abs_neu_m=vectors[1])


def audit(root,prefix):
    """Read hash-verified saved fits from a closed study; no original observations.

    This is a derived stopping diagnostic, not another fit or a scientific
    decision. The current numerical source is never substituted for its freeze.
    """
    from collections import Counter
    from pathlib import Path
    from .studies.closed import ClosedStudy
    from .studies.artifacts import digest
    study=ClosedStudy(root,prefix)
    try:
        names=('analysis/lll/ilvis0_solver_refinement.py','analysis/lll/ilvis0_solver_position.py')
        source={name:study.read('source-freeze/'+name,study.manifest['sources'][name],raw=True) for name in names}
        policy=frozen_policy(*(source[name] for name in names));rows=[]
        for identity,task in study.tasks.items():
            row=dict(identity=identity,payload=task['payload'],returned=identity in study.rows,
                available=False,reason='no_saved_fit',reclassified=False)
            if identity in study.rows:
                envelope=study.envelope(identity);path='artifacts/'+identity+'/fit.json'
                row['saved_task_passed']=envelope['result']['passed']
                if path in envelope['artifacts']:
                    fit=study.artifact(identity,'fit.json')
                    row.update(components(fit,policy),fit_sha256=envelope['artifacts'][path],
                        evaluations=fit.get('evaluations'),maximum_evaluations=fit.get('maximum_evaluations'),
                        termination=fit.get('termination'),message=fit.get('message'))
                    if row['available']:row.pop('reason',None)
            rows.append(row)
        counts=Counter('+'.join(v['failed_components']) or 'all_components_satisfied'
            for v in rows if v['available'])
        return dict(version='saved-stopping-components-v1',manifest_sha256=study.completion['manifest_sha256'],
            summary_sha256=study.completion['summary_sha256'],total=len(rows),rows=rows,
            available=sum(v['available'] for v in rows),component_counts=dict(sorted(counts.items())),
            policy=policy,policy_source_sha256={name:study.manifest['sources'][name] for name in names},
            diagnostic_source_sha256=digest(Path(__file__).read_bytes()),original_reads=0,protected_reads=0,
            native_calls=0,optimizer_starts=0,labels_changed=False,scientific_decision='abstain')
    finally:study.close()
