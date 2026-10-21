# SPDX-License-Identifier: AGPL-3.0-or-later
"""Protect the unchanged numerical calculation when generalizing its sector."""
from pathlib import Path
import importlib.util


def test_future_adapter_changes_only_sector_selection_and_guard():
    module=importlib.util.find_spec('lll.ilvis0_serial_future')
    assert module is not None,'general-sector future adapter is missing'
    original=Path(importlib.util.find_spec('lll.ilvis0_direct_range_preflight').origin).read_text()
    changes={"old['task']['sector']!=0":"old['task']['sector']!=spec['sector']",
        'box=sector(0);':'box=sector(spec[\'sector\']);'}
    for before,after in changes.items():
        assert original.count(before)==1
        original=original.replace(before,after)
    assert Path(module.origin).read_text()==original
