"""The study recovery entry point never duplicates owned or sealed work."""

from pathlib import Path


def test_owned_original_does_not_start_a_second_worker(monkeypatch, tmp_path):
    from lll import bounded_independent_recovery as recovery

    monkeypatch.setattr(recovery, 'inspect', lambda *_: {'state': 'owned'})
    monkeypatch.setattr(recovery, 'close_original', lambda *_a, **_k: 1 / 0)
    assert recovery.resume(tmp_path) == {'state': 'owned', 'action': 'none'}


def test_complete_original_needs_no_continuation(monkeypatch, tmp_path):
    from lll import bounded_independent_recovery as recovery

    monkeypatch.setattr(recovery, 'inspect', lambda *_: {
        'state': 'closed', 'completed': 48})
    monkeypatch.setattr(recovery, 'prepare_campaign', lambda *_a, **_k: 1 / 0)
    assert recovery.resume(tmp_path) == {
        'state': 'original_complete', 'completed': 48, 'action': 'report'}


def test_interrupted_original_prepares_and_resumes_only_pending(monkeypatch, tmp_path):
    from lll import bounded_independent_recovery as recovery

    calls = []
    states = iter(({'state': 'deadline_exhausted'},
                   {'state': 'closed', 'completed': 17}))
    monkeypatch.setattr(recovery, 'inspect', lambda *_: next(states))
    monkeypatch.setattr(recovery, 'close_original',
                        lambda *a, **k: calls.append(('close', a, k)))
    monkeypatch.setattr(recovery, 'prepare_campaign',
                        lambda *a, **k: calls.append(('prepare', a, k)))
    monkeypatch.setattr(recovery, 'resume_campaign',
                        lambda *a, **k: {'state': 'all_tasks_finished'})
    result = recovery.resume(tmp_path)
    assert result == {'state': 'all_tasks_finished'}
    assert [call[0] for call in calls] == ['close', 'prepare']
    assert calls[1][2]['max_attempts_per_task'] == 3
    assert calls[1][2]['max_technical_interruptions'] == 24
    assert calls[1][2]['maximum_wall_s'] == 18000
    assert calls[1][2]['minimum_free_bytes'] == 5 * 1024**3


def test_existing_continuation_is_reused(monkeypatch, tmp_path):
    from lll import bounded_independent_recovery as recovery

    (Path(tmp_path) / recovery.CONTINUATION).mkdir(parents=True)
    monkeypatch.setattr(recovery, 'inspect', lambda *_: {
        'state': 'closed', 'completed': 17})
    monkeypatch.setattr(recovery, 'prepare_campaign', lambda *_a, **_k: 1 / 0)
    monkeypatch.setattr(recovery, 'resume_campaign',
                        lambda *a, **k: {'state': 'owned'})
    assert recovery.resume(tmp_path) == {'state': 'owned'}
