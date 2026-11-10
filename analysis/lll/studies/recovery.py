# SPDX-License-Identifier: AGPL-3.0-or-later
"""Read-only recovery advice, never permission to retry or launch a study.

This checks frozen metadata, charges and sealed outcomes. Scientific side
artifacts remain subject to the shared runner's full verification before any
execution. An owned lease identifies ownership, not a live process or a PID.
"""
from contextlib import ExitStack
import json
from pathlib import Path
import sqlite3
import time
from types import SimpleNamespace

from .. import ilvis0_control_shards as runner
from .artifacts import ArchiveStore,digest,encoded,safe_path
from .closed import ClosedStudy
from .journal import inspect_snapshot


VERSION='lll-study-recovery-v1'


def _base(state,**fields):
    return dict(version=VERSION,state=state,evidence_scope='recovery_metadata_only',
        resume_authorized=False,requires_shared_runner_verification=True,
        scientific_decision='abstain',new_starts=0,new_native_calls=0,**fields)


def _closed(project,prefix,store):
    study=ClosedStudy(project,prefix,store=store)
    manifest=study.manifest;summary=study.summary
    authorization=study.read('authorization.json')
    if (manifest.get('version')!=runner.VERSION
            or authorization['manifest_sha256']!=study.completion['manifest_sha256']
            or authorization['limits']!=manifest['limits']
            or runner._tasks(manifest['tasks'],manifest['allocation']['workers'])!=manifest['tasks']):
        raise ValueError('closed manifest or authorization changed')
    return _base('closed',terminal_state=summary['state'],completed=summary['completed'],
        charged_identities=summary['charged_identities'],
        manifest_sha256=study.completion['manifest_sha256'],
        next_action='Preserve the closed allowance; never resume or retry it.')


def _journal(directory,assigned,freeze):
    """Check and index one immutable byte snapshot, without opening a writable DB."""
    path=safe_path(directory,'charges/journal.sqlite')
    pending=list((directory/'charges').glob('.pending-*'))
    sidecars=[path.with_name(path.name+suffix) for suffix in ('-journal','-wal')]
    if pending or any(p.exists() and p.stat().st_size for p in sidecars):
        raise ValueError('incomplete journal transaction; preserve it without repair')
    if not path.exists():return set(),{}
    raw=path.read_bytes();inspect_snapshot(raw,freeze)
    db=sqlite3.connect(':memory:')
    try:
        db.deserialize(raw);db.execute('PRAGMA query_only=ON')
        spec=json.loads(db.execute('SELECT spec FROM metadata').fetchone()[0])
        limits=dict(fit=max(1,max(t['limits']['native_calls'] for t in assigned)),
                    diagnostic=max(1,max(t['limits']['bound_calls'] for t in assigned)))
        if spec['limits']!={t['identity']:limits for t in assigned}:
            raise ValueError('journal allowances differ from the frozen shard')
        started=set();sweeps={}
        for (payload,) in db.execute('SELECT payload FROM events ORDER BY number'):
            row=json.loads(payload);record=row.get('record')
            if not isinstance(record,dict):raise ValueError('runner charge record required')
            identity=row['identity']
            if row['resource'] is None:started.add(identity)
            else:sweeps.setdefault(identity,[]).append(record)
        return started,sweeps
    finally:db.close()


def _outcomes(root,manifest,freeze):
    charged=set();outcomes={};closed_shards=set()
    for shard in range(manifest['allocation']['workers']):
        directory=safe_path(root,f'shards/{shard:03d}')
        assigned=[t for t in manifest['tasks'] if t['shard']==shard]
        starts,sweeps=_journal(directory,assigned,freeze);charged.update(starts)
        if (directory/'done.json').exists():
            done=runner._load(directory/'done.json')
            if done.get('manifest_sha256')!=freeze or done.get('shard')!=shard:
                raise ValueError('closed shard binding changed')
            closed_shards.add(shard)
        for task in manifest['tasks']:
            identity=task['identity']
            paths=[safe_path(root,f'shards/{shard:03d}/results/{identity}{suffix}.json')
                   for suffix in ('','.interrupted')]
            if task['shard']!=shard:
                if any(p.exists() or p.with_suffix('.seal.json').exists() for p in paths):
                    raise ValueError('result in wrong shard')
                continue
            counts=runner._counts(SimpleNamespace(read=lambda kind:sweeps.get(identity,[])),task)
            sealed=[p for p in paths if p.with_suffix('.seal.json').exists()]
            if len(sealed)>1:raise ValueError('duplicate sealed result')
            if not sealed:
                if identity not in starts and any(p.exists() for p in paths):
                    raise ValueError('uncharged result cannot authorize execution')
                continue
            path=sealed[0];seal=runner._load(path.with_suffix('.seal.json'))
            raw=path.read_bytes();value=json.loads(raw);result=value['result']
            if (identity not in starts or seal.get('sha256')!=digest(raw)
                    or seal.get('manifest_sha256')!=freeze or value.get('manifest_sha256')!=freeze
                    or value.get('identity')!=identity or value.get('shard')!=shard
                    or value.get('task_sha256')!=runner.digest(task) or value.get('charged')!=counts
                    or value.get('result_sha256')!=runner.digest(result)
                    or value.get('status') not in ('complete','interrupted')
                    or type(result.get('passed')) is not bool or result.get('scientific_decision')!='abstain'):
                raise ValueError('result sealing, binding or accounting changed')
            outcomes[identity]=value
    return charged,outcomes,closed_shards


