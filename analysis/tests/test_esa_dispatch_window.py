import pytest

from lll.studies.artifacts import digest, encoded


def test_fresh_esa_dispatch_window_retains_the_original_twenty_minute_cadence(tmp_path, monkeypatch):
    from lll import esa_dispatch_window as selector

    previous = {'plan': {'windows': [{'first_index': 0, 'last_index': 100}]}}
    turns = {'segments': [
        {'first_index': 100, 'last_index': 3399,
         'disjoint_supports': [{'first_index': 2800, 'last_index': 2850}]},
        {'first_index': 5000, 'last_index': 8000, 'disjoint_supports': []},
    ]}
    for name, field, value in ((selector.PRIOR, 'PRIOR_SHA', previous),
                               (selector.RESULT, 'INVENTORY_SHA', turns)):
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        raw = encoded(value)
        target.write_bytes(raw)
        monkeypatch.setattr(selector, field, digest(raw))

    result = selector.preflight(tmp_path)
    window = result['window']
    assert result['candidate_ranges'] == 2
    assert window['first_index'] == 161
    assert window['last_index'] - window['first_index'] == 2400
    assert window['last_index'] + result['buffer_reports'] < 2800
    assert len(range(window['query_first_index'], window['training_last_index'] + 1, 2)) == 800
    assert len(range(window['prediction_first_index'], window['query_last_index'] + 1, 2)) == 400
    assert window['query_stride'] == 2
    assert result['fit_starts'] == result['original_reads'] == result['protected_reads'] == 0

    (tmp_path / selector.RESULT).write_bytes(encoded({'segments': []}))
    with pytest.raises(ValueError, match='exact saved'):
        selector.preflight(tmp_path)
