# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
from pathlib import Path

import pytest


def worker():
    path = Path(__file__).with_name('ilvis0_position_recovery_worker.py')
    assert path.exists(), 'full recovery launcher missing'
    spec = importlib.util.spec_from_file_location('full_position_recovery_test', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_only_new_identities_spend_the_159_start_allowance():
    current = worker()
    plan = current.base.load(current.PREPARATION/'plan.json')
    qualified = dict(qualification=dict(qualified=True, reasons=[]),
                     results={t['identity']: dict(converged=True) for t in plan['tasks']
                              if t['action'] != 'new_start'})
    proposal = current.execution_plan(plan, qualified)
    assert len(proposal['identities']) == proposal['maximum_starts'] == 159
    assert len(proposal['reused_identities']) == 18
    assert not set(proposal['identities']) & set(proposal['reused_identities'])
    assert proposal['maximum_native_sweeps'] == 95718
    assert [t['role'] for t in proposal['tasks'][:6]] == ['control']*6
    assert set(proposal['identities']) == {t['identity'] for t in proposal['tasks']}


@pytest.mark.parametrize('qualified', [False, None])
def test_partial_qualification_cannot_authorize_full_recovery(qualified):
    current = worker()
    with pytest.raises(ValueError, match='qualified'):
        current.execution_plan(current.base.load(current.PREPARATION/'plan.json'),
                               dict(qualification=dict(qualified=qualified)))


def test_saved_start_source_is_fixed_and_copied():
    current = worker()
    task = dict(identity='one::case::model::repeat', segment_id='one', case_id='case',
                model='model', role='repeatability')
    fit = dict(active_parameters=['x'], normalized_parameters=[.3], residual_sum_squares=5.)
    originals = {'one': dict(cases=[dict(case_id='case', fits=[dict(fit, model='model')])])}
    trial = dict(results={'one::case::model::primary': dict(fit, normalized_parameters=[.9])})
    reference = current.reference_for(task, originals, trial)
    assert reference['normalized_parameters'] == [.3]
    reference['normalized_parameters'][0] = .1
    assert originals['one']['cases'][0]['fits'][0]['normalized_parameters'] == [.3]
    assert current.reference_for(dict(task, role='control', identity='one::case::model::primary'), originals, trial)['normalized_parameters'] == [.9]


def comparisons_fixture(current):
    cases = [dict(case_id=c, fits=[dict(model=m, converged=True, exact_projected_gradient_relative=0., residual_sum_squares=i+1.)
             for i, m in enumerate(('sphere_rotating', 'sphere_still', 'flat_still'))])
             for c in ('bias1_unsubtracted', 'bias1_profiled_removal')]
    return {'one': dict(segment_id='one', cases=cases, provenance={})}


def test_failed_repeat_withholds_shape_and_rotation_even_when_all_primaries_pass():
    current = worker()
    originals = comparisons_fixture(current)
    plan = dict(recovery_segment_ids=['one'])
    qualification = dict(controls_passed=True, repeatability=[dict(identity='one::case::model::repeat', passed=False)])
    row = current.comparisons(plan, originals, {}, qualification)[0]
    assert row['raw_profile']['conditional_shape_preference'] == 'globe'
    assert row['profile']['conditional_shape_preference'] == 'unresolved'
    assert row['profile']['rotation_diagnostics'] is None
    assert not row['recovery_checks_passed']


def test_control_failure_withholds_every_new_result():
    current = worker()
    q = dict(controls_passed=False, repeatability=[dict(identity='one::case::model::repeat', passed=True)])
    row = current.comparisons(dict(recovery_segment_ids=['one']), comparisons_fixture(current), {}, q)[0]
    assert row['profile']['conditional_shape_preference'] == 'unresolved'


def test_passing_repeat_permits_full_shape_first_comparison():
    current = worker()
    q = dict(controls_passed=True, repeatability=[dict(identity='one::case::model::repeat', passed=True)])
    row = current.comparisons(dict(recovery_segment_ids=['one']), comparisons_fixture(current), {}, q)[0]
    assert row['profile']['conditional_shape_preference'] == 'globe'
    assert len(row['profile']['rotation_diagnostics']) == 2


def test_completed_run_cannot_restart(tmp_path):
    current = worker()
    (tmp_path/'completion.json').write_text('{}')
    with pytest.raises(ValueError, match='completed'):
        current.run(tmp_path)


def test_interrupted_identity_stays_failed_and_charged(tmp_path):
    current = worker()
    book = current.core.journal.Ledger(tmp_path, 'freeze', ['one'], fit_limit=600, diagnostic_limit=2)
    book.start('one')
    task = dict(identity='one', model='flat_still', role='recovery', case_id='case')
    fit = current.interrupted_fit(task, book)
    assert fit['converged'] is False
    assert fit['fit_native_sweeps'] == 0
    assert 'no retry' in fit['error']
    with pytest.raises(ValueError, match='no retry'):
        book.start('one')


def test_loading_full_worker_does_not_change_completed_trial():
    import ilvis0_position_stability_worker as completed
    before = completed.VERSION, completed.core.VERSION, completed.GUIDE, completed.core.OUTPUT
    current = worker()
    assert current.core.VERSION != completed.core.VERSION
    assert before == (completed.VERSION, completed.core.VERSION, completed.GUIDE, completed.core.OUTPUT)


def test_new_recovery_fit_uses_qualified_native_path(tmp_path, monkeypatch):
    from lll import ilvis0_geographic_controls as geographic
    import numpy as np
    current = worker()
    fixture = geographic.fixture('sphere_rotating', 'nominal')
    kernels = (current.base.explore.load_kernel(tmp_path/'kernel')[0],
               current.base.shape.load_tangent(tmp_path/'kernel')[0])
    values = np.zeros((len(fixture['dt']), 15))
    values[:, 9:12], values[:, 12:15] = fixture['theta'], fixture['dv']
    covariance = np.diag(np.tile(.1/fixture['metric'], len(fixture['gps_times']))**2)
    monkeypatch.setattr(current.base.corpus, 'initialize', lambda *args: (fixture['initial'], 9.81))
    problem = current.base.shape.TangentProblem(fixture['theta'], fixture['dv'], fixture['dt'],
        fixture['gps_times'], fixture['gps'], covariance, fixture['initial'],
        current.base.estimator.Bounds(geographic.LIMITS), fit_earth_removal=False,
        kernel=kernels[0], tangent_kernel=kernels[1], clock_hypothesis='nominal_200Hz',
        processing_hypothesis='unsubtracted_increment_hypothesis', maximum_interval_s=.0075,
        gravity_mps2=9.81, disc_radius_m=6371000.)
    point = np.zeros(len(problem.bounds.active))
    residual, _, _ = problem.residual_tangent(point, 'sphere_rotating')
    reference = dict(active_parameters=list(problem.bounds.active), normalized_parameters=point.tolist(),
                     residual_sum_squares=float(residual@residual))
    book = current.core.journal.Ledger(tmp_path, 'software', ['one'], fit_limit=600, diagnostic_limit=2)
    fit = current.prior.fit_task_from_reference(tmp_path, dict(identity='one', model='sphere_rotating',
        case_id='case', role='recovery'), reference, dict(limits=geographic.LIMITS, profile=False),
        (values, fixture['gps_times'], fixture['gps'], {}, covariance), kernels, book)
    assert 'error' not in fit
    assert fit['converged'] and fit['stability_verified']
    assert fit['fit_native_sweeps'] == fit['evaluations'] <= 600
    assert fit['diagnostic_native_sweeps'] == 2
    assert not fit['scientific_eligible']


def test_uncharged_cache_cannot_be_reused(tmp_path):
    current = worker()
    book = current.core.journal.Ledger(tmp_path, 'freeze', ['one'], fit_limit=600, diagnostic_limit=2)
    current.base.save(tmp_path/'one.json', dict(converged=True), 'freeze')
    with pytest.raises(ValueError, match='without charged'):
        current.saved_fit(tmp_path, 'one', 'freeze', book)


def test_cached_epoch_corruption_is_rejected(tmp_path):
    current = worker()
    book = current.core.journal.Ledger(tmp_path, 'freeze', ['one'], fit_limit=600, diagnostic_limit=2)
    book.start('one')
    (tmp_path/'epoch.json').write_text('{}')
    fit = dict(converged=False, epoch_file='epoch.json', epoch_sha256=current.base.il.sha256(tmp_path/'epoch.json'))
    current.base.save(tmp_path/'one.json', fit, 'freeze')
    (tmp_path/'epoch.json').write_text('changed')
    with pytest.raises(ValueError):
        current.saved_fit(tmp_path, 'one', 'freeze', book)


def test_publication_verifies_159_new_charges_and_18_reused_results_without_fits(tmp_path, monkeypatch):
    current = worker()
    planned = current.base.load(current.PREPARATION/'plan.json')
    qualified = dict(qualification=dict(qualified=True), results={t['identity']: dict(converged=True)
        for t in planned['tasks'] if t['action'] != 'new_start'})
    proposal = current.execution_plan(planned, qualified)
    manifest = dict(proposal=proposal)
    current.base.follow.atomic_json(tmp_path/'manifest.json', manifest)
    digest = current.base.il.sha256(tmp_path/'manifest.json')
    book = current.core.journal.Ledger(tmp_path, digest, proposal['identities'], fit_limit=600, diagnostic_limit=2)
    for identity in proposal['identities']:
        book.start(identity)
    (tmp_path/'sweeps.jsonl').write_text('')
    results = {t['identity']: dict(converged=False, fit_native_sweeps=0, diagnostic_native_sweeps=0,
        result_origin='qualified_subset' if t['action'] != 'new_start' else 'new_recovery')
        for t in planned['tasks']}
    summary = dict(results=results, starts=159, native_sweeps=0, combined_tally=dict(unresolved=41), comparisons=[])
    current.base.follow.atomic_json(tmp_path/'summary.json', summary)
    current.base.follow.atomic_json(tmp_path/'completion.json', dict(manifest_sha256=digest,
        summary_sha256=current.base.il.sha256(tmp_path/'summary.json'), starts=159, native_sweeps=0,
        journal_hashes={n: current.base.il.sha256(tmp_path/n) for n in ('starts.jsonl', 'sweeps.jsonl')}))
    for name in ('proposal.json', 'selection.json.gz', 'reused-results.json.gz', 'authorization.json'):
        (tmp_path/name).write_text('{}')
    (tmp_path/'source-freeze').mkdir()
    monkeypatch.setattr(current, 'verify', lambda output: manifest)
    monkeypatch.setattr(current, 'GUIDE', tmp_path/'publication')
    current.publish(tmp_path)
    assert (current.GUIDE/'RESULTS.md').exists()
    assert len((current.GUIDE/'fits.csv').read_text().splitlines()) == 178
    assert len(book.read('starts')) == 159
    (tmp_path/'starts.jsonl').write_text('corrupt')
    with pytest.raises(ValueError):
        current.publish(tmp_path)
