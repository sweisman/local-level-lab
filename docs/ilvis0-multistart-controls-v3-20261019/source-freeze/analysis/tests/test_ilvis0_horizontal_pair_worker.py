# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
from pathlib import Path
import pytest


def module():
    path=Path(__file__).with_name('ilvis0_horizontal_pair_worker.py')
    assert path.exists(),'pair worker missing'
    spec=importlib.util.spec_from_file_location('horizontal_pair_test',path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def parent():
    rows=[dict(identity=str(i),model=model,case_id=case,start=start,passed=True,
               fit=dict(normalized_parameters=[0.]))
          for i,(model,case,start) in enumerate((m,c,s) for m in ('sphere_rotating','sphere_still','flat_still')
             for c in ('bias1_unsubtracted','bias1_profiled_removal') for s in ('zero','opposed'))]
    return dict(results=[dict(passed=True)]*8,primaries=rows,
        pairs=[dict(model=m,case_id=c,passed=not(m=='sphere_still' and c=='bias1_unsubtracted'))
          for m in ('sphere_rotating','sphere_still','flat_still') for c in ('bias1_unsubtracted','bias1_profiled_removal')])


def test_only_exact_disagreeing_pair_is_selected():
    rows=module().select(parent())
    assert len(rows)==2 and {r['start'] for r in rows}=={'zero','opposed'}
    assert all(r['model']=='sphere_still' and r['case_id']=='bias1_unsubtracted' for r in rows)


def test_any_unpassed_parent_fit_blocks_continuation():
    p=parent();p['results'][0]=dict(passed=False)
    with pytest.raises(ValueError):module().select(p)


def test_changed_pair_failure_is_rejected():
    p=parent();p['pairs'][0]['passed']=False
    with pytest.raises(ValueError):module().select(p)
