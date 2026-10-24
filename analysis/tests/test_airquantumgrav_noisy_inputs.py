# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest


@pytest.mark.parametrize('model',['sphere_rotating','sphere_still','flat_still'])
@pytest.mark.parametrize('profile',[False,True])
def test_noisy_material_exposes_only_measured_earlier_rows_and_no_true_initial_state(model,profile):
    import math
    import numpy as np
    from lll.airquantumgrav_noisy_inputs import construct,noise_settings
    from lll.airquantumgrav_height_training import recipe
    from lll.airquantumgrav_training_controls import generated_training
    from lll.airquantumgrav_weighted_controls import fixture_rows
    r=dict(recipe(),duration_s=40.,queries=39,noise=noise_settings())
    spec=dict(model=model,latitude_deg=55.,profile=profile,start=0,policy_id='reported-short-v1')
    charged={}
    def reserve(**values):
        for key,value in values.items():charged[key]=charged.get(key,0)+value
    noisy=construct(spec,r,reserve=reserve)
    base={k:v for k,v in spec.items() if k!='policy_id'}
    clean=generated_training(base,r,reserve=lambda **kwargs:None,height_profile='climb',gravity_model='inverse_square_height')
    rows=fixture_rows(clean['training_gps'],clean['times'][:clean['training_epochs']])
    assert set(noisy)=={'theta','dv','dt','times','training_rows','training_epochs','binding'}
    assert len(noisy['training_rows'])==26 and len(noisy['times'])==39
    assert not np.array_equal(noisy['theta'],clean['theta']) and not np.array_equal(noisy['dv'],clean['dv'])
    assert np.array_equal(noisy['dt'],clean['dt'])
    assert noisy['training_rows']!=rows
    assert noisy['binding']['gravity_anchor_height_m']==noisy['training_rows'][0]['height_m']
    assert noisy['binding']['gravity_anchor_source']=='first_noisy_training_receiver_height'
    assert math.isfinite(noisy['binding']['gravity_anchor_height_m'])
    assert not noisy['binding']['true_initial_state_supplied'] and not noisy['binding']['true_calibration_supplied']
    assert charged['constructed_intervals']==12000
    assert charged['noise_normal_variates']==18*12000+6*26+12
    assert charged['generated_samples']==12001+26


def test_later_noise_and_query_extension_cannot_change_earlier_noisy_material():
    import numpy as np
    from lll.airquantumgrav_noisy_inputs import construct,noise_settings
    from lll.airquantumgrav_height_training import recipe
    spec=dict(model='sphere_rotating',latitude_deg=55.,profile=False,start=0,policy_id='reported-short-v1')
    short=dict(recipe(),duration_s=40.,queries=39,noise=noise_settings())
    long=dict(short,duration_s=80.,queries=78)
    a=construct(spec,short,reserve=lambda **kwargs:None)
    b=construct(spec,long,reserve=lambda **kwargs:None)
    assert np.array_equal(a['theta'],b['theta'][:len(a['theta'])])
    assert np.array_equal(a['dv'],b['dv'][:len(a['dv'])])
    assert a['training_rows']==b['training_rows'][:len(a['training_rows'])]


def test_noisy_construction_requires_declared_noise_before_any_construction():
    from lll.airquantumgrav_noisy_inputs import construct
    from lll.airquantumgrav_height_training import recipe
    def no_work(**kwargs):raise AssertionError('invalid scope consumed its allowance')
    with pytest.raises(ValueError,match='noise'):
        construct(dict(model='sphere_rotating',latitude_deg=55.,profile=False,start=0,policy_id='reported-short-v1'),
            recipe(),reserve=no_work)
