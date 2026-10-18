# SPDX-License-Identifier: AGPL-3.0-or-later
"""Separate two-case timing profile; completed source studies remain unchanged."""
import copy
import math
from pathlib import Path
import sys
import types

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(Path(__file__).resolve().parent))
import ilvis0_fixed_time_worker as parent

TEMPLATE=Path(parent.__file__)
OUTPUT=ROOT/'data/ilvis0-remaining-time-profile-20261018'
GUIDE=ROOT/'docs/ilvis0-remaining-time-profile-20261018'
ORIGINAL=parent.prior.ORIGINAL
SID='0e73879f98c3b701fd7c42df'
CASES=('bias1_unsubtracted','bias1_profiled_removal')
GROUPS=tuple(case+'__'+role for case in CASES for role in ('primary','repeat'))
VERSION='ilvis0-remaining-two-case-time-profile-v1'


def make_plan(previous,original):
    controls=[copy.deepcopy(t) for t in previous['plan']['tasks'] if t['kind']=='control']
    if len(controls)!=2:raise ValueError('exact two smooth controls required')
    candidates=copy.deepcopy(original['plan']['tasks'])
    for item in copy.deepcopy(original['plan'].get('untouched_passing_repeats',[])):
        item['source_identity']=item['identity'];candidates.append(item)
    selected=[t for t in candidates if t['source_identity'].split('::')[0]==SID]
    expected={f'{SID}::{case}::sphere_still::{role}' for case in CASES for role in ('primary','repeat')}
    if len(selected)!=4 or {t['source_identity'] for t in selected}!=expected:
        raise ValueError('all four predeclared endpoints required')
    for item in controls:
        index=item['fit']['active_parameters'].index('time_offset')
        item.update(identity=item['source_identity']+'::remaining_time_control',maximum_fit_calls=3,
                    maximum_diagnostic_calls=0,anchor_normalized=item['fit']['normalized_parameters'][index])
    tasks=controls
    for case in CASES:
        roles={role:next(t for t in selected if t['source_identity']==f'{SID}::{case}::sphere_still::{role}')
               for role in ('primary','repeat')}
        names=roles['primary']['fit']['active_parameters']
        if names!=roles['repeat']['fit']['active_parameters'] or names.count('time_offset')!=1:
            raise ValueError('common full parameter order required within each processing case')
        index=names.index('time_offset')
        for role,item in roles.items():
            task=item['task'];point=item['fit']['normalized_parameters']
            if (task['segment_id']!=SID or task['case_id']!=case or task['model']!='sphere_still'
                    or len(point)!=len(names) or not all(math.isfinite(v) and -1<=v<=1 for v in point)
                    or item['time_scale_s']!=.15):raise ValueError('unchanged feasible endpoint required')
        anchors={role:t['fit']['normalized_parameters'][index] for role,t in roles.items()}
        if anchors['primary']==anchors['repeat']:raise ValueError('two distinct timing anchors required')
        for anchor in ('primary','repeat'):
            for start in ('primary','repeat'):
                item=copy.deepcopy(roles[start]);point=list(item['fit']['normalized_parameters'])
                point[index]=anchors[anchor]
                item.update(kind='profile',identity=f'{SID}::{case}::sphere_still::time_anchor_{anchor}::from_{start}',
                    anchor_origin=anchor,anchor_role=case+'__'+anchor,start_role=start,
                    anchor_normalized=anchors[anchor],start_full=point,
                    maximum_fit_calls=80,maximum_diagnostic_calls=1)
                tasks.append(item)
    return dict(version=VERSION,tasks=tasks,maximum_starts=10,maximum_profile_starts=8,
        maximum_native_evaluations=654,maximum_saved_pair_comparisons=4,numerical_threads=4,
        retries=0,conditional_only=True,final_stopping_rule_changed=False)


def executor_source(source):
    edits=[('maximum_starts=6','maximum_starts=10',3),
           ('maximum_native_evaluations=330','maximum_native_evaluations=654',4),
           ('len(starts)>6 or len(calls)>330','len(starts)>10 or len(calls)>654',1),
           ('total=6','total=10',1),
           ("for anchor in ('primary','repeat'):",'for anchor in PROFILE_GROUPS:',1),
           ("item['anchor_role']==item['start_role']","item.get('anchor_origin',item['anchor_role'])==item['start_role']",1),
           ("'diagnostic','full_tangent'","'diagnostic','tangent'",1),
           ("str(ROOT/'analysis/tests/test_ilvis0_fixed_time_worker.py')",
            "str(ROOT/'analysis/tests/test_ilvis0_remaining_time_profile_worker.py')",1)]
    for old,new,count in edits:
        if source.count(old)!=count:raise ValueError('unrecognized frozen executor layout: '+old)
        source=source.replace(old,new)
    return source


def build_executor():
    executor=types.ModuleType('_ilvis0_remaining_time_executor')
    executor.__file__=str(Path(__file__).resolve())
    exec(compile(executor_source(TEMPLATE.read_text()),str(TEMPLATE),'exec'),executor.__dict__)
    executor.OUTPUT=OUTPUT;executor.GUIDE=GUIDE;executor.OLD=ORIGINAL
    executor.QUALIFICATION=OUTPUT/'software-controls';executor.QUALIFICATION_GUIDE=GUIDE/'software-controls'
    executor.VERSION=VERSION;executor.TESTS=25;executor.PROFILE_GROUPS=GROUPS
    executor.make_plan=make_plan
    previous_sources=executor.sources

    def sources():
        values=previous_sources()
        for name in ('analysis/tests/ilvis0_remaining_time_profile_worker.py',
                     'analysis/tests/test_ilvis0_remaining_time_profile_worker.py'):
            values[str(ROOT/name)]=executor.sha(ROOT/name)
        executor.prior.check_hashes(values);return values

    executor.sources=sources
    return executor


if __name__=='__main__':build_executor().main()
