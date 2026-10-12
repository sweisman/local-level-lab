# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest


def worker():
    import ilvis0_z_profile_worker
    return ilvis0_z_profile_worker


def test_scope_is_exact_equal_27_point_matrix():
    w = worker()
    assert len(w.identities()) == len(set(w.identities())) == 27
    assert w.scope()['maximum_native_sweeps'] == 5400
    assert w.scope()['retry_reserve'] == 0
    assert w.scope()['initialization'] == 'zero_free_coordinates_then_frozen_stages'
    assert w.scope()['cases'][0]['profile'] is False
    assert {w.coordinate(i) for i in w.identities()} == {(a, b) for a in (-2, 0, 2) for b in (-1, 0, 1)}


def test_journal_retains_charges_and_disallows_retries_or_new_freeze(tmp_path):
    w = worker(); path = tmp_path/'starts.jsonl'
    for identity in w.identities(): w.charge(path, identity, 'freeze')
    old = path.read_bytes()
    with pytest.raises(ValueError): w.charge(path, w.identities()[0], 'freeze')
    with pytest.raises(ValueError): w.journal(path, 'changed')
    assert len(w.journal(path, 'freeze')) == 27
    assert path.read_bytes() == old


def test_interrupted_identity_is_a_failure_not_a_retry(tmp_path):
    w = worker(); identity = w.identities()[0]
    w.charge(tmp_path/'starts.jsonl', identity, 'freeze')
    result = w.checked_cache(tmp_path, identity, 'freeze')
    assert result['evaluations'] is None and not result['converged']
    assert 'no retry' in result['error']
    assert w.checked_cache(tmp_path, identity, 'freeze') == result


def test_completed_worker_does_not_load_measurements_or_prepare(tmp_path, monkeypatch):
    w = worker(); (tmp_path/'completion.json').write_text('{}')
    def forbidden(*args, **kwargs): raise AssertionError('completed worker cannot start')
    monkeypatch.setattr(w, 'prepare', forbidden)
    with pytest.raises(ValueError, match='completed'): w.run(tmp_path)


@pytest.mark.parametrize('action', ['prepare-only', 'package-only'])
def test_nonrun_cli_never_runs_or_spawns(action, tmp_path, monkeypatch):
    w = worker(); calls = []
    monkeypatch.setattr(w, 'OUTPUT', tmp_path)
    monkeypatch.setattr(w.sys, 'argv', ['worker', '--'+action])
    monkeypatch.setattr(w, 'prepare', lambda *a: calls.append('prepare'))
    monkeypatch.setattr(w, 'publish', lambda *a: calls.append('publish'))
    def forbidden(*args, **kwargs): raise AssertionError('no fits or spawn')
    monkeypatch.setattr(w, 'run', forbidden)
    monkeypatch.setattr(w.subprocess, 'Popen', forbidden)
    w.main()
    assert calls == ['prepare' if action == 'prepare-only' else 'publish']


def test_busy_lock_rejects_launch_before_preparation(tmp_path, monkeypatch):
    w = worker(); monkeypatch.setattr(w, 'OUTPUT', tmp_path)
    monkeypatch.setattr(w.sys, 'argv', ['worker', '--detach'])
    def forbidden(*args, **kwargs): raise AssertionError('busy worker must stop')
    monkeypatch.setattr(w, 'prepare', forbidden)
    with (tmp_path/'worker.lock').open('a') as lock:
        w.fcntl.flock(lock, w.fcntl.LOCK_EX|w.fcntl.LOCK_NB)
        with pytest.raises(BlockingIOError): w.main()


def test_explicit_action_required(monkeypatch):
    w = worker(); monkeypatch.setattr(w.sys, 'argv', ['worker'])
    with pytest.raises(SystemExit): w.main()


def test_uncharged_result_and_corrupt_residual_are_rejected(tmp_path):
    w = worker(); identity = w.identities()[0]
    path = w.result_path(tmp_path, identity)
    w.base.save(path, {'converged': True}, 'freeze')
    with pytest.raises(ValueError, match='uncharged'): w.checked_cache(tmp_path, identity, 'freeze')
    w.charge(tmp_path/'starts.jsonl', identity, 'freeze')
    residual = tmp_path/'residual.csv.gz'; residual.write_bytes(b'original')
    w.base.save(path, dict(residual_file=residual.name, residual_sha256=w.base.il.sha256(residual)), 'freeze')
    residual.write_bytes(b'corrupt')
    with pytest.raises(ValueError): w.checked_cache(tmp_path, identity, 'freeze')


