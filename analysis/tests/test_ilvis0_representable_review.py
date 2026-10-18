# SPDX-License-Identifier: AGPL-3.0-or-later
import copy
import importlib.util
from pathlib import Path

import pytest


def publication():
    path=Path(__file__).resolve().parents[2]/'docs/ilvis0-representable-review-20261018/build_report.py'
    assert path.exists(), 'representable review builder is missing'
    spec=importlib.util.spec_from_file_location('representable_review',path)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value)
    return value


def fixture(role='repeat'):
    sid='0e73879f98c3b701fd7c42df';case='bias1_unsubtracted'
    item=dict(kind='target',start_role=role,source_role=case+'/'+role,
        source_identity=f'{sid}::{case}::sphere_still::free_time_{role}::remaining_cluster_check',
        task=dict(identity=f'{sid}::{case}::sphere_still::primary',segment_id=sid,case_id=case,model='sphere_still'))
    result=dict(status='complete',passed=True,source_role=item['source_role'],
        source_relocation=dict(passed=True),cumulative_from_source=dict(passed=True),
        boundary_check=dict(passed=True,branches=[dict(side=s,passed=True) for s in ('left','right')]),
        scientific_stopping_limits_changed=False,representability_version='ilvis0-representable-side-clock-v1',
        geometry=dict(side_geometry_supported=True,representability=dict(passed=True,
            clock_state_matches=[True]*4,adjacent_clock_states_distinct=True)))
    return item,result


def test_repeat_role_is_derived_from_checked_start_provenance():
    item,result=fixture();module=publication()
    assert module.scientific_identity(item).endswith('::repeat')
    module.require_gate(item,result,representable=True)


@pytest.mark.parametrize('bad',['boundary','side','movement','cumulative','geometry','clock','limits','role','source','status'])
def test_incomplete_or_misassigned_evidence_cannot_publish(bad):
    item,result=fixture()
    if bad=='boundary':result['boundary_check']['passed']=False
    if bad=='side':result['boundary_check']['branches'].pop()
    if bad=='movement':result['source_relocation']['passed']=False
    if bad=='cumulative':result['cumulative_from_source']['passed']=False
    if bad=='geometry':result['geometry']['side_geometry_supported']=False
    if bad=='clock':result['geometry']['representability']['clock_state_matches'][0]=False
    if bad=='limits':result['scientific_stopping_limits_changed']=True
    if bad=='role':item['source_role']='bias1_unsubtracted/primary'
    if bad=='source':item['source_identity']=item['source_identity'].replace('free_time_repeat','free_time_primary')
    if bad=='status':result['status']='interrupted'
    with pytest.raises(ValueError):
        publication().scientific_identity(item)
        publication().require_gate(item,result,representable=True)


def test_old_profiled_gate_does_not_claim_new_geometry_qualification():
    item,result=fixture('primary');result.pop('representability_version');result.pop('scientific_stopping_limits_changed')
    result.pop('geometry')
    publication().require_gate(item,result,representable=False)


def test_complete_review_requires_both_scheduled_repeat_pairs():
    from lll import ilvis0_boundary_publication as policy
    sid='0e73879f98c3b701fd7c42df';cases=[];pairs=[]
    for case in sorted(policy.CASES):
        cases.append(dict(case_id=case,fits=[dict(model=m,converged=True,residual_sum_squares=c)
            for m,c in (('sphere_rotating',1.),('sphere_still',2.),('flat_still',3.))]))
        pairs.append(dict(identity=f'{sid}::{case}::sphere_still::repeat',primary_passed=True,repeat_passed=True,
            relative_cost_difference=0.,track_rms_neu_m=[0.,0.,0.],passed=True))
    review=dict(target_segment_ids=[sid],comparisons=[dict(segment_id=sid,cases=cases)],
        controls=[dict(passed=True),dict(passed=True)],pairs=pairs,required_repeat_identities=[p['identity'] for p in pairs])
    assert policy.classify(review,{sid:'unresolved'})[sid]['shape_preference']=='globe'
    partial=copy.deepcopy(review);partial['pairs'].pop()
    with pytest.raises(ValueError):policy.classify(partial,{sid:'unresolved'})
