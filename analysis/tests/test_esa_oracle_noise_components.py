"""The shared component reconstruction keeps both noise laws distinct."""

import numpy as np
import pytest


@pytest.mark.parametrize('law',('increment','point'))
def test_reconstructed_components_sum_to_generated_measurements(law):
    from lll.esa_oracle_noise_components import reconstruct_components

    clean=dict(theta=np.zeros((4,3)),dv=np.zeros((4,3)),
               dt=np.full(4,1/300))
    result=reconstruct_components(clean,law,seed=7)
    for kind,name in (('gyro','theta'),('accel','dv')):
        components=result['noise'][kind]
        assert np.array_equal(result[name],
            clean[name]+components['white_increments']+
            components['bias_increments'])


def test_reconstructed_components_reject_undeclared_law():
    from lll.esa_oracle_noise_components import reconstruct_components

    with pytest.raises(ValueError,match='declared noise law'):
        reconstruct_components({},'other',seed=7)
