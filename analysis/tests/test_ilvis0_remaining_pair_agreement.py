"""Saved forecast-pair disagreement cannot retroactively pass failed fits."""

import numpy as np
import pytest

from lll import ilvis0_remaining_pair_agreement as audit


def _case(start,shift=0.,converged=True):
    path=np.zeros((9,3));path[:,0]=.7
    path[6:,2]=1000.+shift
    return dict(segment_id='one',origin='outer',start=start,
                converged=converged,training_cost=.02+start*1e-8,
                training_epochs=6,prediction_epochs=3,
                forecast=path.tolist())


def test_pair_reports_withheld_path_difference_and_original_stops():
    row=audit.compare_pair([_case(0,converged=False),_case(1,.05)])
    assert row['both_converged'] is False
    assert row['later_maximum_3d_separation_m']==pytest.approx(.05)
    assert row['training_cost_range']==pytest.approx(1e-8)
    assert row['within_generated_point_agreement_limit'] is True
    assert row['reclassified_fits']==0


def test_pair_requires_two_matched_complete_forecasts():
    with pytest.raises(ValueError):
        audit.compare_pair([_case(0),_case(0)])
    bad=_case(1);bad['origin']='inner'
    with pytest.raises(ValueError):
        audit.compare_pair([_case(0),bad])