@pytest.mark.parametrize('model', ['sphere_rotating', 'sphere_still', 'flat_still'])
def test_native_profile_reoptimizes_other_coordinates_and_counts_diagnostics(tmp_path, monkeypatch, model):
    w = worker()
    from lll import ilvis0_geographic_controls as control
    f = control.fixture(model, 'nominal')
    # Construct a zero-Z-calibration control from the independent physical generator.
    theta = f['theta'].copy()
    theta[:,2] = (theta[:,2]-f['truth']['gyro_bias_z']*f['dt'])/(1+f['truth']['gyro_gain_z'])
    values = np.zeros((len(f['dt']), 15))
    values[:,2] = f['dt']; values[:,9:12] = theta; values[:,12:15] = f['dv']
    covariance = np.diag(np.tile(.01/f['metric'], len(f['gps_times']))**2)
    case = dict(w.scope()['cases'][0], limits=control.LIMITS)
    monkeypatch.setattr(w, 'scope', lambda: {'cases': [case]})
    monkeypatch.setattr(w.base.corpus, 'initialize', lambda *args: (f['initial'], 9.81))
    kernel = w.base.explore.load_kernel(tmp_path/'kernel')[0]
    tangent = w.base.shape.load_tangent(tmp_path/'kernel')[0]
    identity = next(i for i in w.identities() if i.split('::')[2]==model and w.coordinate(i)==(0,0))
    result = w.fit_one(tmp_path,identity,values,f['gps_times'],f['gps'],
        {'first_interval_start_utc_s': 0.}, {'h1_v3_tau60': covariance}, 1/f['metric'],kernel,tangent)
    assert result['converged'], result
    assert result['parameters']['gyro_gain_z'] == result['parameters']['gyro_bias_z'] == 0
    assert set(result['active_parameters']) == set(control.LIMITS)-{'gyro_gain_z', 'gyro_bias_z'}
    assert max(result['residual_rms_neu_m']) < .002
    assert result['diagnostic_predictions'] == 2
    assert result['evaluations'] == result['actual_tangent_sweeps']+2 <= 200
    assert result['saved_stationarity'] == pytest.approx(result['exact_projected_gradient_relative'])
    assert (tmp_path/result['residual_file']).is_file()


def test_publication_requires_cached_results_and_never_fits(tmp_path, monkeypatch):
    w = worker(); guide = tmp_path/'public'; monkeypatch.setattr(w, 'GUIDE', guide)
    monkeypatch.setattr(w, 'verify', lambda output: {'sources': {}})
    def forbidden(*args, **kwargs): raise AssertionError('publication must not load or fit measurements')
    monkeypatch.setattr(w.base.segments, 'extract_segment', forbidden)
    monkeypatch.setattr(w.base.shape, 'fit_shape_candidate', forbidden)
    monkeypatch.setattr(w.base.shape, 'load_tangent', forbidden)
    w.base.follow.atomic_json(tmp_path/'manifest.json',{})
    digest = w.base.il.sha256(tmp_path/'manifest.json'); fits = []
    for identity in w.identities():
        w.charge(tmp_path/'starts.jsonl',identity,digest)
        fit = dict(identity=identity,model=identity.split('::')[2],converged=False,
            residual_sum_squares=10.,evaluations=3,active_bounds=[])
        w.base.save(w.result_path(tmp_path,identity),fit,digest); fits.append(fit)
    w.base.follow.atomic_json(tmp_path/'summary.json',dict(fits=fits,
        profile={'conditional_shape_preference':'unresolved'}))
    w.base.follow.atomic_json(tmp_path/'completion.json',dict(state='complete',starts=27,
        manifest_sha256=digest,summary_sha256=w.base.il.sha256(tmp_path/'summary.json')))
    (tmp_path/'selection.json.gz').write_bytes(b'selection'); (tmp_path/'source-freeze').mkdir()
    w.publish(tmp_path)
    w.infrastructure.clock.audit.verify_artifacts(guide,w.base.load(guide/'evidence-receipt.json'))
    assert len((guide/'profiles.csv').read_text().splitlines()) == 28
    assert (guide/'profile-grid.svg').is_file()
    assert (guide/'profile-increases.svg').is_file()
    assert 'unresolved' in (guide/'profile-grid.svg').read_text()


def test_grid_does_not_treat_unfinished_low_cost_as_a_completed_minimum():
    w = worker()
    rows = []
    for identity in w.identities():
        gain,bias = w.coordinate(identity)
        rows.append(dict(model=identity.split('::')[2],gain_percent=gain,bias_dph=bias,
                         status='converged',cost=100.))
    rows[0].update(status='unresolved',cost=0.)
    figure = w.grid_svg(rows, increases=True)
    assert 'unresolved' in figure
    assert '100 / unresolved' in figure or '0 / unresolved' in figure
    assert 'completed grid minimum' in figure
