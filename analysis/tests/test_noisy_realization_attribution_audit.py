# SPDX-License-Identifier: AGPL-3.0-or-later
"""Read-only checks for the generated same-realization attribution audit."""

import pytest


def test_attribution_audit_requires_closed_study_before_numerical_import(
        tmp_path, monkeypatch):
    from lll.studies import closed
    from lll.noisy_realization_attribution_audit import inspect

    requested = []

    def refuse(root, prefix):
        requested.append(prefix)
        raise ValueError('closed study required')

    monkeypatch.setattr(closed, 'ClosedStudy', refuse)
    with pytest.raises(ValueError, match='closed study required'):
        inspect(tmp_path, prefix='data/not-closed')
    assert requested == ['data/not-closed']


def test_attribution_audit_replays_saved_physical_errors_and_rejects_tampering():
    import copy
    import numpy as np
    from lll.noisy_realization_attribution import construction_limits
    from lll.noisy_realization_attribution_audit import check_case
    from lll.airquantumgrav_truth import truth, A, E2, DISC_RADIUS
    from lll.airquantumgrav_observation_truth import receiver_samples, start
    from lll.airquantumgrav_training_report import saved_position_errors
    from lll.airquantumgrav_scoring import sections

    times = (.5 + np.arange(1200)).tolist()
    model = 'sphere_rotating'
    arguments = dict(model=model, latitude_deg=55., pattern='fast',
                     removal=0., height_profile='climb',
                     gravity_model='inverse_square_height')
    answer = receiver_samples(times=times, sign=1, **arguments)
    origin = start(truth(times=np.array([0.]), **arguments),
                   model=model, sign=1)
    coordinates = answer['coordinates'].tolist()
    observed = {key: value.tolist() for key, value in answer.items()}
    errors = saved_position_errors(
        coordinates, observed, model=model,
        constants=dict(A=A, E2=E2, DISC_RADIUS=DISC_RADIUS))
    judged = sections(errors, 800)
    hashes = {key: 'a' * 64 for key in ('theta', 'dv', 'dt', 'times')}
    parents = [f'parent-{index}' for index in range(4)]
    task = dict(payload=dict(model=model, latitude_deg=55., profile=False,
                             hashes=hashes, parent_identities=parents),
                limits=dict(packet_visits=360000 * 1200))
    proof = dict(parent_manifest_sha256='b' * 64,
                 parent_summary_sha256='c' * 64)
    historical = dict(query_start_s=.5, query_step_s=1., queries=1200,
                      pattern='fast', height_profile='climb',
                      gravity_model='inverse_square_height')
    saved = {
        'input-binding.json': dict(parent_manifest_sha256='b' * 64,
                                   parent_summary_sha256='c' * 64,
                                   full_array_sha256=hashes,
                                   parent_identities=parents,
                                   original_reads=0, protected_reads=0),
        'known-corrections.json': dict(
            initial={key: value.tolist() if hasattr(value, 'tolist')
                     else value for key, value in origin['initial'].items()},
            parameters=origin['parameters'], gravity_mps2=origin['gravity_mps2'],
            removal=0., known_corrections_supplied_not_estimated=True),
        'forecast.json': dict(times_s=times, coordinates=coordinates,
                              known_corrections_supplied_not_estimated=True,
                              prediction_receiver_positions_used=False,
                              continuous_propagation_without_gps_reset=True),
        'scoring-observations.json': observed,
        'scores.json': dict(times_s=times, errors_neu_m=errors,
                            training_epochs=800, prediction_epochs=400,
                            score_reference='generated noiseless physical truth',
                            later_receiver_noise_added=False, **judged),
        'compilation.json': dict(source_sha256='d' * 64, compiler='cc')}
    limits = construction_limits()
    result = dict(passed=True, technical_passed=True,
                  accuracy_all_sections=True, training=judged['training'],
                  prediction=judged['prediction'], native_calls=1,
                  constructed_intervals=limits['constructed_intervals'],
                  generated_samples=limits['generated_samples'],
                  noise_normal_variates=limits['noise_normal_variates'],
                  original_reads=0, protected_reads=0,
                  oracle_not_real_flight_estimator=True,
                  confidence_calibrated=False,
                  scientific_decision='abstain')
    environment = dict(native_source_sha256='d' * 64,
                       compilers=dict(cc='cc'))
    operations = dict(value=1, tangent=0, packet_visits=360000 * 1200)
    checked = check_case(task, result, saved, proof=proof,
                         historical=historical, operations=operations,
                         construction=limits, environment=environment)
    assert checked['accurate'] is True
    damaged = copy.deepcopy(saved)
    damaged['scores.json']['errors_neu_m'][900][0] += 1.
    with pytest.raises(ValueError, match='physical errors differ'):
        check_case(task, result, damaged, proof=proof,
                   historical=historical, operations=operations,
                   construction=limits, environment=environment)


def test_attribution_report_distinguishes_technical_and_physical_outcomes():
    from lll.noisy_realization_attribution_audit import render

    report = dict(verified=True, qualified=True, total=6, complete=6,
                  accurate=2, comparisons=[
                      dict(model='sphere_rotating', profile=False,
                           oracle_prediction=dict(horizontal_rms_m=3.,
                                                  vertical_rms_m=4.),
                           original_fits=[dict(prediction=dict(
                               horizontal_rms_m=value, vertical_rms_m=20.))
                               for value in (80., 81., 82., 83.)])])
    page = render(report)
    assert '6/6' in page
    assert '2' in page
    assert '3 m' in page
    assert '80–83 m' in page
    assert 'generated' in page.lower()
    assert 'not aircraft evidence' in page.lower()
