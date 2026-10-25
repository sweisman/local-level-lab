# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest


def example():
    import numpy as np
    from lll.state_space_covariance import LinearInnovations
    steps=[dict(transition=np.eye(3)*.95,process_loading=np.eye(3)*.2,
        observation=np.eye(3),white_loading=np.eye(3)*.1) for _ in range(8)]
    op=LinearInnovations(steps,epoch_count=8,state_dimension=3,observation_dimension=3,
        initial_loading=np.eye(3)*.3,maximum_bytes=10000,design_is_fixed=True,error_distribution='gaussian')
    return op


def test_known_calibration_benchmark_matches_dense_conditional_second_moments():
    import numpy as np
    from lll.prediction_error_benchmark import summarize
    op=example();l=op.unwhiten(np.eye(24));c=l@l.T;k=np.linalg.solve(c[:15,:15],c[:15,15:]).T
    conditional=c[15:,15:]-k@c[:15,15:];units=np.tile([2.,3.,4.],(3,1))
    variances=np.diag(conditional).reshape(3,3)*units**2
    r=summarize(op,training_epochs=5,nominal_position_scales=units,
        accuracy_limits=dict(horizontal_rms_m=10.,vertical_rms_m=30.))
    assert r['horizontal_expected_squared_rms_m2']==pytest.approx(float(np.mean(variances[:,:2].sum(axis=1))))
    assert r['vertical_expected_squared_rms_m2']==pytest.approx(float(np.mean(variances[:,2])))
    assert r['sqrt_expected_horizontal_squared_rms_m']==pytest.approx(np.sqrt(r['horizontal_expected_squared_rms_m2']))
    np.testing.assert_allclose(r['endpoint_standard_deviation_neu_m'],np.sqrt(variances[-1]))
    assert r['is_expected_realized_rms'] is False and r['known_calibration_benchmark'] is True
    assert r['confidence_calibrated'] is False and r['scientific_decision']=='abstain'


@pytest.mark.parametrize('bad',['split','metric','limits'])
def test_error_benchmark_requires_complete_declared_metric_and_screen(bad):
    import numpy as np
    from lll.prediction_error_benchmark import summarize
    args=dict(training_epochs=5,nominal_position_scales=np.ones((3,3)),
        accuracy_limits=dict(horizontal_rms_m=10.,vertical_rms_m=30.))
    if bad=='split':args['training_epochs']=8
    elif bad=='metric':args['nominal_position_scales']=np.ones((2,3))
    else:args['accuracy_limits']['horizontal_rms_m']=-1.
    with pytest.raises(ValueError):summarize(example(),**args)
