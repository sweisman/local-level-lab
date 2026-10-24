# SPDX-License-Identifier: AGPL-3.0-or-later
"""Metadata-only protocol preparation, safe while numerical workers run."""
import hashlib
import inspect
from pathlib import Path

import pytest


def _sources():
    return {name:hashlib.sha256(Path('analysis/lll',name).read_bytes()).hexdigest()
        for name in ('airquantumgrav_prediction.py','airquantumgrav_height_training.py')}


def test_wide_training_reuses_qualified_protocols_without_global_patches():
    from lll.ilvis0_wide_training import bind
    from lll import airquantumgrav_prediction as prediction,airquantumgrav_height_training as control
    original=(prediction.train_and_forecast,control.calculate)
    run,calculate,proof=bind(expected_sources=_sources())
    assert prediction.train_and_forecast is original[0] and control.calculate is original[1]
    assert inspect.signature(run)==inspect.signature(original[0])
    assert inspect.signature(calculate)==inspect.signature(original[1])
    assert proof['prediction']['substitutions']==proof['control']['substitutions']==1
    assert proof['prediction']['import_name']=='training_problem'
    assert proof['control']['import_name']=='train_and_forecast'
    assert proof['source_sha256']==_sources()
    again,other,second=bind(expected_sources=_sources())
    assert second==proof and again is not run and other is not calculate
    assert prediction.train_and_forecast is original[0] and control.calculate is original[1]


@pytest.mark.parametrize('bad',({},{'airquantumgrav_prediction.py':'0'*64,'airquantumgrav_height_training.py':'0'*64}))
def test_wide_training_rejects_unbound_protocol_sources(bad):
    from lll.ilvis0_wide_training import bind
    with pytest.raises(ValueError,match='source'):bind(expected_sources=bad)
