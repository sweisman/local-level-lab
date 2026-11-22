"""Fast active-study discovery without scanning archived result ledgers."""

import fcntl
import json

import pytest

from lll.studies.active_allocation import active_paths, other_threads, register


def test_active_scan_finds_held_study_and_counts_targeted_status(tmp_path):
    (tmp_path/'analysis').mkdir()
    (tmp_path/'data'/'busy').mkdir(parents=True)
    (tmp_path/'data'/'done').mkdir()
    (tmp_path/'analysis'/'study-status.json').write_text(json.dumps(
        {'studies':[{'name':'busy','path':'data/busy'},
                    {'name':'done','path':'data/done'}]}))
    (tmp_path/'data'/'busy'/'worker.lock').touch()
    (tmp_path/'data'/'done'/'worker.lock').touch()
    (tmp_path/'data'/'done'/'status.json').write_text(json.dumps(
        {'state':'running','numerical_threads':4}))
    with (tmp_path/'data'/'busy'/'worker.lock').open('rb') as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        assert active_paths(tmp_path) == ['data/busy']
        assert other_threads(tmp_path, workers=1,
                             status_reader=lambda path: dict(
                                 state='running', threads=2, warnings=[])) == 2


def test_active_scan_rejects_bad_registry_and_excess_threads(tmp_path):
    (tmp_path/'analysis').mkdir()
    (tmp_path/'analysis'/'study-status.json').write_text(json.dumps(
        {'studies':[{'name':'bad','path':'../personal'}]}))
    with pytest.raises(ValueError, match='data'):
        active_paths(tmp_path)
    (tmp_path/'analysis'/'study-status.json').write_text(json.dumps(
        {'studies':[{'name':'busy','path':'data/busy'}]}))
    (tmp_path/'data'/'busy').mkdir(parents=True)
    (tmp_path/'data'/'busy'/'worker.lock').touch()
    with (tmp_path/'data'/'busy'/'worker.lock').open('rb') as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        with pytest.raises(ValueError, match='four'):
            other_threads(tmp_path, workers=2,
                          status_reader=lambda path: dict(
                              state='running', threads=3, warnings=[]))


def test_register_is_idempotent_for_prepared_study(tmp_path):
    (tmp_path/'analysis').mkdir()
    (tmp_path/'analysis'/'study-status.json').write_text('{"studies":[]}')
    study = tmp_path/'data'/'study'
    study.mkdir(parents=True)
    (study/'manifest.json').write_text('{}')
    assert register(tmp_path, name='study', path='data/study') is True
    assert register(tmp_path, name='study', path='data/study') is False
    rows = json.loads((tmp_path/'analysis'/'study-status.json').read_bytes())['studies']
    assert rows == [dict(name='study', path='data/study')]
