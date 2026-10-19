# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite wider-arithmetic recovery selected exclusively from saved stopping gates."""
from lll.ilvis0_pair_diagnosis import stopping_gates

VERSION='ilvis0-cost-only-precision-recovery-v1'
MODELS=('sphere_rotating','sphere_still','flat_still')
CASES=('bias1_unsubtracted','bias1_profiled_removal')
CONTROLS=(('233183f67270980491416678','bias1_unsubtracted','sphere_rotating'),
          ('31d7e5019dfdc9e2e6387206','bias1_profiled_removal','sphere_rotating'))


def classify(recovery, trial, manifest):
    if recovery['state']!='complete' or trial['state']!='complete' or not trial['qualification']['qualified']:
        raise ValueError('completed qualified precision dependency required')
    if not recovery['qualification']['controls_passed']:
        raise ValueError('recovery controls required')
    done={r['segment_id'] for r in trial['comparisons']
          if r['profile']['conditional_shape_preference']!='unresolved'}
    checks={r['identity']:r['passed'] for r in recovery['qualification']['repeatability']}
    repeat_tasks={t['segment_id']:t for t in manifest['proposal']['tasks'] if t['role']=='repeatability'}
    rows=[]
    seen=set()
    for record in recovery['comparisons']:
        sid=record['segment_id']
        if sid in seen: raise ValueError('duplicate recovery stretch')
        seen.add(sid)
        if record['profile']['conditional_shape_preference']!='unresolved' or sid in done: continue
        fits=[f for c in record['cases'] for f in c['fits']]
        if len(fits)!=6 or {(f['case_id'],f['model']) for f in fits}!={(c,m) for c in CASES for m in MODELS}:
            raise ValueError('six distinct frozen primary fits required')
        task=repeat_tasks[sid];identity=task['identity'];repeat=recovery['results'][identity]
        failures=[dict(role='primary',case_id=f['case_id'],model=f['model'],
                       failed_gates=stopping_gates(f)['failed_gates']) for f in fits if not f['converged']]
        if not repeat['converged']:
            failures.append(dict(role='repeat',case_id=task['case_id'],model=task['model'],
                                 failed_gates=stopping_gates(repeat)['failed_gates']))
        elif identity in checks and not checks[identity]:
            failures.append(dict(role='repeat',case_id=task['case_id'],model=task['model'],
                                 failed_gates=['repeat_agreement']))
        elif identity not in checks and all(f['converged'] for f in fits):
            failures.append(dict(role='repeat',case_id=task['case_id'],model=task['model'],
                                 failed_gates=['repeat_agreement_unavailable']))
        eligible=bool(failures) and all(f['failed_gates']==['relative_cost'] for f in failures)
        rows.append(dict(segment_id=sid,eligible=eligible,failures=failures,
                         repeat_case_id=task['case_id'],repeat_model=task['model']))
    return sorted(rows,key=lambda r:r['segment_id'])


def build(recovery, trial, manifest):
    inventory=classify(recovery,trial,manifest)
    targets=[r for r in inventory if r['eligible']]
    if not targets: raise ValueError('no cost-only targets')
    tasks=[]
    def add(sid,case,model,role):
        tasks.append(dict(identity='::'.join((sid,case,model,role)),segment_id=sid,
                          case_id=case,model=model,role=role,
                          maximum_evaluations=200 if role=='repeat' else 40,
                          seed_policy='frozen_primary_endpoint_plus_0.01' if role=='repeat' else 'frozen_primary_endpoint'))
    for sid,case,model in CONTROLS: add(sid,case,model,'control')
    for row in targets:
        for case in CASES:
            for model in MODELS: add(row['segment_id'],case,model,'primary')
        add(row['segment_id'],row['repeat_case_id'],row['repeat_model'],'repeat')
    return dict(version=VERSION,tasks=tasks,inventory=inventory,
                target_segment_ids=[r['segment_id'] for r in targets],
                control_segment_ids=[r[0] for r in CONTROLS],maximum_starts=len(tasks),
                maximum_native_sweeps=sum(t['maximum_evaluations']+2 for t in tasks),
                physical_bounds_changed=False,stopping_tolerances_changed=False,retry_allowance=0,
                target_selection='all remaining stretches whose failed primary and scheduled repeat gates are exclusively relative-cost change',
                repeat_cost_relative_tolerance=1e-6,repeat_track_rms_tolerance_m=.01,
                control_cost_relative_tolerance=1e-6,control_track_rms_tolerance_m=.01)
