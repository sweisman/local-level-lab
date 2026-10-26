from types import SimpleNamespace
import pytest

from lll.prediction_phase_review import identities, read_selected


def test_selection_excludes_other_models_laws_and_unexecuted_records():
    tasks = {}
    for seed in (9, 10, 11):
        for law in ('point', 'increment'):
            for model in ('sphere_rotating', 'sphere_still', 'flat_still'):
                for profile in (0, 1):
                    for start in (0, 1):
                        name = f'{seed}-{law}-{model}-{profile}-{start}'
                        tasks[name] = {'payload': dict(draw_seed=seed, case=dict(law=law, model=model, profile=profile, start=start))}
    study = SimpleNamespace(tasks=tasks, rows={k: {} for k in tasks})
    selected = identities(study, 10)
    assert len(selected) == 9
    assert all(k.startswith(('9-increment-', '10-increment-')) for k in selected)
    study.rows.pop(selected[0])
    assert identities(study, 10) == selected[1:]


@pytest.mark.parametrize('selected', [[], ['a', 'a'], list(map(str, range(25)))])
def test_invalid_selection_rejected_before_reading(selected):
    with pytest.raises(ValueError):
        read_selected(None, selected)


def test_preserves_failed_fit_and_interrupted_outcome_without_evaluation():
    failed = dict(converged=False, residual_sum_squares=2.0)
    study = SimpleNamespace(tasks={'a': {'payload': {}}, 'b': {'payload': {}}},
        completion={'manifest_sha256': 'm', 'summary_sha256': 's'},
        envelope=lambda k: {'artifacts': {'artifacts/a/fit.json': 'h'} if k == 'a' else {},
                            'result': {'error_type': 'BudgetStopped'} if k == 'b' else {'converged': False}},
        artifact=lambda k, n: failed)
    report = read_selected(study, ['a', 'b'])
    assert report['records'][0]['fit'] == failed
    assert report['records'][1]['fit'] is None
    assert report['native_calls'] == report['optimizer_starts'] == report['new_noise_draws'] == 0


def test_wall_allowance_cannot_expand():
    with pytest.raises(ValueError):
        read_selected(None, ['a'], maximum_wall_s=601)


def test_publication_passes_frozen_relative_string_to_packager(tmp_path, monkeypatch):
    from lll.prediction_phase_review import publish_phase
    from lll import prediction_calibration_report, prediction_calibration_study
    from lll import airquantumgrav_inventory, ilvis0_control_publication
    from lll.studies import qualification
    monkeypatch.setattr(qualification, 'checked', lambda *a, **k: (b'request', b'tests'))
    monkeypatch.setattr(prediction_calibration_study, 'qualification_sources', lambda r: {})
    monkeypatch.setattr(airquantumgrav_inventory, 'environment', lambda: {})
    monkeypatch.setattr(prediction_calibration_report, 'inspect', lambda *a: dict(role='calibration', calibration=None))
    monkeypatch.setattr(prediction_calibration_report, 'render', lambda r: 'Stopped calibration')
    class CheckedPlan(Exception):
        pass
    def package(data, public, text, *, plan):
        assert type(plan) is str
        assert plan == 'docs/prediction-score-qualification/EXECUTION_PLAN.md'
        raise CheckedPlan
    monkeypatch.setattr(ilvis0_control_publication, 'publish', package)
    with pytest.raises(CheckedPlan):
        publish_phase(tmp_path, 'data/closed', qualification='request.json')
