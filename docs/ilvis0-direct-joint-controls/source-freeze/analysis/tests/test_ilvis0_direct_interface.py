# SPDX-License-Identifier: AGPL-3.0-or-later
from copy import deepcopy
import pytest


def sample():
    from lll.ilvis0_dyadic_timing import MATCHED_FIELDS
    row={name:[1.,2.,3.] for name in MATCHED_FIELDS}
    row.update(center=[.1,.2,30.],source_id='one',reference_binding='two')
    return row


def test_direct_comparison_preserves_maps_and_accepts_only_nonwidening_radii():
    from lll.ilvis0_direct_interface import matched_bounds
    before=sample();after=deepcopy(before)
    for key in ('unshared_remainder','position_unshared_remainder','force_unshared_remainder','lever_unshared_remainder'):
        after[key]=[v/2 for v in before[key]]
    report=matched_bounds(before,after)
    assert report['passed'] and report['maps_preserved'] and report['remainders_nonwidening']
    after['previous_coefficients'][1]=0.
    assert not matched_bounds(before,after)['passed']


@pytest.mark.parametrize('change',('missing','wider','negative','nonfinite','shape'))
def test_direct_comparison_rejects_incomplete_or_invalid_bound_evidence(change):
    from lll.ilvis0_direct_interface import matched_bounds
    before=sample();after=deepcopy(before)
    if change=='missing':del after['unshared_remainder']
    if change=='wider':after['unshared_remainder'][1]+=1e-12
    if change=='negative':after['unshared_remainder'][1]=-1.
    if change=='nonfinite':after['unshared_remainder'][1]=float('nan')
    if change=='shape':after['unshared_remainder']=[1.,2.]
    assert not matched_bounds(before,after)['passed']
