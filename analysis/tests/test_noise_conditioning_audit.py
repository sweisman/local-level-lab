# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved-result audit checks; these never rebuild the numerical operator."""

import pytest


def _fixtures():
    before = [[25., 25., 9.]] * 400
    after = [[16., 16., 4.]] * 400
    comparison = dict(version='same-operator-conditioning-comparison-v1',
                      training_epochs=800, later_epochs=400,
                      unconditional=dict(conditioning_epochs=0,
                                         horizontal_rms_scale_m=50**.5,
                                         height_rms_scale_m=3.,
                                         later_variance_neu_m2=before),
                      conditioned=dict(conditioning_epochs=800,
                                       horizontal_rms_scale_m=32**.5,
                                       height_rms_scale_m=2.,
                                       later_variance_neu_m2=after),
                      realized_noise_used=False,
                      fitted_calibration_used=False,
                      confidence_calibrated=False,
                      scientific_decision='abstain')
    result = dict(passed=True, training_epochs=800, later_epochs=400,
                  unconditional_horizontal_rms_scale_m=50**.5,
                  conditioned_horizontal_rms_scale_m=32**.5,
                  unconditional_height_rms_scale_m=3.,
                  conditioned_height_rms_scale_m=2.,
                  native_calls_attempted=361200,
                  original_reads=0, protected_reads=0,
                  optimizer_starts=0, random_draws=0,
                  prediction_qualified=False,
                  confidence_calibrated=False,
                  scientific_decision='abstain')
    descriptor = dict(law='increment', model='sphere_rotating',
                      receiver_observation_epochs=800,
                      confidence_calibrated=False,
                      original_reads=0, protected_reads=0)
    return result, comparison, descriptor


def test_conditioning_saved_audit_checks_scales_and_no_decision():
    from lll.noise_conditioning_audit import validate

    result, comparison, descriptor = _fixtures()
    report = validate(result, comparison, descriptor)
    assert report['verified'] is True
    assert report['unconditional_horizontal_rms_scale_m'] == 50**.5
    assert report['conditioned_horizontal_rms_scale_m'] == 32**.5
    assert report['scientific_decision'] == 'abstain'


def test_conditioning_saved_audit_rejects_tampered_curve_or_scale():
    from lll.noise_conditioning_audit import validate

    result, comparison, descriptor = _fixtures()
    comparison['conditioned']['later_variance_neu_m2'][0][0] = 30.
    with pytest.raises(ValueError):
        validate(result, comparison, descriptor)
    result, comparison, descriptor = _fixtures()
    result['conditioned_horizontal_rms_scale_m'] = 1.
    with pytest.raises(ValueError):
        validate(result, comparison, descriptor)
