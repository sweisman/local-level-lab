# SPDX-License-Identifier: AGPL-3.0-or-later
from lll.esa_packet_bound_profile import equivalent_report, profile_once


def test_profile_keeps_result_and_records_failed_work():
    root = {'window': 1}
    answer, profile = profile_once(lambda: root)
    assert answer is root
    assert profile['error'] is None
    assert profile['total_calls'] > 0

    def error():
        raise ValueError('bound deadline test')

    answer, profile = profile_once(error)
    assert answer is None
    assert profile['error'] == dict(type='ValueError', message='bound deadline test')
    assert profile['total_calls'] > 0


def test_profile_agreement_requires_equal_bound_bytes_and_work():
    from lll.studies.artifacts import digest

    gold = dict(sha256=digest(b'new'), work={'packet_steps': 470})
    replay = dict(passed=True, work={'packet_steps': 470})
    assert equivalent_report(replay, b'new', gold)
    assert not equivalent_report(replay, b'old', gold)
    assert not equivalent_report(dict(replay, work={}), b'new', gold)
    assert not equivalent_report(None, None, gold)
