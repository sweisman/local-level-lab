import numpy as np
import pytest

from lll.esa_error_shape_transfer import fit_correction


def test_constant_acceleration_transfers_with_no_later_outcome_leakage():
    time = np.arange(1., 21.)
    design = np.column_stack((np.ones(len(time)), time, .5*time**2))
    expected = np.array([[1., 2., 3.], [.001, -.002, .003], [.3, -.2, .001]])
    error = design@expected
    exact = fit_correction(design, error, prefix=12)
    modified = error.copy()
    modified[12:] += 25.
    altered = fit_correction(design, modified, prefix=12)
    assert np.array(exact['coefficients']) == pytest.approx(expected)
    assert exact['coefficients'] == altered['coefficients']
    assert exact['later_rms_neu_m'] == pytest.approx([0., 0., 0.], abs=1e-12)
    assert altered['later_rms_neu_m'] == pytest.approx([25., 25., 25.])


def test_future_turn_cannot_supply_a_prefix_coefficient():
    time = np.arange(1., 21.)
    design = np.column_stack((np.ones(len(time)), time, np.maximum(time-12., 0.)**2))
    result = fit_correction(design, np.ones((len(time), 3)), prefix=12)
    assert result['status'] == 'unidentifiable'
    assert result['prefix_rank'] == 2
    assert result['coefficients'] is None
