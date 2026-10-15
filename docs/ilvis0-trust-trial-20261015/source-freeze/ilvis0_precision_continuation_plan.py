# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite continuations selected by stopping status, preserving qualified equations."""
VERSION='ilvis0-precision-continuation-plan-v1'
MODELS=('sphere_rotating','sphere_still','flat_still')
CASES=('bias1_unsubtracted','bias1_profiled_removal')
CONTROLS=(('233183f67270980491416678','bias1_unsubtracted','sphere_rotating'),
          ('31d7e5019dfdc9e2e6387206','bias1_profiled_removal','sphere_rotating'))
STAGES={'budget':('ilvis0-budget-continuation-20261014',8,1296),
        'remaining':('ilvis0-remaining-precision-20261014',65,12810)}


def build(stage,summary,manifest):
    if stage not in STAGES or summary['state']!='complete' or not summary['qualification']['controls_passed']:
        raise ValueError('completed parent with passing controls required')
    tasks=[];targets=[]
    def add(sid,case,model,role):
        tasks.append(dict(identity='::'.join((sid,case,model,role)),segment_id=sid,case_id=case,
                          model=model,role=role,maximum_evaluations=40 if role=='control' else 200,
                          seed_policy='frozen_primary_endpoint_plus_0.01' if role=='repeat' else 'frozen_primary_endpoint'))
    for sid,case,model in CONTROLS: add(sid,case,model,'control')
    if stage=='budget':
        for row in summary['comparisons']:
            if row['profile']['conditional_shape_preference']!='unresolved': continue
            failed=[f for c in row['cases'] for f in c['fits'] if not f['converged']]
            if len(failed)!=1 or failed[0].get('message')!='tangent allowance exhausted':
                raise ValueError('exactly one frozen budget failure per target required')
            fit=failed[0];sid=row['segment_id'];targets.append(sid)
            add(sid,fit['case_id'],fit['model'],'primary')
            add(sid,fit['case_id'],fit['model'],'repeat')
    else:
        for row in manifest['plan']['inventory']:
            if row['eligible']: continue
            sid=row['segment_id'];targets.append(sid)
            for case in CASES:
                for model in MODELS: add(sid,case,model,'primary')
            add(sid,row['repeat_case_id'],row['repeat_model'],'repeat')
    if not targets: raise ValueError('no unfinished targets')
    if len(set(targets))!=len(targets): raise ValueError('duplicate target')
    return dict(version=VERSION,stage=stage,tasks=tasks,target_segment_ids=targets,
                control_segment_ids=[r[0] for r in CONTROLS],maximum_starts=len(tasks),
                maximum_native_sweeps=sum(t['maximum_evaluations']+2 for t in tasks),retry_allowance=0,
                physical_bounds_changed=False,stopping_tolerances_changed=False,
                reuse_passed_parent_primaries=stage=='budget',
                target_selection='all three unfinished budget failures' if stage=='budget' else 'all nine previously excluded stationarity/position-failure stretches',
                control_cost_relative_tolerance=1e-6,control_track_rms_tolerance_m=.01,
                repeat_cost_relative_tolerance=1e-6,repeat_track_rms_tolerance_m=.01)
