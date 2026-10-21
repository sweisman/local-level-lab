# SPDX-License-Identifier: AGPL-3.0-or-later
from copy import deepcopy
import numpy as np
import pytest


def sample():
    return dict(configuration=dict(model=1,profile=True),dt=[.005]*1600,
        theta=[[0.,0.,0.] for _ in range(1600)],
        dv=[[0.,0.,-.04905] for _ in range(1600)])


def test_prefix_preserves_processing_case_and_owns_its_arrays():
    from lll.ilvis0_taylor_runtime_profile import prefix
    original=sample();before=deepcopy(original)
    result=prefix(original,model=1,profile=True)
    assert len(result['dt'])==128
    np.testing.assert_array_equal(result['dv'],original['dv'][:128])
    result['dv'][0,0]=123.;result['configuration']['model']=2
    assert original==before


@pytest.mark.parametrize('change',('model','profile','clock','length'))
def test_prefix_rejects_changed_identity_or_sampling(change):
    from lll.ilvis0_taylor_runtime_profile import prefix
    original=sample()
    if change=='model':original['configuration']['model']=0
    elif change=='profile':original['configuration']['profile']=False
    elif change=='clock':original['dt'][42]=.006
    else:original['dt'].pop()
    with pytest.raises(ValueError):prefix(original,model=1,profile=True)
