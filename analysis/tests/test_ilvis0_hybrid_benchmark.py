# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite lifecycle gates for the selective-precision long benchmark."""
import pytest


def test_hybrid_long_benchmark_has_six_finite_generated_tasks():
    """Catch extra starts, observed-data use, or an expanded native allowance."""
    from lll.ilvis0_hybrid_benchmark import recipe, tasks

    r = recipe()
    matrix = tasks()
    assert (r['duration_s'], r['rate_hz'], r['queries']) == (1200., 300, 1200)
    assert (r['workers'], r['threads'], r['maximum_wall_s']) == (1, 1, 7200.)
    assert len(matrix) == 6
    assert sum(t['limits']['native_calls'] for t in matrix) == 12
    assert sum(t['limits']['packet_visits'] for t in matrix) == 5_184_000_000
    assert r['optimizer_starts'] == r['original_reads'] == r['protected_reads'] == r['retries'] == 0


def test_hybrid_long_report_rejects_unclosed_study_before_native_import(tmp_path):
    """A report cannot launch or infer missing benchmark calculations."""
    from lll.ilvis0_hybrid_benchmark import inspect

    with pytest.raises(ValueError, match='closed study'):
        inspect(tmp_path)
