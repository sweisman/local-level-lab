"""A saved stopping audit must not turn a failed fit into a passing one."""

import pytest

from lll.esa_matrix_stopping_geometry import summarize_fit


def test_saved_linearization_and_rejected_step_remain_separate():
    fit = dict(
        converged=False,
        local_linearization=dict(
            residual=[100., 2., 0.],
            jacobian=[[0., 0.], [1., 0.], [0., 1.]],
            normalized_parameters=[0., 0.],
        ),
        step_history=[dict(method='full_bounded', accepted=False,
                           predicted_reduction=3., actual_reduction=-1.)],
        stability_probe=dict(position_rms_neu_m=[.0015, .0005, .0001],
                             position_rms_tolerance_m=.001),
    )
    report = summarize_fit(fit)
    assert report['saved_converged'] is False
    assert report['scientific_decision'] == 'abstain'
    assert report['linear_predicted_reduction_direct'] == pytest.approx(3.)
    assert report['linear_predicted_reduction_stable'] == pytest.approx(3.)
    assert report['last_rejected_actual_reduction'] == -1.
    assert report['position_rms_ratio'] == pytest.approx(1.5)


def test_saved_audit_rejects_a_missing_full_step():
    fit = dict(converged=False,
               local_linearization=dict(residual=[1.], jacobian=[[1.]],
                                        normalized_parameters=[0.]),
               step_history=[],
               stability_probe=dict(position_rms_neu_m=[0., 0., 0.],
                                    position_rms_tolerance_m=.001))
    with pytest.raises(ValueError, match='rejected full step'):
        summarize_fit(fit)
