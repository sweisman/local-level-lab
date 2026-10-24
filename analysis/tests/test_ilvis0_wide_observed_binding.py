# SPDX-License-Identifier: AGPL-3.0-or-later
"""Metadata-only preparation; no observed inputs or numerical libraries."""
import hashlib
import inspect
from pathlib import Path

import pytest


def sources():
    from lll.ilvis0_wide_observed import SOURCES
    return {n:hashlib.sha256(Path('analysis/lll',n).read_bytes()).hexdigest() for n in SOURCES}


def test_wide_observed_protocol_preserves_original_signatures_and_shared_functions():
    from lll.ilvis0_wide_observed import bind
    from lll import airquantumgrav_observed as base,airquantumgrav_observed_height as height
    original=(base.calculate,height.calculate)
    calculate,proof=bind(expected_sources=sources())
    assert inspect.signature(calculate)==inspect.signature(height.calculate)
    assert base.calculate is original[0] and height.calculate is original[1]
    assert proof['observed']['substitutions']==proof['height']['substitutions']==1
    assert proof['observed']['import_name']=='train_and_forecast'
    assert proof['height']['import_name']=='calculate'
    again,second=bind(expected_sources=sources())
    assert second==proof and again is not calculate
    assert base.calculate is original[0] and height.calculate is original[1]


def test_wide_observed_binding_rejects_missing_or_changed_source_before_calculation():
    from lll.ilvis0_wide_observed import bind
    with pytest.raises(ValueError,match='source'):bind(expected_sources={})
    bad=sources();bad['airquantumgrav_observed.py']='0'*64
    with pytest.raises(ValueError,match='source'):bind(expected_sources=bad)
