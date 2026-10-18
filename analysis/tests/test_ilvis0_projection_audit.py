# SPDX-License-Identifier: AGPL-3.0-or-later
import copy
import numpy as np
import pytest


def module():
    from lll import ilvis0_projection_audit
    return ilvis0_projection_audit


def population():
    return [dict(segment_id=s,case_id=c,model=m,status='ready') for s in ('a','b')
        for c in ('bias1_unsubtracted','bias1_profiled_removal') for m in ('sphere_rotating','sphere_still','flat_still')]


def test_selects_only_complete_predeclared_artifact_sets_without_cost_ranking():
    values=population();values[-1]['status']='not_saved';before=copy.deepcopy(values)
    selected=module().complete_groups(values)
    assert list(selected)==['a'] and len(selected['a'])==6 and values==before


@pytest.mark.parametrize('bad',['duplicate','missing','case','model'])
def test_invalid_inventory_population_fails_closed(bad):
    rows=population()
    if bad=='duplicate':rows.append(copy.deepcopy(rows[0]))
    if bad=='missing':rows.pop()
    if bad=='case':rows[0]['case_id']='other'
    if bad=='model':rows[0]['model']='other'
    with pytest.raises(ValueError):module().complete_groups(rows)


def test_projection_retains_null_columns_and_reports_descriptive_rank():
    from lll.ilvis0_observation_projection import ReceiverProjection
    p=ReceiverProjection(np.eye(6),('height',));j=np.tile(np.eye(3),(2,1))
    report=module().assess(p,np.arange(6,dtype=float),j)
    assert report['cost']==pytest.approx(29.) and report['numerical_rank']==1
    assert report['columns']==3 and report['observations']==2
    assert report['scientific_decision']=='abstain' and not report['reoptimized']


def test_fixed_parameter_comparison_covers_every_case_model_and_projection():
    rows=[]
    for case in ('bias1_unsubtracted','bias1_profiled_removal'):
        for view in ('full','horizontal','height'):
            for model,cost in (('sphere_rotating',1.),('sphere_still',2.),('flat_still',10.)):
                rows.append(dict(case_id=case,view=view,model=model,cost=cost))
    result=module().contrasts(rows)
    assert len(result)==6 and all(r['fixed_parameter_shape_preference']=='globe' for r in result)
    assert all(r['flat_minus_globe_cost']==9. and r['not_reoptimized'] for r in result)
    rows.pop()
    with pytest.raises(ValueError):module().contrasts(rows)


def test_height_only_ranking_change_is_described_without_relabeling_a_fit():
    rows=[]
    for case in ('bias1_unsubtracted','bias1_profiled_removal'):
        for view in ('full','horizontal','height'):
            costs=(3.,4.,1.) if view=='height' else (1.,2.,10.)
            rows.extend(dict(case_id=case,view=view,model=m,cost=c) for m,c in zip(('sphere_rotating','sphere_still','flat_still'),costs))
    report=module().contrasts(rows)
    assert sum(r['fixed_parameter_shape_preference']=='flat' for r in report)==2
    assert all(r['scientific_decision']=='abstain' for r in report)
