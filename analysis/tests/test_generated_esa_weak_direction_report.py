"""Saved-whitened-Jacobian calibration direction audit."""

import numpy as np
import pytest


def test_weak_direction_identifies_smallest_singular_axis():
    from lll.generated_esa_weak_direction_report import diagnose

    design = np.diag([10., 2., .5])
    result = diagnose(design, ['a', 'b', 'c'], np.zeros(3))
    assert result['rank'] == 3
    assert result['weakest_singular_value'] == .5
    assert result['weakest_local_inverse_scale'] == 2.
    assert result['top_loadings'][0]['parameter'] == 'c'
    np.testing.assert_allclose(result['weakest_vector'], [0., 0., 1.])


def test_weak_direction_rejects_bad_saved_jacobian():
    from lll.generated_esa_weak_direction_report import diagnose

    with pytest.raises(ValueError):
        diagnose(np.zeros((3, 2)), ['a', 'b'], np.zeros(3))
    with pytest.raises(ValueError):
        diagnose(np.eye(2), ['a'], np.zeros(2))
    with pytest.raises(ValueError):
        diagnose(np.eye(2), ['a', 'b'], np.ones(1))


def test_closed_pilot_has_same_weak_axis_but_no_physical_pass():
    from pathlib import Path
    from lll.generated_esa_weak_direction_report import build

    result = build(Path(__file__).resolve().parents[2])
    assert result['verified'] is True
    assert result['tasks_total'] == 2
    assert result['original_physical_passing'] == 0
    assert result['weak_direction_abs_similarity'] > .99
    assert result['scientific_decision'] == 'abstain'
    assert result['new_fits'] == result['original_reads'] == 0
    assert result['protected_reads'] == 0
