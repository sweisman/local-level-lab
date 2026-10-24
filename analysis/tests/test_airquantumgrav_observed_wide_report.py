# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved evidence checks; no native execution or numerical imports."""
import copy
import hashlib
from pathlib import Path

import pytest


def test_observed_wide_report_rejects_unfinished_before_numerical_imports(tmp_path):
    from lll.airquantumgrav_observed_wide_report import inspect
    with pytest.raises(ValueError,match='closed study'):inspect(tmp_path)


def compilation():
    from lll.ilvis0_wide_tangent import derive,VERSION
    raw=Path('analysis/lll/ilvis0_tangent.cpp').read_bytes();sha=hashlib.sha256(raw).hexdigest()
    sources={'analysis/lll/ilvis0_native.c':'c'*64,'analysis/lll/ilvis0_tangent.cpp':sha}
    common=dict(gravity_model='inverse-square-height-v1',gravity_anchor_height_m=1000.)
    meta=dict(value=dict(common,source_sha256='c'*64,binary_sha256='a'*64,compiler='cc test'),
        tangent=dict(common,version=VERSION,original_source_sha256=sha,
            source_sha256=hashlib.sha256(derive(raw,expected_sha256=sha)).hexdigest(),binary_sha256='b'*64,
            compiler='c++ test',flags=['-O2','-std=c++17','-fPIC','-shared'],internal_mantissa_bits=64,
            residual_subtraction='before-binary64-cast',packet_clock_changed=False,
            clock_dispatch='binary64-frozen',profile_mapping='binary64-frozen',
            query_fraction='binary64-frozen',parameter_products='binary64-frozen'))
    return dict(meta=meta,raw=raw,sources=sources,environment=dict(compilers={'cc':'cc test','c++':'c++ test'}),anchor=1000.)


def test_observed_wide_compilation_verifies_actual_derived_source_without_relabeled_hashes():
    from lll.airquantumgrav_observed_wide_report import verify_compilation
    data=compilation();original=copy.deepcopy(data)
    assert verify_compilation(**data)=={'value':'a'*64,'tangent':'b'*64}
    assert data==original
    assert data['meta']['tangent']['source_sha256']!=data['meta']['tangent']['original_source_sha256']


@pytest.mark.parametrize('kind,key,value',[
    ('tangent','source_sha256','0'*64),('tangent','original_source_sha256','0'*64),
    ('tangent','internal_mantissa_bits',53),('tangent','packet_clock_changed',True),
    ('tangent','residual_subtraction','after-binary64-cast'),('tangent','profile_mapping','wide'),
    ('tangent','query_fraction','wide'),('tangent','parameter_products','wide'),
    ('tangent','compiler','other'),('tangent','flags',['-ffast-math']),
    ('tangent','gravity_anchor_height_m',2000.),('value','source_sha256','0'*64),
    ('value','gravity_anchor_height_m',2000.),('value','binary_sha256','missing')])
def test_observed_wide_compilation_rejects_changed_arithmetic_clock_or_provenance(kind,key,value):
    from lll.airquantumgrav_observed_wide_report import verify_compilation
    data=compilation();data['meta'][kind][key]=value
    with pytest.raises(ValueError):verify_compilation(**data)
