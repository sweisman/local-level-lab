# SPDX-License-Identifier: AGPL-3.0-or-later
"""Fixed six-target recovery, with every failed primary independently repeated."""
import copy

VERSION='ilvis0-hybrid-six-target-plan-v1'
TARGETS=('0e73879f98c3b701fd7c42df','370cec66878c4c1cf84b4ceb','50f24131843071ae9312c082',
         'b4e44ddc0f130ecd45674c78','bb8061a43b4f14b6262ceda1','da346f70a6661ee42cecea19')
CASES=('bias1_unsubtracted','bias1_profiled_removal')
MODELS=('sphere_rotating','sphere_still','flat_still')


def build(parent,summary):
    if summary['state']!='complete' or not summary['qualification']['controls_passed']:
        raise ValueError('completed parent with passing controls required')
    records={r['segment_id']:r for r in summary['comparisons']}
    if {sid for sid,r in records.items() if r['profile']['conditional_shape_preference']=='unresolved'}!=set(TARGETS):
        raise ValueError('six frozen unfinished targets required')
    old={t['identity']:t for t in parent['plan']['tasks']};tasks=[];reused={}
    for task in parent['plan']['tasks']:
        if task['role']=='control':
            row=copy.deepcopy(task);row['reference']=copy.deepcopy(summary['results'][task['identity']]);tasks.append(row)
    for sid in TARGETS:
        for case in records[sid]['cases']:
            for fit in case['fits']:
                key='::'.join((sid,case['case_id'],fit['model'],'primary'))
                if fit['converged']:
                    reused[key]=copy.deepcopy(fit);continue
                for role in ('primary','repeat'):
                    task=copy.deepcopy(old[key]);task.update(role=role,identity=key.rsplit('::',1)[0]+'::'+role,
                        reference=copy.deepcopy(fit),maximum_evaluations=200,
                        seed_policy='latest_frozen_primary_plus_0.01' if role=='repeat' else 'latest_frozen_primary')
                    tasks.append(task)
    if (len(tasks)!=24 or len({t['identity'] for t in tasks})!=24 or len(reused)!=25
            or sum(t['role']=='primary' for t in tasks)!=11 or sum(t['role']=='repeat' for t in tasks)!=11
            or sum(t['role']=='control' for t in tasks)!=2):
        raise ValueError('eleven primary/repeat pairs, two controls and 25 reused primaries required')
    plan=dict(parent['plan'],version=VERSION,tasks=tasks,target_segment_ids=list(TARGETS),maximum_starts=24,
        maximum_native_sweeps=sum(t['maximum_evaluations']+2 for t in tasks),retry_allowance=0,
        solver='lll.ilvis0_solver_trust_v2',reuse_passed_parent_primaries=True,
        repeat_policy='all eleven newly fitted primary identities must pass their own predetermined repeat',
        target_selection='all six unresolved targets from the completed nine-target assessment')
    if plan['maximum_native_sweeps']!=4528: raise ValueError('unexpected finite sweep allowance')
    return plan,reused


def aggregate_repeatability(plan,raw):
    expected={t['identity'] for t in plan['tasks'] if t['role']=='repeat'}
    pairs=raw['repeatability']
    if len(pairs)!=len(expected) or {r['identity'] for r in pairs}!=expected:
        raise ValueError('every scheduled primary/repeat pair required exactly once')
    groups=[]
    for sid in plan['target_segment_ids']:
        checks=[r for r in pairs if r['identity'].split('::')[0]==sid]
        if not checks: raise ValueError('missing target repeat checks')
        groups.append(dict(identity=sid+'::all_failed_primaries::matched::repeat',passed=all(r['passed'] for r in checks),
                           required_pairs=len(checks),pair_identities=[r['identity'] for r in checks]))
    return dict(raw,pair_repeatability=copy.deepcopy(pairs),repeatability=groups,
                qualified=bool(raw['qualified'] and all(r['passed'] for r in groups)))
