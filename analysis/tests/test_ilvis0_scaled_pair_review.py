# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
from pathlib import Path

import pytest


def publication():
    path=Path(__file__).resolve().parents[2]/'docs/ilvis0-scaled-pair-review-20261018/build_report.py'
    assert path.exists(), 'scaled pair review is missing'
    spec=importlib.util.spec_from_file_location('scaled_pair_review',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def fixture():
    sid='370cec66878c4c1cf84b4ceb';case='bias1_profiled_removal';identity=f'{sid}::{case}::sphere_rotating::repeat'
    item=dict(kind='target',start_role='repeat',source_role=case+'/repeat',source_identity=identity,
        task=dict(segment_id=sid,identity=identity.rsplit('::',1)[0]+'::primary',case_id=case,model='sphere_rotating'))
    row=dict(status='complete',passed=True,source_role=item['source_role'],source_relocation=dict(passed=True),
        cumulative_from_source=dict(passed=True),physical_bounds_changed=False,scientific_stopping_limits_changed=False,
        scaled_affine_version='ilvis0-scaled-affine-branch-v1',geometry=dict(side_geometry_supported=True,
            representability_version='ilvis0-representable-side-clock-v1',representability=dict(passed=True,
                adjacent_clock_states_distinct=True,clock_state_matches=[True]*4)),
        boundary_check=dict(passed=True,branches=[dict(side=s,passed=True) for s in ('left','right')],
            policy=dict(stationarity_tolerance=1e-4,relative_cost_tolerance=1e-8,
                position_rms_tolerance_m=.001,position_max_tolerance_m=.01,
                affine_solver='ilvis0-scaled-affine-branch-v1')))
    return item,row


def test_explicit_source_role_preserves_repeat_identity():
    item,row=fixture();module=publication()
    assert module.scientific_identity(item).endswith('::repeat')
    module.require_gate(item,row)


@pytest.mark.parametrize('bad',['boundary','side','source','movement','clock','bounds','limits','solver','role','status','tolerance'])
def test_incomplete_or_changed_gate_cannot_publish(bad):
    item,row=fixture()
    if bad=='boundary':row['boundary_check']['passed']=False
    if bad=='side':row['boundary_check']['branches'].pop()
    if bad=='source':item['source_identity']=item['source_identity'].replace('repeat','primary')
    if bad=='movement':row['cumulative_from_source']['passed']=False
    if bad=='clock':row['geometry']['representability']['clock_state_matches'][0]=False
    if bad=='bounds':row['physical_bounds_changed']=True
    if bad=='limits':row['scientific_stopping_limits_changed']=True
    if bad=='solver':row['scaled_affine_version']='other'
    if bad=='role':item['source_role']='bias1_profiled_removal/primary'
    if bad=='status':row['status']='interrupted'
    if bad=='tolerance':row['boundary_check']['policy']['stationarity_tolerance']=.1
    with pytest.raises(ValueError):publication().require_gate(item,row)


def test_required_pair_set_keeps_both_processing_cases():
    module=publication();expected=sorted(f'{module.SID}::{case}::sphere_rotating::repeat' for case in module.policy.CASES)
    assert module.required_pairs(expected)==expected
    with pytest.raises(ValueError):module.required_pairs(expected[:1])
    with pytest.raises(ValueError):module.required_pairs(expected+[expected[0]])
