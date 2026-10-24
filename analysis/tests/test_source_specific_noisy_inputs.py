# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest


@pytest.mark.parametrize('model',['sphere_rotating','sphere_still','flat_still'])
@pytest.mark.parametrize('profile',[False,True])
def test_point_input_constructor_matches_error_law_and_precharges_each_draw(model,profile):
    from lll.airquantumgrav_noisy_inputs import construct,rate_point_noise_settings,error_law,construction_limits
    from lll.airquantumgrav_height_training import recipe
    from lll.linear_point_noise import LinearPointNoise
    import numpy as np
    r=dict(recipe(),duration_s=2.,queries=9,query_start_s=.1,query_step_s=.2,noise=rate_point_noise_settings())
    spec=dict(model=model,latitude_deg=55.,profile=profile,start=0,policy_id='reported-short-v1')
    charges={}
    def reserve(**counts):
        for key,value in counts.items():charges[key]=charges.get(key,0)+value
    material=construct(spec,r,reserve=reserve)
    assert material['binding']['input_error_law']=='linear_rate_points'
    assert charges==construction_limits(r)
    assert len(material['theta'])==600 and len(material['training_rows'])==6
    assert material['binding']['later_receiver_positions_generated'] is False
    law=error_law(r['noise']);assert isinstance(law,LinearPointNoise)
    np.testing.assert_allclose(law.roots[0]@law.roots[0].T,
        np.eye(3)*r['noise']['gyro_point_std_rads']**2,rtol=1e-15,atol=0)


def test_increment_error_provider_keeps_existing_settings():
    from lll.airquantumgrav_noisy_inputs import error_law,noise_settings
    from lll.ilvis0_noise_history import PacketNoise
    assert isinstance(error_law(noise_settings()),PacketNoise)


def test_source_specific_provider_rejects_changed_settings():
    from lll.airquantumgrav_noisy_inputs import error_law,rate_point_noise_settings
    with pytest.raises(ValueError):error_law(dict(rate_point_noise_settings(),gyro_point_std_rads=1.))


def test_point_input_extension_preserves_earlier_receiver_and_imu():
    import numpy as np
    from lll.airquantumgrav_noisy_inputs import construct,rate_point_noise_settings
    from lll.airquantumgrav_height_training import recipe
    short=dict(recipe(),duration_s=2.,queries=9,query_start_s=.1,query_step_s=.2,noise=rate_point_noise_settings())
    long=dict(short,duration_s=4.,queries=18)
    spec=dict(model='sphere_rotating',latitude_deg=55.,profile=False,start=0,policy_id='reported-short-v1')
    a=construct(spec,short,reserve=lambda **counts:None);b=construct(spec,long,reserve=lambda **counts:None)
    for key in ('theta','dv','dt'):np.testing.assert_array_equal(a[key],b[key][:len(a[key])])
    assert a['training_rows']==b['training_rows'][:len(a['training_rows'])]