def _unavailable_settings(manifest,unavailable,policy):
    if not policy:return [],'not_declared'
    if policy.get('role')!='calibration':return [],'not_maximum_order_calibration'
    seeds=policy.get('seeds',[])
    if (not seeds or any(type(s) is not int for s in seeds) or len(set(seeds))!=len(seeds)):
        raise ValueError('distinct finite calibration seeds required')
    if policy.get('order_statistic_rank')!=len(seeds):return [],'not_maximum_order_calibration'
    groups={};populations=set();seen=set()
    for task in manifest['tasks']:
        p=task['payload'];case=dict(p['case']);start=case.pop('start')
        if (p.get('role')!='calibration' or p.get('draw_seed') not in seeds
                or type(start) is not int or start not in (0,1)
                or not isinstance(p.get('population_sha256'),str) or not p['population_sha256']):
            raise ValueError('calibration task differs from its frozen recipe')
        population=p['population_sha256'];populations.add(population);seen.add(p['draw_seed'])
        key=(p['draw_seed'],population,encoded(case))
        groups.setdefault(key,[]).append((start,task['identity']))
    if len(populations)!=1 or seen!=set(seeds):raise ValueError('one complete bound calibration population required')
    failed=[]
    for (seed,population,raw),starts in groups.items():
        if len(starts)!=2 or {s for s,_ in starts}!={0,1}:
            raise ValueError('both prescribed starts required for each setting')
        identities=[identity for _,identity in sorted(starts)]
        if all(identity in unavailable for identity in identities):
            failed.append(dict(seed=seed,population_sha256=population,case=json.loads(raw),identities=identities))
    return failed,'maximum_order_calibration'


def inspect(project,prefix):
    """Return advice at one ownership snapshot; make no persistent changes."""
    project=Path(project).resolve();root=safe_path(project,prefix);store=ArchiveStore(project)
    try:
        catalog=store.catalog()
        if (root/'completion.json').exists() or prefix+'/completion.json' in catalog['paths']:
            return _closed(project,prefix,store)
        with ExitStack() as stack:
            initial=runner._load(root/'manifest.json')
            a=initial['allocation']
            if runner.allocation(workers=a['workers'],threads=a['threads'],reserved=a['reserved'])!=a:
                raise ValueError('invalid frozen numerical allocation')
            leases=['coordinator.lock']+[f'shards/{s:03d}/worker.lock'
                                         for s in range(initial['allocation']['workers'])]
            for name in leases:
                path=safe_path(root,name)
                if not path.exists():
                    if name=='coordinator.lock':continue
                    raise ValueError('missing declared worker lease')
                try:stack.enter_context(runner._lease(path,True))
                except ValueError:
                    return _base('owned',owned_lease=name,
                        next_action='Do not duplicate work; lease ownership does not establish process identity.')
            # A coordinator may have completed after the first completion read
            # and before releasing its lease. Closed allowances always win.
            if (root/'completion.json').exists():return _closed(project,prefix,store)
            manifest=runner.verify(root);freeze=runner._sha(root/'manifest.json')
            for name,sha in manifest['sources'].items():
                if digest(safe_path(project,name).read_bytes())!=sha:
                    raise ValueError('current source differs from the frozen implementation')
            if manifest['environment']!=runner.runtime_environment():
                raise ValueError('current numerical environment differs from the freeze')
            if manifest.get('accounting_format')!='sqlite-v1':
                raise ValueError('recovery inspection currently requires sqlite-v1 accounting')
            charged,outcomes,closed_shards=_outcomes(root,manifest,freeze)
            usable={i for i,v in outcomes.items() if v['status']=='complete'
                    and v['result']['passed'] and v['result'].get('converged') is True}
            unavailable=charged-usable
            unavailable.update(t['identity'] for t in manifest['tasks'] if t['shard'] in closed_shards
                               and t['identity'] not in usable)
            policy=runner._load(safe_path(root,manifest['inputs']['recipe']['path'])) if 'recipe' in manifest['inputs'] else {}
            if not isinstance(policy,dict):raise ValueError('explicit cohort policy object required')
            uninterrupted=policy.get('require_uninterrupted_cohort',False)
            if type(uninterrupted) is not bool:raise ValueError('explicit boolean uninterrupted-cohort policy required')
            interrupted={i for i in charged if i not in outcomes or outcomes[i]['status']=='interrupted'
                or outcomes[i]['result'].get('error_type')=='BudgetStopped'
                or 'artifacts/'+i+'/family-futility.json' in outcomes[i].get('artifacts',{})}
            failed,check=_unavailable_settings(manifest,unavailable,policy)
            uncharged=[t['identity'] for t in manifest['tasks'] if t['identity'] not in charged]
            runnable=[t['identity'] for t in manifest['tasks']
                      if t['identity'] not in charged and t['shard'] not in closed_shards]
            clock=runner._clock_record(root,manifest) if (root/'start.json').exists() else None
            if charged and clock is None:raise ValueError('charged study requires its original deadline')
            deadline=None if clock is None else clock['deadline_unix']
            state='uncharged_work_available' if runnable else 'no_uncharged_work'
            stop=root/'stop-request.json'
            if stop.exists():
                if runner._load(stop).get('manifest_sha256')!=freeze:raise ValueError('stop binding changed')
                state='stop_requested'
            elif deadline is not None and time.time()>=deadline:state='deadline_exhausted'
            elif failed or (uninterrupted and interrupted):state='cohort_unavailable'
            return _base(state,manifest_sha256=freeze,deadline_unix=deadline,
                charged_identities=len(charged),uncharged_identities=len(uncharged),
                uncharged_tasks=runnable,unavailable_identities=sorted(unavailable),
                interrupted_identities=sorted(interrupted),uninterrupted_cohort_required=uninterrupted,
                unavailable_calibration_settings=failed,cohort_check=check,
                next_action=('Continue only uncharged tasks through the shared runner after its full checks.'
                    if state=='uncharged_work_available' else 'Do not launch; preserve charges and the original allowance.'))
    finally:store.close()
