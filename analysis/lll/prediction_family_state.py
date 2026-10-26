# SPDX-License-Identifier: AGPL-3.0-or-later
"""Manifest-bound seed-family markers and cooperative, fail-closed futility.

Markers coordinate workers. Only independently checked sealed outcomes support
publication; these files alone never establish statistical coverage.
"""
import json
import math
from pathlib import Path

from .studies.artifacts import atomic,digest,encoded,safe_path


def _number(value):
    if type(value) not in (int,float) or not math.isfinite(value) or value<0:
        raise ValueError('finite nonnegative training cost or score required')
    return value


def _binding(context,task):
    found=[v for v in context.manifest['tasks'] if v['identity']==task['identity']]
    if found!=[task]:raise ValueError('unique unchanged task in the manifest required')
    p=task['payload']
    return dict(manifest_sha256=digest((context.root/'manifest.json').read_bytes()),identity=task['identity'],
        seed=p['draw_seed'],role=p['role'],population_sha256=p['population_sha256'],case=p['case'])


def record(context,task,result):
    marker=_binding(context,task);complete='converged' in result
    if complete and type(result['converged']) is not bool:raise ValueError('explicit numerical outcome required')
    cost=score=None
    if complete:
        fit=json.loads((context.directory/'fit.json').read_bytes())
        cost=_number(fit['residual_sum_squares']);score=_number(result['maximum_standardized_error'])
    marker.update(complete=complete,converged=result.get('converged',False),training_cost=cost,maximum_score=score)
    context.save('family-outcome.json',marker)
    return marker


def _read(context,task,manifest_sha256):
    path=safe_path(context.root,'artifacts/'+task['identity']+'/family-outcome.json')
    if not path.exists():return None
    value=json.loads(path.read_bytes());p=task['payload']
    expected=dict(manifest_sha256=manifest_sha256,identity=task['identity'],seed=p['draw_seed'],
        role=p['role'],population_sha256=p['population_sha256'],case=p['case'])
    if (any(value.get(k)!=v for k,v in expected.items()) or type(value.get('complete')) is not bool
            or type(value.get('converged')) is not bool or (value['converged'] and not value['complete'])):
        raise ValueError('family marker differs from its manifest, role or task')
    if value['complete']:_number(value['training_cost']);_number(value['maximum_score'])
    elif value.get('training_cost') is not None or value.get('maximum_score') is not None:
        raise ValueError('incomplete case cannot carry a selection cost or score')
    return value


def _failed_families(context,binding,policy):
    import fcntl
    directory=context.root/'family-state';directory.mkdir(exist_ok=True)
    base={k:binding[k] for k in ('manifest_sha256','role','population_sha256')}
    value=dict(base,seed=binding['seed']);target=directory/f"seed-{binding['seed']}.json"
    with (directory/'worker.lock').open('a+b') as lease:
        fcntl.flock(lease,fcntl.LOCK_EX)
        if target.exists() and json.loads(target.read_bytes())!=value:raise ValueError('seed-failure binding changed')
        if not target.exists():atomic(target,encoded(value))
        count=0
        for seed in policy['seeds']:
            path=directory/f'seed-{seed}.json'
            if path.exists():
                if json.loads(path.read_bytes())!=dict(base,seed=seed):raise ValueError('seed-failure role or manifest changed')
                count+=1
    return count


def check(context,task,*,policy,threshold=None):
    """Stop only when the predeclared full-cohort criterion cannot succeed."""
    from .ilvis0_forecast_publication import primary
    from .ilvis0_control_shards import _request_stop
    if policy['role']=='validation':_number(threshold)
    elif policy['role']!='calibration' or policy.get('order_statistic_rank')!=len(policy['seeds']):
        raise ValueError('maximum-order-statistic calibration policy required for early futility')
    binding=_binding(context,task);p=task['payload'];groups={}
    if p['role']!=policy['role'] or p['draw_seed'] not in policy['seeds']:raise ValueError('declared phase seed required')
    for other in context.manifest['tasks']:
        payload=other['payload']
        if payload['draw_seed']!=p['draw_seed']:continue
        if payload['role']!=p['role'] or payload['population_sha256']!=p['population_sha256']:
            raise ValueError('one bound population per seed family required')
        key=json.dumps({k:v for k,v in payload['case'].items() if k!='start'},sort_keys=True)
        groups.setdefault(key,[]).append(_read(context,other,binding['manifest_sha256']))
    for markers in groups.values():
        if any(v is None for v in markers):continue
        chosen=primary([dict(v,passed=v['complete'] and v['converged'],start=v['case']['start']) for v in markers])
        unavailable=chosen is None
        if policy['role']=='calibration' and unavailable:
            proof=dict(binding,reason='unavailable_calibration_family')
        elif policy['role']=='validation' and (unavailable or chosen['maximum_score']>threshold):
            count=_failed_families(context,binding,policy)
            if count<=policy['allowed_failures']:continue
            proof=dict(binding,reason='validation_failure_budget_exceeded',failed_families=count)
        else:continue
        context.save('family-futility.json',proof)
        _request_stop(context.root,proof['reason']+': '+str(binding['seed']))
        return proof
    return None
