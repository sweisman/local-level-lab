"""The known-answer report keeps numerical failures in the record."""

import pytest


def _fit(*, converged=True):
    return dict(converged=converged, stopping_rule_verified=converged,
        active_bounds=[], active_parameters=['one'], residual_sum_squares=2.,
        local_linearization=dict(
            convention='whitened residual derivative by normalized parameter',
            residual=[0., 1., 0., -1., 0., 0.],
            jacobian=[[1.], [0.], [0.], [0.], [0.], [0.]]))


def test_control_report_keeps_nonconverged_fit_without_reference():
    from lll.esa_fit_adjusted_control_report import score_candidate

    result = score_candidate(_fit(converged=False),
        dict(converged=False, training_cost=2., active_bounds=[]),
        training_epochs=2)
    assert result['status'] == 'numerical_nonpass'
    assert result['training_cost'] == 2.
    assert result['linear_reference'] is None
    assert result['scientific_decision'] == 'abstain'


def test_control_report_uses_full_saved_fit_and_rejects_changed_cost():
    from lll.esa_fit_adjusted_control_report import score_candidate

    fit = _fit()
    summary = dict(converged=True,training_cost=2.,active_bounds=[])
    result = score_candidate(fit, summary, training_epochs=2)
    assert result['status'] == 'interior_complete'
    assert result['linear_reference']['local_rank'] == 1
    summary['training_cost'] = 3.
    with pytest.raises(ValueError,match='cost'):
        score_candidate(fit,summary,training_epochs=2)


def test_control_report_reads_recovered_binary_artifact_by_sealed_hash():
    from types import SimpleNamespace
    from lll.esa_fit_adjusted_control_report import _artifact

    calls = []
    study = SimpleNamespace(
        envelope=lambda identity: dict(artifacts={
            'artifacts/case/measured-inputs.npz':'expected-hash'}),
        read_artifact=lambda identity,name,expected,raw: (
            calls.append((identity,name,expected,raw)) or b'bytes'))
    assert _artifact(study,'case','measured-inputs.npz',raw=True) == b'bytes'
    assert calls == [('case','artifacts/case/measured-inputs.npz',
                      'expected-hash',True)]


def test_observed_reference_checks_training_support_in_each_law():
    from lll.esa_fit_adjusted_control_report import validate_observed_reference

    observed = dict(protected_confirmation_groups_opened=0,
        laws={law:dict(training_epochs=600,quadratic=7.)
              for law in ('increment','point')})
    validate_observed_reference(observed)
    observed['laws']['point']['training_epochs'] = 800
    with pytest.raises(ValueError,match='training reference'):
        validate_observed_reference(observed)
