# SPDX-License-Identifier: AGPL-3.0-or-later
from pathlib import Path
import importlib.util
import pytest


def test_three_family_adapter_preserves_every_numerical_operation():
    spec=importlib.util.find_spec('lll.ilvis0_reused_prediction_three')
    assert spec is not None,'three-family saved-report adapter is missing'
    original=Path(importlib.util.find_spec('lll.ilvis0_reused_prediction').origin).read_text()
    changes={
        'provenance_reads=4':'provenance_reads=6',
        "len(spec['provider_sources'])!=2":"len(spec['provider_sources'])!=3",
        'two explicit qualified provider families required':'three explicit qualified provider families required',
    }
    for before,after in changes.items():
        assert original.count(before)==1
        original=original.replace(before,after)
    assert Path(spec.origin).read_text()==original


@pytest.mark.parametrize('epochs,count',((1,1),(2,3),(6,16)))
def test_only_provider_provenance_allowance_changes(epochs,count):
    from lll.ilvis0_reused_prediction import allowances as previous
    from lll.ilvis0_reused_prediction_three import allowances
    providers=[count]*(epochs+1)
    assert allowances(epochs,providers)==dict(previous(epochs,providers),provenance_reads=6)
