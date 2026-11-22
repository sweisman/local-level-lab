"""Earlier-only paired alignment is checked on later, untouched samples."""

import numpy as np
import pytest


def _seconds(values):
    from lll.ilvis0_stretch_analytics import DPH
    return {i: {'raw_aircraft': (v / DPH).tolist(), 'duration_s': 1.0}
            for i, v in enumerate(values)}


def test_known_rotation_and_offset_predict_later_samples():
    from lll.ilvis0_pair_alignment import compare_halves

    rng = np.random.default_rng(21)
    right = rng.normal(size=(160, 3)) * [4.0, 7.0, 3.0]
    angle = np.deg2rad(3.0)
    rotation = np.array([[np.cos(angle), -np.sin(angle), 0.0],
                         [np.sin(angle), np.cos(angle), 0.0],
                         [0.0, 0.0, 1.0]])
    left = right @ rotation.T + [0.2, -0.3, 0.1]
    result = compare_halves(_seconds(left), _seconds(right),
                            begin_s=0, end_s=160)
    assert result['training_seconds'] == result['heldout_seconds'] == 80
    assert result['rotation_identifiable'] is True
    assert result['fitted_rotation_angle_deg'] == pytest.approx(3.0, abs=1e-7)
    assert result['heldout_rotated_vector_rms_dph'] == pytest.approx(0, abs=1e-10)
    assert result['heldout_offset_only_vector_rms_dph'] > 0.1
    assert result['heldout_windows'][60]['complete_windows'] == 1
    assert result['heldout_windows'][60]['rotated_vector_rms_dph'] == pytest.approx(
        0, abs=1e-10)


def test_rank_deficient_motion_abstains_from_rotation():
    from lll.ilvis0_pair_alignment import compare_halves

    right = np.column_stack((np.arange(160, dtype=float),
                             np.zeros(160), np.zeros(160)))
    left = right + [0.1, 0.2, 0.3]
    result = compare_halves(_seconds(left), _seconds(right),
                            begin_s=0, end_s=160)
    assert result['rotation_identifiable'] is False
    assert result['heldout_rotated_vector_rms_dph'] is None
    assert result['heldout_offset_only_vector_rms_dph'] == pytest.approx(0)


def test_midpoint_and_missing_seconds_are_not_reselected():
    from lll.ilvis0_pair_alignment import compare_halves

    rng = np.random.default_rng(42)
    right = _seconds(rng.normal(size=(160, 3)))
    left = _seconds(rng.normal(size=(160, 3)))
    del right[90]
    result = compare_halves(left, right, begin_s=0, end_s=160)
    assert result['training_seconds'] == 80
    assert result['heldout_seconds'] == 79
    assert result['split_utc_week_s'] == 80
    assert result['heldout_windows'][10]['complete_windows'] == 7
    assert result['heldout_windows'][60]['complete_windows'] == 0

    with pytest.raises(ValueError, match='at least 60'):
        compare_halves(left, right, begin_s=0, end_s=110)


def test_later_change_cannot_update_earlier_fitted_alignment():
    from lll.ilvis0_pair_alignment import compare_halves

    rng = np.random.default_rng(5)
    values = rng.normal(size=(160, 3))
    right = _seconds(values)
    left = _seconds(values + [0.2, 0.1, -0.1])
    first = compare_halves(left, right, begin_s=0, end_s=160)
    for second in range(80, 160):
        left[second]['raw_aircraft'][0] += 1.0
    changed = compare_halves(left, right, begin_s=0, end_s=160)
    assert np.allclose(changed['fitted_rotation_matrix'],
                       first['fitted_rotation_matrix'])
    assert changed['fitted_rotated_offset_dph'] == pytest.approx(
        first['fitted_rotated_offset_dph'])
    assert changed['heldout_rotated_vector_rms_dph'] > first[
        'heldout_rotated_vector_rms_dph']
