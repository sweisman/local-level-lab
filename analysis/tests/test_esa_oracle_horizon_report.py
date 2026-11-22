"""Short-horizon scales preserve units and correlated-epoch caution."""

import numpy as np
import pytest


def test_prefix_horizon_scales_use_each_future_epoch_once():
    from lll.esa_oracle_horizon_report import prefix_scales
    values=np.array([[3.,1.,4.],[12.,4.,9.],[27.,9.,16.]])
    result=prefix_scales(values,(1,2,3))
    assert result['1']['horizontal_rms_scale_m']==2.
    assert result['2']['horizontal_rms_scale_m']==np.sqrt(10.)
    assert result['2']['vertical_rms_scale_m']==np.sqrt(6.5)
    assert result['3']['final_epoch_horizontal_scale_m']==6.


def test_prefix_horizon_scales_reject_missing_or_changed_support():
    from lll.esa_oracle_horizon_report import prefix_scales
    with pytest.raises(ValueError,match='future three-axis'):
        prefix_scales([[1.,2.,3.],[-1.,2.,3.]],(1,2))
    with pytest.raises(ValueError,match='ordered horizons'):
        prefix_scales([[1.,2.,3.]],(2,))


def test_long_training_crosscheck_uses_only_first_120_future_epochs():
    from lll.esa_oracle_horizon_report import long_training_crosscheck
    variances=[[4.,5.,9.]]*120+[[100.,100.,100.]]*280
    row=dict(version='same-operator-conditioning-comparison-v1',
             training_epochs=800,later_epochs=400,
             realized_noise_used=False,fitted_calibration_used=False,
             conditioned=dict(later_variance_neu_m2=variances,
                              horizontal_rms_scale_m=float(np.sqrt(142.7))),
             unconditional=dict(later_variance_neu_m2=variances,
                                horizontal_rms_scale_m=float(np.sqrt(142.7))))
    result=long_training_crosscheck(row)
    assert result['horizontal_rms_scale_m']==3.
    assert result['vertical_rms_scale_m']==3.
    with pytest.raises(ValueError,match='800 earlier'):
        long_training_crosscheck({**row,'training_epochs':799})
