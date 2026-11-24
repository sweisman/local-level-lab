"""Finite performance receipt for the long receiver likelihood."""

import json

import pytest


def test_benchmark_seals_finite_inputs_and_outputs(tmp_path):
    from lll.structured_receiver_benchmark import run

    first = run(12, tmp_path / 'first.json')
    second = run(12, tmp_path / 'second.json')
    assert first['epochs'] == second['epochs'] == 12
    assert first['jacobian_columns'] == 26
    assert first['input_sha256'] == second['input_sha256']
    assert first['output_sha256'] == second['output_sha256']
    assert len(first['core_source_sha256']) == 64
    assert len(first['benchmark_source_sha256']) == 64
    assert first['peak_rss_kib'] > 0
    assert first['wall_seconds'] > 0
    assert json.loads((tmp_path / 'first.json').read_text()) == first


def test_benchmark_rejects_unbounded_request(tmp_path):
    from lll.structured_receiver_benchmark import run

    with pytest.raises(ValueError):
        run(64081, tmp_path / 'invalid.json')
    assert not (tmp_path / 'invalid.json').exists()
