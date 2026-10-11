# SPDX-License-Identifier: AGPL-3.0-or-later
import json

import pytest


def worker():
    import ilvis0_calibration_trial
    return ilvis0_calibration_trial


def test_exact_twelve_identities_and_one_parameter_ablation():
    trial = worker()
    reference = trial.clock.base.primary_cases()
    cases = trial.cases()
    assert len(cases)==4
    assert len(set(trial.identities()))==12
    for case in cases:
        original = next(c for c in reference if c['case_id']==case['reference_case_id'])
        expected = 'gyro_gain_z' if case['alternative']=='gain_zero' else 'gyro_bias_z'
        assert [k for k in original['limits'] if original['limits'][k]!=case['limits'][k]]==[expected]
        assert case['limits'][expected]==0.
        assert case['profile']==original['profile']
        bounds = trial.clock.base.estimator.Bounds(case['limits'])
        assert expected not in bounds.active
        assert bounds.decode([0.]*len(bounds.active))[expected]==0.


def test_start_journal_does_not_retry_expand_or_change_freeze(tmp_path):
    trial = worker(); p=tmp_path/'starts.jsonl'
    for identity in trial.identities(): trial.charge(p, identity, 'freeze')
    assert len(trial.journal(p, 'freeze'))==12
    with pytest.raises(ValueError): trial.charge(p, trial.identities()[0], 'freeze')
    with pytest.raises(ValueError): trial.charge(p, 'outside', 'freeze')
    with pytest.raises(ValueError): trial.journal(p, 'different')
    rows = [json.loads(line) for line in p.read_text().splitlines()]
    rows[0]['maximum_evaluations']=201
    p.write_text(''.join(json.dumps(r)+'\n' for r in rows))
    with pytest.raises(ValueError): trial.journal(p, 'freeze')


def test_completed_worker_cannot_load_native_kernel(tmp_path, monkeypatch):
    trial=worker(); (tmp_path/'completion.json').write_text('{}')
    monkeypatch.setattr(trial, 'prepare', lambda output: {})
    def forbidden(*args, **kwargs):
        raise AssertionError('completed trial must not load native kernels')
    monkeypatch.setattr(trial.clock.base.explore, 'load_kernel', forbidden)
    with pytest.raises(ValueError, match='completed'): trial.run(tmp_path)


def test_prepare_cli_cannot_fit_or_spawn(monkeypatch):
    trial=worker(); prepared=[]
    monkeypatch.setattr(trial.sys, 'argv', ['trial', '--prepare-only'])
    monkeypatch.setattr(trial, 'prepare', lambda output: prepared.append(output))
    def forbidden(*args, **kwargs): raise AssertionError('prepare must not start workers')
    monkeypatch.setattr(trial, 'run', forbidden)
    monkeypatch.setattr(trial.subprocess, 'Popen', forbidden)
    trial.main()
    assert prepared==[trial.OUTPUT]


def test_manifest_scope_rejects_a_widened_allowance():
    trial=worker()
    scope=trial.scope()
    trial.check_scope(scope)
    for key, value in [('maximum_starts', 13), ('maximum_per_identity', 2),
                       ('maximum_evaluations_per_start', 201)]:
        changed=dict(scope); changed[key]=value
        with pytest.raises(ValueError, match='scope'): trial.check_scope(changed)


def test_profiles_keep_calibration_alternatives_separate():
    trial=worker(); rows=[]
    for case in trial.cases():
        rows.append(dict(case_id=case['case_id'], reference_case_id=case['reference_case_id'],
                         alternative=case['alternative'], fits=[]))
    calls=[]
    def profile(cases):
        calls.append(cases)
        return {'count': len(cases)}
    assert trial.profiles(rows, profile)=={'gain_zero': {'count': 2}, 'offset_zero': {'count': 2}}
    assert all(len({r['alternative'] for r in group})==1 for group in calls)
