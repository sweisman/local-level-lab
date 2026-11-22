"""The observed continuation resume command must preserve sealed outcomes."""

import pytest

from lll.prediction_observed_continuation_resume import resume
from lll.prediction_observed_continuation_study import IDENTITY, task


def test_resume_rejects_missing_frozen_study_without_start(tmp_path):
    with pytest.raises(ValueError, match='prepared frozen'):
        resume(tmp_path)


def test_resume_of_sealed_result_is_idempotent(tmp_path, monkeypatch):
    import lll.studies.closed as closed_module

    study = tmp_path/'data'/IDENTITY
    study.mkdir(parents=True)
    (study/'completion.json').write_text('{}')
    opened = []

    class Sealed:
        def __init__(self, root, prefix):
            opened.append(prefix)
            self.manifest = dict(tasks=[dict(identity=task(smoke=False)['identity'])])
            self.completion = dict(state='complete')
            self.summary = dict(completed=1, passed=True)

        def close(self):
            opened.append('closed')

    monkeypatch.setattr(closed_module, 'ClosedStudy', Sealed)
    result = resume(tmp_path)
    assert result == dict(state='complete', completed=1,
                          passed=True, new_starts=0)
    assert opened == ['data/'+IDENTITY, 'closed']


def test_resume_of_sealed_interruption_prepares_one_finite_recovery(tmp_path,
                                                                   monkeypatch):
    import lll.studies.closed as closed_module
    import lll.studies.task_resume as recovery

    study = tmp_path/'data'/IDENTITY
    study.mkdir(parents=True)
    (study/'completion.json').write_text('{}')
    calls = []

    class Interrupted:
        def __init__(self, root, prefix):
            self.manifest = dict(tasks=[dict(identity=task(smoke=False)['identity'])])
            self.completion = dict(state='terminal')
            self.summary = dict(completed=1, passed=False)
            self.rows = {task(smoke=False)['identity']: dict(status='interrupted')}

        def close(self):
            calls.append('closed')

    def prepare(*args, **kwargs):
        calls.append(('prepare', kwargs['max_attempts_per_task'],
                      kwargs['max_technical_interruptions'],
                      kwargs['minimum_free_bytes']))

    def recover(*args, **kwargs):
        calls.append('resume')
        return dict(state='all_tasks_finished')

    monkeypatch.setattr(closed_module, 'ClosedStudy', Interrupted)
    monkeypatch.setattr(recovery, 'prepare_campaign', prepare)
    monkeypatch.setattr(recovery, 'resume_campaign', recover)
    assert resume(tmp_path) == dict(state='all_tasks_finished')
    assert calls == ['closed', ('prepare', 2, 2, 20*1024**3), 'resume']
