# SPDX-License-Identifier: AGPL-3.0-or-later
"""Metadata-only controls for an isolated arithmetic prototype."""
import hashlib
from pathlib import Path
import pytest


def fixture():
    original=Path('analysis/lll/ilvis0_tangent.cpp').read_text();mark=original.index('static void mul')
    head=original[:mark].replace('double v; std::array<double,27> d;',
        'long double v; std::array<long double,27> d;').replace('Dual(double value=0)',
        'Dual(long double value=0)').replace('double q=','long double q=')
    return (head+original[mark:]).encode()


def test_mixed_source_preserves_primal_expressions_and_everything_after_dual_arithmetic():
    from lll.ilvis0_mixed_tangent import derive
    raw=fixture();result=derive(raw,expected_sha256=hashlib.sha256(raw).hexdigest())
    assert b'long double v; std::array<double,27> d;' in result
    assert result.split(b'static void mul',1)[1]==raw.split(b'static void mul',1)[1]
    for expression in (b'Dual r(a.v+b.v)',b'Dual r(a.v-b.v)',b'Dual r(a.v*b.v)',b'Dual r(a.v/b.v)',
            b'Dual r(std::sin(a.v))',b'Dual r(std::cos(a.v))',b'Dual r(std::sqrt(a.v))',b'Dual r(std::pow(a.v,b))'):
        assert expression in result


def test_mixed_source_requires_exact_input_hash_and_supported_dual_layout():
    from lll.ilvis0_mixed_tangent import derive
    raw=fixture()
    with pytest.raises(ValueError,match='hash'):derive(raw,expected_sha256='0'*64)
    altered=raw.replace(b'std::array<long double,27>',b'std::array<long double,26>')
    with pytest.raises(ValueError,match='layout'):derive(altered,expected_sha256=hashlib.sha256(altered).hexdigest())


def test_mixed_loader_rejects_changed_shared_loader_before_numerical_imports(tmp_path):
    from lll.ilvis0_mixed_tangent import load
    with pytest.raises(ValueError,match='loader'):
        load(tmp_path,expected_source_sha256='0'*64,expected_loader_sha256='0'*64)
    assert not any(tmp_path.iterdir())
