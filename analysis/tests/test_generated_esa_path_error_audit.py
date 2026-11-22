"""A saved generated audit must separate receiver noise from path error."""

import pytest


def test_matched_error_decomposition_preserves_failed_physical_path():
    from lll.generated_esa_path_error_audit import summarize

    receiver = [[0.2, 0., 0.]] * 2
    fitted = [[12., 0., 0.], [12., 0., 0.],
              [30., 0., 0.], [30., 0., 0.]]
    versus_receiver = [[11.8, 0., 0.], [11.8, 0., 0.]]
    result = summarize(receiver, fitted, versus_receiver, cut=2)
    assert result['training']['receiver_to_truth']['horizontal_rms_m'] == pytest.approx(.2)
    assert result['training']['fitted_to_truth']['horizontal_rms_m'] == pytest.approx(12.)
    assert result['prediction']['fitted_to_truth']['horizontal_rms_m'] == pytest.approx(30.)
    assert result['training']['fitted_to_receiver']['horizontal_rms_m'] == pytest.approx(11.8)


def test_inconsistent_saved_errors_are_rejected():
    from lll.generated_esa_path_error_audit import summarize

    with pytest.raises(ValueError, match='same physical basis'):
        summarize([[1., 0., 0.]] * 4, [[2., 0., 0.]] * 4,
                  [[2., 0., 0.]] * 2, cut=2)


def test_closed_generated_pilot_audit_preserves_failed_outcomes():
    from lll.generated_esa_path_error_audit import build

    report = build('.')
    assert report['tasks_total'] == 2
    assert report['numerical_passing_fits'] == 2
    assert report['physical_passing_tasks'] == 0
    assert report['new_fits'] == 0
    assert report['original_reads'] == 0
    assert report['protected_reads'] == 0
    assert all(row['training']['receiver_to_truth']['horizontal_rms_m'] < 2
               for row in report['laws'].values())
