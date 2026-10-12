# SPDX-License-Identifier: AGPL-3.0-or-later
import json
from pathlib import Path

import pytest

ROOT=Path(__file__).resolve().parents[2]/'docs'


def grids():
    return {label:(json.loads((ROOT/path/'summary.json').read_text()),
                   json.loads((ROOT/path/'manifest.json').read_text()))
        for label,path in (
            ('original','ilvis0-z-profile-20261011'),
            ('removal','ilvis0-z-profile-removal-20261011'),
            ('replication','ilvis0-z-profile-replication-20261011'))}


def compare(data):
    from lll.ilvis0_z_followup_audit import compare
    return compare(data)


def test_completed_and_unfinished_nodes_are_separated_without_relabeling():
    data=grids();out=compare(data)
    assert out['optimizer_starts']==out['native_predictions']==0
    assert len(out['fits'])==81
    assert len(out['nodes'])==27
    assert [(r['study'],r['converged'],r['complete_nodes']) for r in out['studies']]==[
        ('original',27,9),('removal',27,9),('replication',25,7)]
    assert out['studies'][2]['shape_preference']=='unresolved'
    assert out['studies'][2]['background_field_preference'] is None
    assert len(out['failures'])==2
    assert all(f['saved_stationarity_passed'] and f['budget_exhausted'] for f in out['failures'])
    assert all(f['status']=='unresolved' and not f['solver_reported_success'] for f in out['failures'])
    assert all(not f['converged'] for f in data['replication'][0]['fits'] if not f['solver_reported_success'])


def test_processing_match_is_by_fixed_coordinates_and_model():
    out=compare(grids())
    assert len(out['processing_changes'])==27
    preferred=[r for r in out['processing_changes'] if r['model']=='sphere_rotating']
    assert max(r['removal_fraction'] for r in preferred)<2e-9
    assert max(abs(r['relative_cost_change']) for r in preferred)<1e-4
    assert all(r['paired_status']=='converged' for r in preferred)


def test_model_cost_ranges_use_converged_points_and_expose_upper_bounds():
    out=compare(grids())
    preferred=next(r for r in out['models'] if r['study']=='replication' and r['model']=='sphere_rotating')
    assert preferred['converged']==7 and preferred['unresolved']==2
    assert preferred['completed_cost_min'] is not None
    assert preferred['unfinished_achieved_cost_min'] is not None
    assert preferred['remaining_bounds_max']==0


@pytest.mark.parametrize('corruption',['missing_study','wrong_recording','wrong_case','missing_node','wrong_identity'])
def test_mismatched_grids_are_rejected(corruption):
    data=grids()
    if corruption=='missing_study':del data['original']
    if corruption=='wrong_recording':data['removal'][0]['provenance']['segment_id']='another'
    if corruption=='wrong_case':data['removal'][1]['cases'][0]['profile']=False
    if corruption=='missing_node':data['replication'][0]['fits'].pop()
    if corruption=='wrong_identity':data['original'][0]['fits'][0]['identity']='unregistered'
    with pytest.raises(ValueError):compare(data)
