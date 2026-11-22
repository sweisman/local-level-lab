import math

import numpy as np
import pytest

from lll.generated_esa_noise_floor_audit import expected_horizontal_rms, build


def test_expected_horizontal_rms_uses_local_metric_and_all_future_epochs():
    covariance = np.zeros((2, 3, 3))
    covariance[:, 0, 0] = [1, 9]
    covariance[:, 1, 1] = [4, 16]
    covariance[:, 2, 2] = 1
    truth = np.array([[0., 0., 0.], [0., 0., 0.]])
    value = expected_horizontal_rms(covariance, truth)
    from lll.airquantumgrav_truth import A, E2
    north = A * (1-E2)
    east = A
    assert value == pytest.approx(math.sqrt((5*north*north+10*east*east)))


def test_expected_horizontal_rms_rejects_incomplete_covariance():
    with pytest.raises(ValueError):
        expected_horizontal_rms(np.zeros((2, 3, 3)), np.zeros((2, 3)))


def test_closed_cohort_noise_floor_exceeds_inherited_screen():
    report = build('.')
    assert report['tasks_total'] == 8
    assert report['checked_tasks'] == 8
    assert report['noise_floor_above_coded_screen'] == 8
    assert report['new_fits'] == report['original_reads'] == 0
    assert report['scientific_decision'] == 'abstain'
    assert all(row['conditional_horizontal_rms_m'] < row['raw_horizontal_rms_m']
               for row in report['rows'].values())
