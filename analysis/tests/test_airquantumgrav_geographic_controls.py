# SPDX-License-Identifier: AGPL-3.0-or-later
"""Independent generated geometry; numerical checks wait for a free allocation."""
import ast
import importlib
from pathlib import Path

import pytest


def library():return importlib.import_module('lll.airquantumgrav_truth')


def test_generator_import_contract_keeps_navigation_code_separate():
    module=library();tree=ast.parse(Path(module.__file__).read_text())
    imports=[node for node in ast.walk(tree) if isinstance(node,(ast.Import,ast.ImportFrom))]
    targets=[node.module or '' for node in imports if isinstance(node,ast.ImportFrom)]
    targets += [a.name for node in imports if isinstance(node,ast.Import) for a in node.names]
    assert not any(n.startswith('lll') for n in targets)
    assert callable(module.truth)


@pytest.mark.parametrize('model',['sphere_rotating','sphere_still','flat_still'])
@pytest.mark.parametrize('latitude',[-55.,55.])
def test_stationary_limit_preserves_signed_background_and_specific_force(model,latitude):
    module=library()
    import numpy as np
    result=module.truth(model,[0.,1.],latitude_deg=latitude,pattern='stationary',removal=0.)
    field=7.292115e-5*np.array([np.cos(np.radians(latitude)),0.,-np.sin(np.radians(latitude))])
    expected=result['attitude_body_to_local'][0].T@field if model=='sphere_rotating' else np.zeros(3)
    np.testing.assert_allclose(result['angular_rate_rads'],np.tile(expected,(2,1)),atol=1e-15,rtol=0.)
    np.testing.assert_allclose(result['specific_force_mps2'],np.tile([0.,0.,-9.81],(2,1)),atol=1e-13,rtol=0.)
    np.testing.assert_allclose(result['velocity_world_mps'],0.,atol=1e-15)


@pytest.mark.parametrize('model',['sphere_rotating','sphere_still','flat_still'])
@pytest.mark.parametrize('pattern',['slow','fast'])
def test_analytic_derivatives_match_independent_five_point_samples(model,pattern):
    module=library()
    import numpy as np
    times=np.array([0.,7.,31.,143.,599.]);base=module.truth(model,times,latitude_deg=-55.,pattern=pattern,removal=0.)
    def at(offset):return module.truth(model,times+offset,latitude_deg=-55.,pattern=pattern,removal=0.)
    for h in (.5,.25):
        a,b,c,d=(at(k*h)['position_world_m'] for k in (-2,-1,1,2))
        velocity=(a-8*b+8*c-d)/(12*h)
        acceleration=(-a+16*b-30*base['position_world_m']+16*c-d)/(12*h*h)
        np.testing.assert_allclose(velocity,base['velocity_world_mps'],atol=1e-5,rtol=0.)
        np.testing.assert_allclose(acceleration,base['acceleration_world_mps2'],atol=1e-5,rtol=0.)
    for h in (.01,.005):
        a,b,c,d=(at(k*h)['body_axes_world'] for k in (-2,-1,1,2))
        derivative=(a-8*b+8*c-d)/(12*h)
        np.testing.assert_allclose(derivative,base['body_axes_derivative_per_s'],atol=1e-8,rtol=0.)
    axes=base['body_axes_world']
    np.testing.assert_allclose(axes.swapaxes(1,2)@axes,np.tile(np.eye(3),(len(times),1,1)),atol=1e-14,rtol=0.)
    np.testing.assert_allclose(np.linalg.det(axes),1.,atol=1e-14,rtol=0.)


@pytest.mark.parametrize('model',['sphere_rotating','sphere_still','flat_still'])
def test_common_removal_changes_only_the_logged_angular_channels(model):
    module=library()
    import numpy as np
    kwargs=dict(latitude_deg=55.,pattern='fast')
    raw=module.truth(model,[0.,7.],removal=0.,**kwargs);removed=module.truth(model,[0.,7.],removal=.35,**kwargs)
    phi=raw['coordinates'][:,0];standard=7.292115e-5*np.column_stack((np.cos(phi),np.zeros(2),-np.sin(phi)))
    expected=.35*np.einsum('nji,nj->ni',raw['attitude_body_to_local'],standard)
    np.testing.assert_allclose(raw['angular_rate_rads']-removed['angular_rate_rads'],expected,atol=1e-15,rtol=0.)
    assert np.array_equal(raw['specific_force_mps2'],removed['specific_force_mps2'])
