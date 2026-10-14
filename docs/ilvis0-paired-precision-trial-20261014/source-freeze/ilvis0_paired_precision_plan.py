# SPDX-License-Identifier: AGPL-3.0-or-later
"""Frozen cost-only failure class; no selection from scientific preferences."""
VERSION='ilvis0-paired-precision-qualification-v1'
MODELS=('sphere_rotating','sphere_still','flat_still')
CASES=('bias1_unsubtracted','bias1_profiled_removal')
PAIRS=(('3df34ea39a6cbdbe15bb0f36','233183f67270980491416678','bias1_unsubtracted'),
       ('a953c8ddf4fae255674de128','31d7e5019dfdc9e2e6387206','bias1_profiled_removal'))


def build():
    tasks=[]
    def add(sid,case,model,role):
        tasks.append(dict(identity='::'.join((sid,case,model,role)),segment_id=sid,
                          case_id=case,model=model,role=role,
                          maximum_evaluations=200 if role=='repeat' else 40,
                          seed_policy='frozen_primary_endpoint_plus_0.01' if role=='repeat' else 'frozen_primary_endpoint'))
    for target,control,case in PAIRS:
        add(control,case,'sphere_rotating','control')
    for target,control,case in PAIRS:
        for processing in CASES:
            for model in MODELS:
                add(target,processing,model,'primary')
        add(target,case,'sphere_rotating','repeat')
    return dict(version=VERSION,tasks=tasks,target_segment_ids=[p[0] for p in PAIRS],
                control_segment_ids=[p[1] for p in PAIRS],maximum_starts=len(tasks),
                maximum_native_sweeps=sum(t['maximum_evaluations']+2 for t in tasks),
                physical_bounds_changed=False,stopping_tolerances_changed=False,retry_allowance=0,
                target_selection='two frozen relative-cost-only failures, not model-cost selection',
                repeat_cost_relative_tolerance=1e-6,repeat_track_rms_tolerance_m=.01,
                control_cost_relative_tolerance=1e-6,control_track_rms_tolerance_m=.01)
