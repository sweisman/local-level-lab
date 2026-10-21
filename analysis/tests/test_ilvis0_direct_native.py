# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib
import numpy as np
import pytest
from test_ilvis0_conditioned_transform_native import case


@pytest.fixture(scope='module')
def kernels(tmp_path_factory):
    from lll.ilvis0_source_stream import load_stream
    from lll.ilvis0_source_derivative_intervals import load_kernel
    from lll.ilvis0_source_point_derivatives import load_kernel as load_point
    directory=tmp_path_factory.mktemp('direct-native')
    return load_stream(directory)[0],load_kernel(directory)[0],load_point(directory)[0]


@pytest.mark.parametrize('model,profile',[(m,p) for m in range(3) for p in (False,True)])
def test_direct_candidate_preserves_maps_and_never_widens_remainders(model,profile,kernels):
    candidate=importlib.import_module('lll.ilvis0_direct_native')
    from lll import ilvis0_dyadic_native as previous
    config,theta,dv,dt,center,lo,hi,reference,conditioning=case(model,profile)
    arguments=dict(time=.05,lower=lo,upper=hi,reference=reference,conditioning=conditioning,
        source_kernel=kernels[0],derivative_kernel=kernels[1])
    before=previous.enclose(config,theta,dv,dt,**arguments)
    after=candidate.enclose(config,theta,dv,dt,point_kernel=kernels[2],**arguments)
    np.testing.assert_array_equal(after.center,before.center)
    assert np.all(after.unshared_remainder<=before.unshared_remainder)
    for name in ('previous_coefficients','acceleration_coefficients','transform_coefficients'):
        np.testing.assert_array_equal(getattr(after,name).matrix,getattr(before,name).matrix)
    for name in ('source_derivative_steps','source_reference_steps','conditioning','source_initial_padding'):
        assert after.metadata[name]==before.metadata[name]
    assert after.metadata['source_direct_steps']==after.metadata['source_derivative_steps']
    assert after.metadata['source_direct_remainder_installed']


def test_direct_source_binding_domain_and_phase_cannot_be_substituted(kernels):
    from dataclasses import replace
    from lll.ilvis0_direct_source_taylor import SourceDirectStream,DirectBodyInterval
    from lll.ilvis0_source_stream import SourceStream
    config,theta,dv,dt,center,lo,hi,reference,conditioning=case(0,False)
    inputs=dict(configuration=config,theta=theta,dv=dv,dt=dt)
    values=SourceDirectStream(inputs,reference,lo,hi,.05,maximum_packets=len(dt),
        derivative_kernel=kernels[1],point_kernel=kernels[2])
    body=DirectBodyInterval(reference,conditioning,lo,hi,direct_source_binding=values.direct.source_binding)
    numerical=SourceStream(kernels[0],inputs,center,.05,maximum_packets=len(dt)).append()
    proof=values.append()['phases'][0]
    original=body.bound(proof,numerical,phase=0)
    assert original.details['source_direct_remainder_installed']
    for field,value in (('source_binding','wrong'),('packet_index',2),('nominal_time_s',.051),
                        ('center',tuple(np.zeros(27))),('lower',tuple(np.zeros(27)))):
        corrupted=replace(proof,direct_frame=replace(proof.direct_frame,**{field:value}))
        with pytest.raises(ValueError):body.bound(corrupted,numerical,phase=0)
    with pytest.raises(ValueError):body.bound(proof,numerical,phase=1)
