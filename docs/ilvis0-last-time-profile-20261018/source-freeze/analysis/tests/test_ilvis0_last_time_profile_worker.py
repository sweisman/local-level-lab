# SPDX-License-Identifier: AGPL-3.0-or-later
"""Reuse exact timing-profile controls for the final declared source population."""
from pathlib import Path

_reference=Path(__file__).with_name('test_ilvis0_remaining_time_profile_worker.py')
_source=_reference.read_text()
_old="Path(__file__).with_name('ilvis0_remaining_time_profile_worker.py')"
assert _source.count(_old)==1
_source=_source.replace(_old,"Path(__file__).with_name('ilvis0_last_time_profile_worker.py')")
exec(compile(_source.replace('0e73879f98c3b701fd7c42df','b4e44ddc0f130ecd45674c78'),str(_reference),'exec'),globals())


def test_bound_anchor_is_preserved_and_field_endpoints_are_not_profiled():
    parent,old=inputs()
    for item in old['plan']['tasks']:
        if item['source_identity'].endswith('::repeat'):item['fit']['normalized_parameters'][-1]=1.
    old['plan']['untouched_passing_repeats'][0]['fit']['normalized_parameters'][-1]=1.
    extra=copy.deepcopy(old['plan']['tasks'][0])
    extra['source_identity']=extra['source_identity'].replace('sphere_still','sphere_rotating')
    extra['task']['model']='sphere_rotating';old['plan']['tasks'].append(extra)
    plan=worker().make_plan(parent,old)
    assert len(plan['tasks'])==10
    assert {t['task']['model'] for t in plan['tasks'] if t['kind']=='profile'}=={'sphere_still'}
    bound=[t for t in plan['tasks'] if t['kind']=='profile' and t['anchor_origin']=='repeat']
    assert len(bound)==4 and all(t['anchor_normalized']==1. and t['start_full'][-1]==1. for t in bound)
