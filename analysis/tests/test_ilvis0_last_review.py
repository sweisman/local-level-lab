# SPDX-License-Identifier: AGPL-3.0-or-later
import copy
import importlib.util
from pathlib import Path

import pytest


def publication():
    path=Path(__file__).resolve().parents[2]/'docs/ilvis0-last-review-20261018/build_report.py'
    assert path.exists(), 'complete final-stretch review is missing'
    spec=importlib.util.spec_from_file_location('last_review',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def fixture(model='sphere_still',case='bias1_unsubtracted',role='repeat'):
    from test_ilvis0_scaled_pair_review import fixture as prior
    item,row=prior();sid='b4e44ddc0f130ecd45674c78'
    item.update(start_role=role,source_role=case+'/'+role,
        source_identity=f'{sid}::{case}::{model}::'+('free_time_' if model=='sphere_still' else '')+role)
    item['task'].update(segment_id=sid,case_id=case,model=model)
    row['source_role']=item['source_role']
    return item,row


@pytest.mark.parametrize('model',['sphere_rotating','sphere_still'])
@pytest.mark.parametrize('case',['bias1_unsubtracted','bias1_profiled_removal'])
def test_each_original_model_case_repeat_keeps_checked_identity(model,case):
    module=publication();item,row=fixture(model,case)
    assert module.scientific_identity(item)==f'{module.SID}::{case}::{model}::repeat'
    module.require_gate(item,row)


@pytest.mark.parametrize('bad',['side','source','movement','clock','bounds','limits','solver','role','status','tolerance'])
def test_failed_or_changed_gates_cannot_resolve_stretch(bad):
    module=publication();item,row=fixture()
    if bad=='side':row['boundary_check']['branches'].pop()
    if bad=='source':item['source_identity']=item['source_identity'].replace('repeat','primary')
    if bad=='movement':row['cumulative_from_source']['passed']=False
    if bad=='clock':row['geometry']['representability']['clock_state_matches'][0]=False
    if bad=='bounds':row['physical_bounds_changed']=True
    if bad=='limits':row['scientific_stopping_limits_changed']=True
    if bad=='solver':row['scaled_affine_version']='other'
    if bad=='role':item['source_role']='bias1_unsubtracted/primary'
    if bad=='status':row['status']='interrupted'
    if bad=='tolerance':row['boundary_check']['policy']['stationarity_tolerance']=.1
    with pytest.raises(ValueError):module.require_gate(item,row)


def test_all_four_original_pairs_required_without_duplicate_substitution():
    module=publication()
    pairs=[f'{module.SID}::{c}::{m}::repeat' for c in module.policy.CASES for m in ('sphere_rotating','sphere_still')]
    assert module.required_pairs(pairs)==sorted(pairs)
    with pytest.raises(ValueError):module.required_pairs(pairs[:-1])
    with pytest.raises(ValueError):module.required_pairs(pairs+[pairs[0]])


def test_conditional_profiles_are_not_published_as_full_convergence():
    module=publication()
    row=dict(status='complete',conditional_converged=True,free_time_converged=False)
    before=copy.deepcopy(row)
    assert module.full_pass(row,conditional=True) is False
    assert row==before
    assert module.full_pass(dict(status='complete',passed=True)) is True
    assert module.full_pass(dict(status='error',passed=True)) is False


def test_profile_controls_use_checked_base_identity_without_optional_role_label():
    module=publication();identity='control0::bias1_unsubtracted::sphere_rotating::control'
    item=dict(kind='control',source_identity=identity,
        task=dict(identity=identity,segment_id='control0',case_id='bias1_unsubtracted',model='sphere_rotating'))
    assert module.scientific_identity(item)==identity
    item['source_identity']='other::bias1_unsubtracted::sphere_rotating::control'
    with pytest.raises(ValueError):module.scientific_identity(item)


def test_only_conditional_controls_may_have_metadata_without_saved_arrays(tmp_path):
    module=publication();row=dict(kind='control')
    assert module.linearization_path(tmp_path,row,conditional=True) is None
    with pytest.raises(ValueError):module.linearization_path(tmp_path,row,conditional=False)
    with pytest.raises(ValueError):module.linearization_path(tmp_path,dict(kind='profile'),conditional=True)


def test_evidence_names_fit_filesystem_limits_and_do_not_alias_sources():
    module=publication();name='x'*245+'.json.gz'
    first=module.evidence_name(module.ROOT/'docs'/'first'/name)
    other=module.evidence_name(module.ROOT/'docs'/'second'/name)
    assert len(first.encode())<255 and first!=other and first.endswith('.json.gz')
