# SPDX-License-Identifier: AGPL-3.0-or-later
from copy import deepcopy
import pytest


def test_metadata_keeps_four_laws_and_separate_rng_roles():
    from lll.ilvis0_dense_observations import plan,stream_spec
    p=plan()
    assert len(p['laws'])==4 and p['training_times_s']==list(map(float,range(2,291)))
    assert p['future_times_s']==list(map(float,range(292,439)))
    streams=[stream_spec(m,b,l,r) for m in range(3) for b in (False,True) for l in range(4) for r in (0,1)]
    assert len({tuple(s['spawn_key']) for s in streams})==48
    assert {s['bit_generator'] for s in streams}=={'PCG64DXSM'}


@pytest.mark.parametrize('args',[(3,False,0,0),(0,1,0,0),(0,False,4,0),(0,False,0,2)])
def test_metadata_refuses_unregistered_streams(args):
    from lll.ilvis0_dense_observations import stream_spec
    with pytest.raises(ValueError):stream_spec(*args)


@pytest.mark.parametrize('law',range(4))
def test_training_draw_is_reproducible_and_future_draw_preserves_its_prefix(law):
    from lll.ilvis0_dense_observations import training_noise,complete_noise
    earlier=training_noise(model=1,profile=True,law_index=law)
    assert earlier==training_noise(model=1,profile=True,law_index=law)
    assert len(earlier['error_m'])==289 and earlier['future_innovations_drawn'] is False
    completed=complete_noise(earlier)
    assert completed['training_prefix_bitwise_equal'] and len(completed['future_error_m'])==147
    assert completed['training_stream']!=completed['future_stream']
    assert completed['error_law_is_device_estimate'] is False
    damaged=deepcopy(earlier);damaged['error_m'][0][0]+=1e-6
    with pytest.raises(ValueError,match='training'):
        complete_noise(damaged)


@pytest.mark.parametrize('law',range(4))
def test_noise_transform_matches_independent_dense_covariance(law):
    import numpy as np
    from lll.ilvis0_dense_observations import _transform,plan
    from lll.ilvis0_receiver_distance import receiver_spec,joint_recipe
    from lll.ilvis0_inertial_error import joint_covariance
    from lll.ilvis0_error_model import factor
    settings=joint_recipe();tau,q=plan()['laws'][law];times=np.array([2.,3.,7.,10.,16.]);z=np.arange(15.)/11.-.7
    actual=_transform(times,z,law_index=law,clock_s=.25)
    cov=joint_covariance(times+.25,receiver_spec(tau),origin_s=settings['noise_origin_s'],
        accel_psd=np.eye(3)*settings['accel_psd'],gyro_psd=np.eye(3)*q,coupling=settings['coupling'])
    np.testing.assert_allclose(np.asarray(actual['error_m']).ravel(),factor(cov)@z,rtol=3e-10,atol=2e-10)
    assert actual['mean_parameters_fitted']==0
