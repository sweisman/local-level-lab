from types import SimpleNamespace

import pytest

from lll import esa_repeat_turn_execution as original


def test_recovery_worker_exposes_only_training_inputs(monkeypatch):
    from lll import esa_repeat_turn_execution_v2 as worker

    recovery = {
        'continuation-parent-manifest', 'continuation-policy', 'continuation-plan',
        'continuation-qualification-request', 'continuation-qualification-report',
    }
    for metadata in (set(), recovery):
        read = []
        manifest = {'scope': original.SCOPE, 'inputs': dict.fromkeys(original.input_keys() | metadata)}
        context = SimpleNamespace(manifest=manifest, input_path=lambda name: read.append(name))

        def evaluate(task, view):
            assert set(view.manifest['inputs']) == original.input_keys()
            view.input_path('recipe')
            with pytest.raises(ValueError, match='training'):
                view.input_path('continuation-policy')
            return task['identity']

        monkeypatch.setattr(original, 'evaluate', evaluate)
        assert worker.evaluate(original.tasks()[0], context) == original.tasks()[0]['identity']
        assert set(context.manifest['inputs']) == original.input_keys() | metadata
        assert read == ['recipe']

    for invalid in ({'continuation-policy'}, recovery | {'later_receiver'}):
        manifest['inputs'] = dict.fromkeys(original.input_keys() | invalid)
        with pytest.raises(ValueError, match='training'):
            worker.evaluate(original.tasks()[0], context)
        assert read == ['recipe']


def test_release_requires_all_terminal_starts_and_never_substitutes_a_forecast():
    from lll.esa_repeat_turn_release import primary_starts

    choices = {t['identity']: {'converged': False} for t in original.tasks()}
    first, second, third, fourth = (t['identity'] for t in original.tasks()[:4])
    choices[first] = {'converged': True, 'cost': 2.}
    choices[second] = {'converged': True, 'cost': 3., 'forecast_sha256': 'a'*64}
    choices[third] = {'converged': True, 'cost': 3., 'forecast_sha256': 'b'*64}
    choices[fourth] = {'converged': True, 'cost': 3., 'forecast_sha256': 'c'*64}
    selected = primary_starts(choices)
    assert [(row['identity'], row['state']) for row in selected[:3]] == [
        (first, 'primary_forecast_missing'), (third, 'sealed'), (None, 'no_converged_start'),
    ]
    del choices[fourth]
    with pytest.raises(ValueError, match='all 16'):
        primary_starts(choices)


def test_scoring_opens_positions_only_after_replaying_the_saved_release(monkeypatch, tmp_path):
    from lll import esa_repeat_turn_release as gate, esa_repeat_turn_scoring as scoring
    from lll.studies.artifacts import encoded

    identity = original.tasks()[0]['identity']
    release = {'receiver_metadata': {'receipt': 'b'*64},
               'primary': [{'identity': identity, 'first_index': original.WINDOWS[0],
                            'state': 'sealed', 'forecast_sha256': 'a'*64}]}
    events = []

    def replay(*args, **kwargs):
        events.append('release')
        return release, {identity: b'forecast'}, {original.WINDOWS[0]: 'preflight'}

    def positions(root, windows, *, expected_metadata):
        assert windows == {original.WINDOWS[0]: 'preflight'}
        assert expected_metadata == {'receipt': 'b'*64}
        events.append('positions')
        return {original.WINDOWS[0]: ([1.], [[1., 2., 3.]])}

    def score(raw, **kwargs):
        assert raw == b'forecast'
        events.append('score')
        return kwargs

    monkeypatch.setattr(gate, 'release', replay)
    monkeypatch.setattr(gate, 'receiver_positions', positions)
    monkeypatch.setattr(scoring, 'score_sealed', score)
    with pytest.raises(ValueError, match='exact saved release'):
        gate.score(tmp_path, expected_manifest_sha256='c'*64, saved_release=b'changed')
    assert events == ['release']
    result = gate.score(tmp_path, expected_manifest_sha256='c'*64, saved_release=encoded(release))
    assert events == ['release', 'release', 'positions', 'score']
    assert result['scores'][identity]['expected_sha256'] == 'a'*64


def test_terminal_start_audit_keeps_converged_fit_if_forecast_failed():
    from lll.esa_repeat_turn_release import terminal_starts

    identity = original.tasks()[0]['identity']
    fit = {'converged': True, 'residual_sum_squares': 0.5}
    completed = SimpleNamespace(rows={identity: {}}, prefix='recovery',
        envelope=lambda _: {'status': 'complete', 'result': {'passed': False}, 'result_sha256': 'a'*64,
                            'artifacts': {f'artifacts/{identity}/fit.json': 'b'*64}},
        artifact=lambda *args: fit)
    interrupted = SimpleNamespace(rows={identity: {}}, envelope=lambda _: {'status': 'interrupted'})
    outcomes, owners = terminal_starts([interrupted, completed])
    assert owners == {identity: completed}
    assert outcomes[identity]['cost'] == 0.5
    assert not outcomes[identity]['passed']
    with pytest.raises(ValueError, match='one terminal'):
        terminal_starts([completed, completed])
