# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest

from lll import ilvis0_interval_controls as controls
from lll import ilvis0_geographic_controls as original
from lll import ilvis0_exploratory as explore, ilvis0_shape as shape


@pytest.fixture(scope='module')
def kernels(tmp_path_factory):
    path=tmp_path_factory.mktemp('interval-kernels')
    return explore.load_kernel(path)[0],shape.load_tangent(path)[0]


@pytest.mark.parametrize('model',explore.MODELS)
@pytest.mark.parametrize('clock',('nominal','variable'))
def test_unmodified_resolution_reproduces_frozen_analytic_generator(model,clock):
    old=original.fixture(model,clock)
    f=controls.fixture(model,1,'original',clock)
    np.testing.assert_array_equal(f['gps'],old['gps'])
    np.testing.assert_array_equal(f['gps_times'],old['gps_times'])
    np.testing.assert_allclose(f['theta'],old['theta'],atol=2e-17,rtol=0)
    np.testing.assert_allclose(f['dv'],old['dv'],atol=2e-16,rtol=0)
    assert f['truth']==old['truth']


def test_finer_intervals_preserve_external_epochs_and_physical_duration():
    coarse=controls.fixture('sphere_rotating',1)
    fine=controls.fixture('sphere_rotating',4)
    assert len(fine['dt'])==4*len(coarse['dt'])
    assert np.all(fine['dt']==.00125)
    assert abs(fine['dt'].sum()-coarse['dt'].sum())<1e-12
    np.testing.assert_array_equal(fine['gps'],coarse['gps'])
    assert fine['truth']==coarse['truth']
    # Fine increments are reintegrated continuous rates, not duplicated/split packets.
    assert np.max(abs(fine['theta'].reshape(-1,4,3)-coarse['theta'][:,None,:]/4))>1e-8


def test_roll_excitation_preserves_trajectory_and_improves_offset_conditioning(kernels):
    a=controls.fixture('sphere_rotating',4,'original')
    b=controls.fixture('sphere_rotating',4,'roll')
    np.testing.assert_array_equal(a['gps'],b['gps'])
    assert a['truth']==b['truth']
    values=[]
    for f in (a,b):
        p=original.problem(f,*kernels)
        _,jac,_=p.residual_tangent(original.truth_point(f,p),f['model'])
        values.append(np.linalg.svd(jac,compute_uv=False))
    assert values[1][-1]>2*values[0][-1]
    assert values[1][0]/values[1][-1]<.5*values[0][0]/values[0][-1]


def test_refinement_reduces_known_parameter_navigation_error(kernels):
    errors=[]
    for factor in (1,2,4):
        f=controls.fixture('sphere_rotating',factor)
        p=original.problem(f,*kernels)
        errors.append(original.position_error(f,p.predict(original.truth_point(f,p),f['model'])))
    assert errors[1]<.35*errors[0]
    assert errors[2]<.35*errors[1]


def test_invalid_resolution_and_geometry_are_rejected():
    for factor in (0,3,True):
        with pytest.raises(ValueError): controls.fixture('sphere_rotating',factor)
    with pytest.raises(ValueError): controls.fixture('sphere_rotating',1,'unknown')
