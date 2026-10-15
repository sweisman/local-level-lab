# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest
import ilvis0_clock_trial as trial


def test_clock_scope_is_exactly_six_fixed_control_identities():
    identities = trial.identities()
    assert len(identities) == len(set(identities)) == 6
    assert all(identity.startswith(trial.TARGET+'::') for identity in identities)


def test_clock_start_charges_cannot_retry_or_expand(tmp_path):
    path = tmp_path/'starts.jsonl'; identities = trial.identities()
    trial.charge(path, identities[0], 'hash')
    assert len(trial.journal(path, 'hash')) == 1
    with pytest.raises(ValueError, match='charged'):
        trial.charge(path, identities[0], 'hash')
    with pytest.raises(ValueError):
        trial.charge(path, 'outside', 'hash')
    with pytest.raises(ValueError):
        trial.journal(path, 'different')


def test_original_initialization_is_reused_for_both_clock_hypotheses():
    class Problem:
        class Bounds:
            active = ('gyro_bias_z', 'accel_gain_x', 'earth_removal')
        bounds = Bounds()
    point = trial.initial_point(Problem(), 9.81*1.03, {'accel_gain_x': .15})
    assert np.allclose(point, [0., .2, -1.])


def test_completed_clock_worker_cannot_start_fits(tmp_path, monkeypatch):
    (tmp_path/'completion.json').write_text('{}'); (tmp_path/'manifest.json').write_text('{}')
    monkeypatch.setattr(trial, 'prepare', lambda output: {})
    def forbidden(directory):
        raise AssertionError('must not load native kernel for completed work')
    monkeypatch.setattr(trial.base.explore, 'load_kernel', forbidden)
    with pytest.raises(ValueError, match='completed'):
        trial.run(tmp_path)


def test_prepare_cli_does_not_run_or_spawn_workers(monkeypatch):
    prepared = []
    monkeypatch.setattr(trial.sys, 'argv', ['clock', '--prepare-only'])
    monkeypatch.setattr(trial, 'prepare', lambda output: prepared.append(output))
    def forbidden(*args, **kwargs):
        raise AssertionError('prepare must not run or spawn workers')
    monkeypatch.setattr(trial, 'run', forbidden)
    monkeypatch.setattr(trial.subprocess, 'Popen', forbidden)
    trial.main()
    assert prepared == [trial.OUTPUT]
