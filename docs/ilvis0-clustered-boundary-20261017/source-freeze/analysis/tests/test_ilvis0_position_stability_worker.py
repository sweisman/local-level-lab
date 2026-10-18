# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest


def worker():
    path = Path(__file__).with_name('ilvis0_position_stability_worker.py')
    assert path.exists(), 'separate position-stability worker missing'
    spec = importlib.util.spec_from_file_location('position_worker_test', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_frozen_worker_globals_unchanged():
    import ilvis0_boundary_worker as previous
    before = previous.VERSION, previous.GUIDE, previous.OUTPUT, previous.core.solver.VERSION
    current = worker()
    assert current.core.solver.VERSION == 'ilvis0-actual-position-stability-v1'
    assert current.GUIDE != previous.GUIDE and current.OUTPUT != previous.OUTPUT
    assert before == (previous.VERSION, previous.GUIDE, previous.OUTPUT, previous.core.solver.VERSION)


def test_latest_primary_endpoints_are_used_for_both_starts_without_cherry_picking():
    current = worker()
    task = dict(identity='one::case::model::repeat', role='repeatability')
    endpoint = dict(active_parameters=['x'], normalized_parameters=[.4], residual_sum_squares=3.)
    summary = dict(results={'one::case::model::primary': endpoint})
    source = current.endpoint_reference(task, summary)
    assert source == endpoint
    assert source is not endpoint
    source['normalized_parameters'][0] = -.1
    assert endpoint['normalized_parameters'] == [.4]


def test_completed_study_cannot_restart(tmp_path):
    current = worker()
    (tmp_path/'completion.json').write_text('{}')
    with pytest.raises(ValueError, match='completed'):
        current.core.run(tmp_path)


def endpoint_dependency(tmp_path, current):
    source = tmp_path/'source.py'
    source.write_text('unchanged')
    (tmp_path/'source-freeze').mkdir()
    (tmp_path/'source-freeze/source.py').write_bytes(source.read_bytes())
    manifest = dict(sources={str(source): current.core.base.il.sha256(source)}, artifacts={},
                    environment=current.core.base.runtime.numerical_environment(),
                    proposal=dict(identities=['one'], maximum_starts=1,
                                  maximum_fit_sweeps=600, maximum_diagnostic_sweeps=2))
    current.core.base.follow.atomic_json(tmp_path/'manifest.json', manifest)
    digest = current.core.base.il.sha256(tmp_path/'manifest.json')
    (tmp_path/'starts.jsonl').write_text(json.dumps(dict(number=1, identity='one', manifest_sha256=digest))+'\n')
    # Fixture data only: demonstrate the old 200-call dependency checker is
    # inappropriate for a completed study whose frozen per-fit limit is 600.
    rows = [dict(number=i+1, identity='one', manifest_sha256=digest,
                 phase='fit', kind='tangent') for i in range(251)]
    (tmp_path/'sweeps.jsonl').write_text(''.join(json.dumps(row)+'\n' for row in rows))
    summary = dict(state='complete', starts=1, native_sweeps=251,
                   results={'one': dict(fit_native_sweeps=251, diagnostic_native_sweeps=0)})
    current.core.base.follow.atomic_json(tmp_path/'summary.json', summary)
    current.core.base.follow.atomic_json(tmp_path/'completion.json', dict(
        state='complete', manifest_sha256=digest, summary_sha256=current.core.base.il.sha256(tmp_path/'summary.json'),
        starts=1, native_sweeps=251, journal_hashes={name: current.core.base.il.sha256(tmp_path/name)
                                                   for name in ('starts.jsonl', 'sweeps.jsonl')}))
    return manifest


def test_completed_endpoint_check_uses_its_own_frozen_600_call_allowance(tmp_path):
    current = worker()
    manifest = endpoint_dependency(tmp_path, current)
    assert current.completed_endpoints(tmp_path)[0] == manifest


@pytest.mark.parametrize('name', ['source.py', 'source-freeze/source.py', 'sweeps.jsonl'])
def test_completed_endpoint_source_and_journal_corruption_rejected(tmp_path, name):
    current = worker()
    endpoint_dependency(tmp_path, current)
    (tmp_path/name).write_text('changed')
    with pytest.raises(ValueError):
        current.completed_endpoints(tmp_path)


@pytest.mark.parametrize('model', ['sphere_rotating', 'sphere_still', 'flat_still'])
def test_native_position_check_and_ledger_agree_on_independent_motion(tmp_path, monkeypatch, model):
    from lll import ilvis0_geographic_controls as geographic
    current = worker()
    fixture = geographic.fixture(model, 'nominal')
    kernels = (current.core.base.explore.load_kernel(tmp_path/'kernel')[0],
               current.core.base.shape.load_tangent(tmp_path/'kernel')[0])
    values = np.zeros((len(fixture['dt']), 15))
    values[:, 9:12], values[:, 12:15] = fixture['theta'], fixture['dv']
    covariance = np.diag(np.tile(.1/fixture['metric'], len(fixture['gps_times']))**2)
    monkeypatch.setattr(current.core.base.corpus, 'initialize', lambda *args: (fixture['initial'], 9.81))
    problem = current.core.base.shape.TangentProblem(
        fixture['theta'], fixture['dv'], fixture['dt'], fixture['gps_times'], fixture['gps'],
        covariance, fixture['initial'], current.core.base.estimator.Bounds(geographic.LIMITS),
        fit_earth_removal=False, kernel=kernels[0], tangent_kernel=kernels[1],
        clock_hypothesis='nominal_200Hz', processing_hypothesis='unsubtracted_increment_hypothesis',
        maximum_interval_s=.0075, gravity_mps2=9.81, disc_radius_m=6371000.)
    point = np.zeros(len(problem.bounds.active))
    residual, _, _ = problem.residual_tangent(point, model)
    reference = dict(active_parameters=list(problem.bounds.active), normalized_parameters=point.tolist(),
                     residual_sum_squares=float(residual@residual))
    # Short independent coordinates verify unwhitening against direct positions.
    offset = point.copy()
    offset[0] = .001
    r2, _, _ = problem.residual_tangent(offset, model)
    from lll import ilvis0_solver_position as solver
    direct = (problem.predict(offset, model)-problem.predict(point, model))*solver.physical_metric(fixture['gps'])
    np.testing.assert_allclose(solver.physical_residual_step(problem, r2-residual), direct, atol=1e-8, rtol=1e-6)
    book = current.core.journal.Ledger(tmp_path, 'software', ['one'], fit_limit=600, diagnostic_limit=2)
    fit = current.fit_task_from_reference(tmp_path, dict(identity='one', model=model, case_id='case', role='control'),
        reference, dict(limits=geographic.LIMITS, profile=False),
        (values, fixture['gps_times'], fixture['gps'], {}, covariance), kernels, book)
    assert 'error' not in fit, fit
    assert fit['converged'] and fit['stability_verified']
    assert fit['fit_native_sweeps'] == fit['evaluations'] <= 600
    assert fit['diagnostic_native_sweeps'] == 2
    assert max(fit['track_rms_neu_m']) < 1e-4
    assert not fit['scientific_eligible']
    assert 'linearization_file' in fit
