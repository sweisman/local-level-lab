"""Immutable eight-case generated cohort report and denominator checks."""

import pytest


def test_physical_accuracy_checks_all_sections_and_dimensions():
    from lll.generated_esa_bounded_cohort_report import physical_accuracy

    limits = dict(horizontal_rms_m=.1, vertical_rms_m=.1,
                  maximum_3d_m=.5)
    scores = dict(training=dict(horizontal_rms_m=.01,
                                vertical_rms_m=.02, maximum_3d_m=.2),
                  prediction=dict(horizontal_rms_m=.09,
                                  vertical_rms_m=.08, maximum_3d_m=.4))
    assert physical_accuracy(scores, limits) is True
    assert physical_accuracy(dict(scores, prediction=dict(
        scores['prediction'], vertical_rms_m=.11)), limits) is False
    with pytest.raises(ValueError):
        physical_accuracy(dict(scores, training={}), limits)


def test_wording_gap_is_detected_without_changing_coded_screen():
    from lll.generated_esa_bounded_cohort_report import wording_gap

    assert wording_gap(dict(training=dict(horizontal_rms_m=5.),
                            prediction=dict(horizontal_rms_m=12.))) is True
    assert wording_gap(dict(training=dict(horizontal_rms_m=.05),
                            prediction=dict(horizontal_rms_m=11.))) is False


def test_sealed_pilot_artifacts_match_reporter_physical_schema():
    from pathlib import Path
    from lll.generated_esa_bounded_cohort_report import physical_accuracy
    from lll.generated_esa_bounded_pilot_v2 import ID, recipe
    from lll.studies.closed import ClosedStudy

    root = Path(__file__).resolve().parents[2]
    study = ClosedStudy(root, 'data/' + ID)
    try:
        source = recipe()
        assert source['accuracy'] == dict(horizontal_rms_m=.1,
                                          vertical_rms_m=.1,
                                          maximum_3d_m=.5)
        for law in ('increment', 'point'):
            scores = study.artifact(law, 'scores.json')
            original = study.envelope(law)['result']
            fit = study.artifact(law, 'fit.json')
            assert bool(physical_accuracy(scores, source['accuracy'])
                        and fit['converged']) is original['original_prediction_passed']
    finally:
        study.close()


def test_closed_cohort_keeps_all_eight_and_separate_outcomes():
    from pathlib import Path
    from lll.generated_esa_bounded_cohort_report import build

    result = build(Path(__file__).resolve().parents[2])
    assert result['verified'] is True
    assert result['tasks_total'] == result['technical_passing'] == 8
    assert result['numerical_converged'] == 8
    assert result['coded_accuracy_metrics_passing'] == 0
    assert result['known_truth_all_coordinate_coverage'] == 8
    assert result['horizontal_wording_gap_cases'] == 0
    assert result['new_fits'] == result['original_reads'] == 0
    assert result['protected_reads'] == 0
