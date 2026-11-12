# SPDX-License-Identifier: AGPL-3.0-or-later
"""Unconditional and receiver-conditioned scales share one noise operator."""

import pytest


def _operator():
    import numpy as np
    from lll.state_space_covariance import LinearInnovations

    steps = [dict(transition=np.eye(3)*.95, process_loading=np.eye(3)*.2,
                  observation=np.eye(3), white_loading=np.eye(3)*.1)
             for _ in range(8)]
    return LinearInnovations(
        steps, epoch_count=8, state_dimension=3, observation_dimension=3,
        initial_loading=np.eye(3)*.3, maximum_bytes=10000,
        design_is_fixed=True, error_distribution='gaussian')


def test_same_operator_scales_match_dense_unconditional_and_conditional():
    import numpy as np
    from lll.noise_conditioning_comparison import compare

    operator = _operator()
    covariance = operator.unwhiten(np.eye(24))
    covariance = covariance @ covariance.T
    earlier = covariance[:15, :15]
    cross = covariance[15:, :15]
    later = covariance[15:, 15:]
    conditional = later - cross @ np.linalg.solve(earlier, cross.T)
    metric = np.tile([2., 3., 4.], (3, 1))
    result = compare(operator, training_epochs=5, physical_scales=metric)

    def expected(matrix):
        variances = np.diag(matrix).reshape(3, 3) * metric**2
        return (float(np.sqrt(np.mean(variances[:, :2].sum(axis=1)))),
                float(np.sqrt(np.mean(variances[:, 2]))))

    assert result['unconditional']['horizontal_rms_scale_m'] == pytest.approx(expected(later)[0])
    assert result['unconditional']['height_rms_scale_m'] == pytest.approx(expected(later)[1])
    assert result['conditioned']['horizontal_rms_scale_m'] == pytest.approx(expected(conditional)[0])
    assert result['conditioned']['height_rms_scale_m'] == pytest.approx(expected(conditional)[1])
    assert result['conditioned']['horizontal_rms_scale_m'] < result['unconditional']['horizontal_rms_scale_m']
    assert result['confidence_calibrated'] is False
    assert result['scientific_decision'] == 'abstain'


@pytest.mark.parametrize('split,shape', [(0, (3, 3)), (8, (0, 3)),
                                         (5, (2, 3))])
def test_same_operator_scales_reject_invalid_support(split, shape):
    import numpy as np
    from lll.noise_conditioning_comparison import compare

    with pytest.raises(ValueError, match='complete later physical support'):
        compare(_operator(), training_epochs=split,
                physical_scales=np.ones(shape))
