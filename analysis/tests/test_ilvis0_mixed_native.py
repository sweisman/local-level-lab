# SPDX-License-Identifier: AGPL-3.0-or-later
"""Small native prototype checks; require a reserved numerical core."""
import hashlib
from pathlib import Path
import numpy as np
import pytest


@pytest.mark.parametrize('model',['sphere_rotating','sphere_still','flat_still'])
@pytest.mark.parametrize('profile',[False,True])
def test_mixed_candidate_preserves_values_and_all_derivatives_without_global_patch(model,profile,tmp_path):
    from test_ilvis0_wide_tangent import _problem
    from lll import ilvis0_wide_tangent as reference
    from lll.ilvis0_mixed_tangent import load
    original=reference.derive;version=reference.VERSION
    base,anchor,material=_problem(tmp_path,model,profile)
    full,full_meta=reference.load(tmp_path,gravity_anchor_height_m=anchor)
    mixed,meta=load(tmp_path,gravity_anchor_height_m=anchor,
        expected_source_sha256=hashlib.sha256(Path('analysis/lll/ilvis0_tangent.cpp').read_bytes()).hexdigest(),
        expected_loader_sha256=hashlib.sha256(Path(reference.__file__).read_bytes()).hexdigest())
    a=reference.problem(base,kernel=full);b=reference.problem(base,kernel=mixed)
    point=np.linspace(-.02,.02,len(base.bounds.active))
    ar,aj,ab=a.residual_tangent(point,model);br,bj,bb=b.residual_tangent(point,model)
    assert np.array_equal(ar,br) and np.array_equal(a.predict(point,model),b.predict(point,model))
    assert ab==bb and aj.shape==bj.shape==(18,26+int(profile))
    assert np.allclose(aj,bj,rtol=2e-10,atol=2e-10)
    assert reference.derive is original and reference.VERSION==version
    assert meta['internal_mantissa_bits']==full_meta['internal_mantissa_bits']>53
    assert meta['packet_clock_changed'] is False and meta['production_method_changed'] is False
    assert meta['source_sha256']!=full_meta['source_sha256'] and meta['shared_loader_unchanged']
