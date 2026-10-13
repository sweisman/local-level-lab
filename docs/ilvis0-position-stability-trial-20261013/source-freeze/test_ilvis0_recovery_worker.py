# SPDX-License-Identifier: AGPL-3.0-or-later
import json
import numpy as np
import pytest
import ilvis0_recovery_worker as worker


def test_no_authorization_means_no_native_or_original_access(tmp_path, monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail('unauthorized execution reached scientific work')
    monkeypatch.setattr(worker, 'verify', forbidden)
    with pytest.raises(ValueError, match='authorization'):
        worker.run(tmp_path)


def test_completed_trial_cannot_be_restarted(tmp_path):
    (tmp_path / 'completion.json').write_text('{}')
    with pytest.raises(ValueError, match='completed'):
        worker.run(tmp_path)


def test_repeat_starts_are_feasible_and_actually_distinct():
    point = np.array([-1., 0., 1., -.3, .3])
    shifted = worker.repeat_start(point, .01)
    assert np.all(abs(shifted) <= 1)
    assert np.all(shifted != point)
    assert np.max(abs(shifted - point)) <= .01000000001
    assert np.array_equal(point, [-1., 0., 1., -.3, .3])


def test_wrong_finite_authorization_is_rejected(tmp_path):
    (tmp_path / 'manifest.json').write_text('{}')
    (tmp_path / 'authorization.json').write_text(json.dumps(dict(maximum_starts=999)))
    with pytest.raises(ValueError, match='authorization'):
        worker.authorization(tmp_path, dict(maximum_starts=24, maximum_native_sweeps=14448))


def test_invalid_authorization_cannot_reach_original_verification(tmp_path, monkeypatch):
    (tmp_path / 'manifest.json').write_text(json.dumps(dict(proposal=dict(maximum_starts=24, maximum_native_sweeps=14448))))
    (tmp_path / 'authorization.json').write_text('{}')
    monkeypatch.setattr(worker, 'verify', lambda *args, **kwargs: pytest.fail('original access before authorization'))
    with pytest.raises(ValueError, match='authorization'):
        worker.run(tmp_path)


@pytest.mark.parametrize('model', worker.planning.MODELS)
def test_fit_path_charges_real_native_sweeps_and_preserves_epoch_outputs(tmp_path, monkeypatch, model):
    from lll import ilvis0_geographic_controls as geographic
    f = geographic.fixture(model, 'nominal')
    kernels = (worker.base.explore.load_kernel(tmp_path / 'kernel')[0],
               worker.base.shape.load_tangent(tmp_path / 'kernel')[0])
    values = np.zeros((len(f['dt']), 15))
    values[:, 9:12] = f['theta']; values[:, 12:15] = f['dv']
    seed, _ = worker.base.corpus.initialize(f['gps_times'], f['gps'], values, model)
    covariance = np.diag(np.tile(.1 / f['metric'], len(f['gps_times'])) ** 2)
    limits = geographic.LIMITS
    p = worker.base.shape.TangentProblem(f['theta'], f['dv'], f['dt'], f['gps_times'], f['gps'],
        covariance, seed, worker.base.estimator.Bounds(limits), fit_earth_removal=False,
        kernel=kernels[0], tangent_kernel=kernels[1], clock_hypothesis='nominal_200Hz',
        processing_hypothesis='unsubtracted_increment_hypothesis', maximum_interval_s=.0075,
        gravity_mps2=9.81, disc_radius_m=6371000.)
    point = np.zeros(len(p.bounds.active))
    residual, _, _ = p.residual_tangent(point, model)
    cost = float(residual @ residual)
    reference = dict(active_parameters=list(p.bounds.active), normalized_parameters=point.tolist(), residual_sum_squares=cost)
    def one_real_tangent(problem, candidate, *, start, **kwargs):
        r, _, _ = problem.residual_tangent(start, candidate)
        return dict(converged=True, evaluations=1, normalized_parameters=start.tolist(),
                    initial_cost=float(r @ r), residual_sum_squares=float(r @ r))
    monkeypatch.setattr(worker.solver, 'fit_candidate', one_real_tangent)
    book = worker.journal.Ledger(tmp_path, 'software', ['one'], fit_limit=600, diagnostic_limit=2)
    fit = worker.fit_task(tmp_path, dict(identity='one', model=model, case_id='case', role='control'),
        reference, dict(limits=limits, profile=False),
        (values, f['gps_times'], f['gps'], {}, covariance), kernels, book)
    assert 'error' not in fit, fit
    assert fit['fit_native_sweeps'] == 1 and fit['diagnostic_native_sweeps'] == 2
    epochs = worker.base.load(tmp_path / fit['epoch_file'])
    assert epochs['times_s'] == f['gps_times'].tolist()
    assert len(epochs['errors_neu_m']) == len(f['gps_times'])
    assert max(fit['baseline_track_change_rms_neu_m']) == 0
    assert fit['scientific_decision'] == 'abstain'


def test_repeatability_rejects_different_cost_even_with_success_flags(tmp_path):
    task = dict(identity='sid::case::model::repeat', role='repeatability')
    plan = dict(tasks=[task], repeat_cost_relative_tolerance=1e-6, repeat_track_rms_tolerance_m=.01)
    for name in ('one.json.gz', 'two.json.gz'):
        worker.base.observation.gzip_json(tmp_path / name, dict(times_s=[0., 1.], errors_neu_m=[[0., 0., 0.]] * 2))
    fits = {task['identity']: dict(converged=True, residual_sum_squares=2., epoch_file='one.json.gz'),
            'sid::case::model::primary': dict(converged=True, residual_sum_squares=1., epoch_file='two.json.gz')}
    result = worker.qualify(tmp_path, plan, fits)
    assert not result['qualified']
    assert not result['repeatability'][0]['passed']


def test_unfinished_fit_prevents_qualification(tmp_path):
    plan = dict(tasks=[dict(identity='one', role='recovery')])
    result = worker.qualify(tmp_path, plan, {'one': dict(converged=False)})
    assert not result['qualified'] and result['reasons']


def test_recovery_budget_preserves_charged_failures(tmp_path):
    book = worker.journal.Ledger(tmp_path, 'freeze', ['one'], fit_limit=600, diagnostic_limit=2)
    book.start('one')
    def failed():
        raise RuntimeError('native error')
    with pytest.raises(RuntimeError):
        book.call('one', 'fit', 'tangent', failed)
    assert book.count('one', 'fit') == 1
    with pytest.raises(ValueError):
        book.start('one')
    for _ in range(2):
        book.call('one', 'diagnostic', 'value', lambda: None)
    with pytest.raises(worker.base.estimator.EvaluationLimit):
        book.call('one', 'diagnostic', 'value', lambda: pytest.fail('over-budget call'))
