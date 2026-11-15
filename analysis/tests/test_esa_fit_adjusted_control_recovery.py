"""The generated control's recovery policy binds its prepared source."""

import pytest


def test_known_answer_recovery_requires_sealed_matching_source(tmp_path,
                                                               monkeypatch):
    from lll import esa_study_recovery as shared
    from lll.esa_fit_adjusted_control_recovery import SPEC

    (tmp_path/SPEC.parent).mkdir(parents=True)
    monkeypatch.setattr(shared.runner, 'verify', lambda path: dict(
        scope=SPEC.scope, tasks=[{}, {}], accounting_format='sqlite-v1',
        allocation=dict(workers=2, threads=1)))
    monkeypatch.setattr(shared, '_qualification',
                        lambda root, spec: ('request-hash', 'report-hash'))
    monkeypatch.setattr(shared.runner, '_sha', lambda path: 'original-hash')
    assert shared.freeze(tmp_path, SPEC)['state'] == 'frozen'

    def changed(path):
        return ('changed-wrapper' if str(path).endswith(SPEC.wrapper)
                else 'original-hash')

    monkeypatch.setattr(shared.runner, '_sha', changed)
    with pytest.raises(ValueError, match='policy changed'):
        shared.verify_policy(tmp_path, SPEC)
