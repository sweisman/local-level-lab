# SPDX-License-Identifier: AGPL-3.0-or-later
"""Backward compatibility and earlier-only generated height material."""
from pathlib import Path

import numpy as np
import pytest


@pytest.mark.parametrize('profile',(False,True))
def test_default_training_material_matches_archived_source_exactly(profile):
    from lll import airquantumgrav_training_controls as current
    from lll.studies.closed import ClosedStudy,load_python_reference
    closed=ClosedStudy(Path(__file__).resolve().parents[2],'docs/esa-weighted-training-controls')
    try:
        key='analysis/lll/airquantumgrav_training_controls.py';sha=closed.manifest['sources'][key]
        old=load_python_reference(closed.read('source-freeze/'+key,sha,raw=True),
            name='lll._height_material_reference_'+sha,sha256=sha)
    finally:closed.close()
    r=dict(current.recipe(),duration_s=2.,queries=9,query_start_s=.1,query_step_s=.2)
    spec=dict(model='sphere_still',latitude_deg=55.,profile=profile,start=0)
    before=old.generated_training(spec,r,reserve=lambda **v:None)
    after=current.generated_training(spec,r,reserve=lambda **v:None)
    assert set(before)==set(after)
    for key in before:np.testing.assert_array_equal(before[key],after[key],err_msg=key)


@pytest.mark.parametrize('profile',(False,True))
def test_height_material_exposes_only_earlier_positions_and_no_true_calibration(profile,monkeypatch):
    from lll import airquantumgrav_training_controls as module,airquantumgrav_observation_truth as observation
    r=dict(module.recipe(),duration_s=2.,queries=9,query_start_s=.1,query_step_s=.2)
    original=observation.receiver_samples;seen=[];charges=[]
    def receiver(model,times,**kwargs):
        seen.append(np.array(times));return original(model,times,**kwargs)
    monkeypatch.setattr(observation,'receiver_samples',receiver)
    value=module.generated_training(dict(model='sphere_still',latitude_deg=55.,profile=profile,start=0),r,
        reserve=lambda **v:charges.append(v),height_profile='climb',gravity_model='inverse_square_height')
    assert value['training_gps'].shape==(6,3)
    assert len(seen)==1 and np.array_equal(seen[0],value['times'][:6])
    assert not {'initial','parameters','later_gps','gravity_anchor_height_m'}&set(value)
    assert sum(v.get('generated_samples',0) for v in charges)==607
    assert sum(v.get('constructed_intervals',0) for v in charges)==600
    assert np.all(abs(value['training_gps'][:,2]-1500.)<5.)


def test_default_material_does_not_silently_expand_legacy_duration_allowance():
    from lll.airquantumgrav_training_controls import generated_training,recipe
    calls=[]
    with pytest.raises(ValueError):generated_training(dict(model='sphere_still',latitude_deg=55.,profile=False,start=0),
        dict(recipe(),duration_s=121.),reserve=lambda **v:calls.append(v))
    assert not calls


@pytest.mark.parametrize('model',('sphere_rotating','sphere_still','flat_still'))
def test_height_receiver_observations_use_independent_antenna_and_latency(model):
    from lll.airquantumgrav_observation_truth import receiver_samples,antenna,receiver_coordinates
    from lll.airquantumgrav_truth import truth
    times=np.array([.5,300.,1199.5]);arguments=dict(latitude_deg=55.,pattern='fast',removal=.35,
        height_profile='climb',gravity_model='inverse_square_height')
    actual=receiver_samples(model,times,sign=-1,**arguments)
    expected=antenna(truth(model,times-.0007,**arguments),sign=-1)
    np.testing.assert_array_equal(actual['position_world_m'],expected['position_world_m'])
    np.testing.assert_array_equal(actual['coordinates'],receiver_coordinates(expected['position_world_m'],model=model))
