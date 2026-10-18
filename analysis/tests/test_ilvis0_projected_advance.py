# SPDX-License-Identifier: AGPL-3.0-or-later
import copy
import importlib.util
from pathlib import Path
import pytest
from lll.ilvis0_projected_trust_qualification import tasks


def module():
    path=Path(__file__).with_name('ilvis0_projected_advance.py')
    spec=importlib.util.spec_from_file_location('advance_test',path)
    assert path.exists(),'saved-only advancement helper missing'
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def fixtures():
    rows=[dict(r,passed=True) for r in tasks()];pairs=[dict(model=r['model'],clock=r['clock'],axes=r['axes'],passed=True) for r in rows[::2]]
    bad=next(p for p in pairs if (p['model'],p['clock'],p['axes'])==('sphere_still','nominal',['height']));bad['passed']=False
    target=[dict(r,identity=r['identity']+'-continuation') for r in rows if all(r[k]==bad[k] for k in ('model','clock','axes'))]
    return dict(results=rows,pairs=pairs,passed=False),dict(results=target,pairs=[dict(bad,passed=True)],passed=True)


def test_join_keeps_22_companions_and_original_failed_gate_immutable():
    parent,continued=fixtures();before=copy.deepcopy(parent);out=module().combine(parent,continued)
    assert out['passed'] and len(out['results'])==24 and len(out['pairs'])==12
    assert sum(r['identity'].endswith('-continuation') for r in out['results'])==2
    assert parent==before and out['preceding_qualification_passed'] is False


def test_failed_continuation_never_releases_next_stage():
    parent,continued=fixtures();continued['passed']=False;continued['pairs'][0]['passed']=False
    assert not module().combine(parent,continued)['passed']


def test_unrelated_endpoint_substitution_is_rejected():
    parent,continued=fixtures();continued['results'][0]['model']='flat_still'
    with pytest.raises(ValueError):module().combine(parent,continued)
