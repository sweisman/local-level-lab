"""Common ESA residual and method spread are kept distinct."""
import numpy as np
import pytest


def test_common_residual_decomposition_keeps_shared_error_and_method_spread():
    from lll.esa_rate_refit_common_residual import decompose

    receiver = np.array([[0., 0., 100.] for _ in range(9)])
    shared = receiver.copy()
    shared[:, 2] += 2.
    routes = {f'{method}-{law}': shared.copy()
              for method in ('linear_points', 'left_hold', 'right_hold')
              for law in ('increment', 'point')}
    result = decompose(routes, receiver, training_epochs=6, block_epochs=3)
    assert result['increment']['training']['shared_vertical_rms_m'] == pytest.approx(2.)
    assert result['point']['prediction']['maximum_method_horizontal_spread_m'] == 0.
    assert len(result['point']['blocks']) == 3
    routes['left_hold-point'] = receiver[:8]
    with pytest.raises(ValueError, match='matched six'):
        decompose(routes, receiver, training_epochs=6, block_epochs=3)
