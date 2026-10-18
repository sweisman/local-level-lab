# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
from pathlib import Path
import pytest
from lll.ilvis0_projected_trust_qualification import tasks


def module():
    path=Path(__file__).with_name('ilvis0_projected_horizontal_worker.py')
    assert path.exists(),'horizontal capability policy missing'
    spec=importlib.util.spec_from_file_location('horizontal_test',path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def source():
    rows=[dict(r,passed=True) for r in tasks()]
    pairs=[dict(model=r['model'],clock=r['clock'],axes=r['axes'],passed=len(r['axes'])==2) for r in rows[::2]]
    return dict(results=rows,pairs=pairs,passed=False)


def test_horizontal_capability_does_not_promote_failed_height_mode():
    result=module().horizontal_inventory(source())
    assert result['passed'] and len(result['results'])==12 and len(result['pairs'])==6
    assert result['qualified_axes']==[['latitude','longitude']]
    assert result['unqualified_axes']==[['height']] and result['preceding_overall_passed'] is False


def test_any_unfinished_horizontal_comparison_blocks_capability():
    parent=source();next(r for r in parent['results'] if len(r['axes'])==2)['passed']=False
    with pytest.raises(ValueError):module().horizontal_inventory(parent)
