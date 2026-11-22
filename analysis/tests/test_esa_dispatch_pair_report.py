import pytest


def test_pair_report_retains_all_sixteen_terminal_pairs_and_failed_groups(monkeypatch):
    from lll import esa_dispatch_pair_report as report, esa_dispatch_pairs as design

    declared = design.tasks(native_packets=359729, training_prefix_packets=239750)
    terminal = {case['identity']: dict(result={'passed': True}, source='original',
                                      result_sha256='a'*64, forecasts={}) for case in declared}
    failed = declared[-1]['identity']
    terminal[failed]['result'] = {'passed': False, 'reason': 'native operation budget exhausted'}
    assessed = []

    def group(pairs, **kwargs):
        assert set(pairs) == {0, 1}
        both = all(pair['passed'] for pair in pairs.values())
        assessed.append(both)
        return dict(state='equivalent' if both else 'pair_failed', equivalent=both)

    monkeypatch.setattr(report, 'assess_group', group)
    with pytest.raises(ValueError, match='all 16 terminal'):
        report.summarize(declared, {k: v for k, v in terminal.items() if k != failed},
                         times=[], materials='b'*64)
    assert not assessed
    result = report.summarize(declared, terminal, times=[], materials='b'*64)
    assert result['terminal_pairs'] == 16
    assert result['passing_pairs'] == 15
    assert result['equivalent_groups'] == 7
    assert result['groups'][-1]['state'] == 'pair_failed'
    assert result['pairs'][-1]['reason'] == 'native operation budget exhausted'
    assert result['equivalent_on_window'] is False
