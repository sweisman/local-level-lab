"""Controls for one shared accelerometer calibration over alternative windows."""

import numpy as np

from lll import ilvis0_adaptive_calibration
from lll.ilvis0_receiver_force import MATCHED_MODELS


def compare(required, *, optional=False, maximum_boxes=63):
    choices = [[2.], [2., 4., None] if optional else [2., 4.]]
    assessment = dict(
        model_order=MATCHED_MODELS, branches=[(0, 2.), (1, 2.), (1, 4.)],
        targets=[dict(possible_choices_s=widths) for widths in choices],
        gyro_observations_used=False, fused_navigation_used=False,
        magnitude_ranges_mps2=dict(zip(MATCHED_MODELS, required, strict=True)))
    return ilvis0_adaptive_calibration.compare(
        assessment, measured_specific_force=[[10., 0., 0.], [10., 0., 0.]],
        measurement_error_mps2=np.zeros((2, 3)),
        calibration_bounds=[[0., 0.]]*3 + [[-2., 2.], [0., 0.], [0., 0.]],
        maximum_boxes=maximum_boxes)


COMPATIBLE = [[9.99, 10.01], [11.2, 11.3], [9.99, 10.01]]
INCOMPATIBLE = [[9.99, 10.01], [10.9, 11.1], [11.2, 11.3]]


def test_one_shared_calibration_must_work_at_all_required_targets():
    result = compare([COMPATIBLE, INCOMPATIBLE, COMPATIBLE, INCOMPATIBLE])
    fits = result['candidates']
    assert [fits[model]['status'] for model in MATCHED_MODELS] == [
        'scalar_compatible', 'scalar_excluded', 'scalar_compatible', 'scalar_excluded']
    for model in MATCHED_MODELS[::2]:
        assert fits[model]['calibration'] == [0.]*6
        assert fits[model]['matching_windows_s'] == [[2.], [4.]]
    assert result['attitude_identified'] is False
    assert result['scientific_decision'] == 'abstain'


def test_budget_exhaustion_and_possible_abstention_do_not_exclude_a_model():
    results = compare([INCOMPATIBLE]*4, maximum_boxes=1)
    assert {row['status'] for row in results['candidates'].values()} == {'budget_unresolved'}
    assert {row['boxes_evaluated'] for row in results['candidates'].values()} == {1}
    results = compare([INCOMPATIBLE]*4, optional=True)
    assert {row['status'] for row in results['candidates'].values()} == {'scalar_compatible'}
    assert results['required_target_indices'] == [0]


def test_common_gain_and_offset_work_across_different_unknown_orientations():
    history = np.array([[0., 10., 0.], [-10., 0., 0.], [0., 0., -10.]])
    gain = np.array([.012, -.008, .004])
    bias = np.array([.07, -.03, .02])
    required = [[9.999, 10.001]]*3
    assessment = dict(model_order=MATCHED_MODELS, branches=[(j, 2.) for j in range(3)],
                      targets=[dict(possible_choices_s=[2.]) for _ in range(3)],
                      gyro_observations_used=False, fused_navigation_used=False,
                      magnitude_ranges_mps2={model: required for model in MATCHED_MODELS})
    point = np.r_[gain, bias]
    result = ilvis0_adaptive_calibration.compare(
        assessment, measured_specific_force=history*(1.+gain)+bias,
        measurement_error_mps2=np.zeros((3, 3)),
        calibration_bounds=np.column_stack((point-.0001, point+.0001)), maximum_boxes=1)
    for row in result['candidates'].values():
        assert row['status'] == 'scalar_compatible'
        np.testing.assert_allclose(row['calibration'], point, rtol=0., atol=1e-14)
