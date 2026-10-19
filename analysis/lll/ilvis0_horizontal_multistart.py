# SPDX-License-Identifier: AGPL-3.0-or-later
"""Explicit finite matched observed multi-start scope and unchanged repeat gate."""
from . import ilvis0_horizontal_observed as preceding
from . import ilvis0_multistart

VERSION='ilvis0-horizontal-matched-multistart-v1'
GRID=(-.8,0.,.8)
LIMITS=dict(maximum_starts=38,maximum_tangents_per_start=200,maximum_diagnostics_per_start=1,
    maximum_preflight_calls=8,maximum_native_evaluations=7646,numerical_threads=4,
    maximum_wall_s=72000,retries=0)


def plan(selected):
    if len(selected)!=2 or {r['segment']['imu_type'] for r in selected}!={8,21}:
        raise ValueError('exact parent two-recording selection required')
    target=next(r['segment']['segment_id'] for r in selected if r['segment']['imu_type']==21)
    control=next(r['segment']['segment_id'] for r in selected if r['segment']['imu_type']==8)
    tasks=[]
    for case in preceding.CASES:
        for model in preceding.MODELS:
            for role in ('primary','repeat'):
                for index,timing in enumerate(GRID):
                    tasks.append(dict(identity='::'.join((target,case,model,role,'grid'+str(index))),segment_id=target,
                        case_id=case,model=model,role=role,timing_start=timing,control=False,axes=['latitude','longitude']))
    for role in ('primary','repeat'):
        tasks.append(dict(identity='::'.join((control,'bias1_unsubtracted','sphere_rotating',role,'control')),
            segment_id=control,case_id='bias1_unsubtracted',model='sphere_rotating',role=role,
            control=True,axes=['latitude','longitude']))
    return dict(version=VERSION,tasks=tasks,timing_grid=list(GRID),**LIMITS)


def choose(rows,tasks):
    expected=[t['identity'] for t in tasks]
    return ilvis0_multistart.select(rows,expected_ids=expected)
