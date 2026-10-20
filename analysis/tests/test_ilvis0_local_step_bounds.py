# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest

from lll import ilvis0_local_step_bounds as bounds


def value(x,change=0.,remainder=0.):return bounds.Value(x,change,remainder)


def inputs(model='sphere_rotating',removal=0.):
    return dict(model=model,attitude=bounds.Matrix(np.eye(3),0.,0.,'rotation'),
        velocity=value([200.,30.,-.2]),theta=value([3e-5,-2e-5,1e-5]),dv=value([0.,0.,-.04905]),
        latitude=value(np.deg2rad(-65.)),transport=value([1e-5,-3e-5,2e-5]),removal=value(removal),
        gravity=value(9.81),dt=.005)


@pytest.mark.parametrize('model',['sphere_rotating','sphere_still','flat_still'])
@pytest.mark.parametrize('removal',[0.,.5])
def test_zero_uncertainty_matches_independent_linear_algebra(model,removal):
    from scipy.linalg import expm
    args=inputs(model,removal);result=bounds.local_bound(**args);dt=args['dt']
    phi=args['latitude'].center;standard=bounds.OMEGA*np.array([np.cos(phi),0.,-np.sin(phi)])
    earth=standard if model=='sphere_rotating' else np.zeros(3);transport=args['transport'].center
    win=earth+transport-removal*standard;a=(2*earth+transport)*dt/2
    def skew(v):
        x,y,z=v;return np.array([[0.,-z,y],[z,0.,-x],[-y,x,0.]])
    middle=expm(skew(-win*dt/2))@expm(skew(args['theta'].center/2))
    expected=np.linalg.solve(np.eye(3)+skew(a),(np.eye(3)-skew(a))@args['velocity'].center
        +middle@args['dv'].center+np.array([0.,0.,9.81*dt]))
    np.testing.assert_allclose(result['velocity'].center,expected,atol=1e-12,rtol=0.)
    assert result['velocity'].remainder==result['attitude'].remainder==0.
    assert result['native_full_map_covered'] is False


def test_removed_rate_does_not_change_coriolis_argument():
    a=bounds.local_bound(**inputs('flat_still',0.));b=bounds.local_bound(**inputs('flat_still',1.))
    np.testing.assert_array_equal(a['context']['coriolis_argument'].center,b['context']['coriolis_argument'].center)
    assert not np.array_equal(a['context']['win'].center,b['context']['win'].center)


def test_cayley_and_inverse_global_bounds_at_large_arguments():
    from scipy.linalg import expm_frechet
    nominal=np.array([2.,-1.,3.]);delta=np.array([.3,-.2,.4]);a=value(nominal,np.linalg.norm(delta))
    def skew(v):
        x,y,z=v;return np.array([[0.,-z,y],[z,0.,-x],[-y,x,0.]])
    b0=np.linalg.solve(np.eye(3)+skew(nominal),np.eye(3));b=np.linalg.solve(np.eye(3)+skew(nominal+delta),np.eye(3))
    db=-b0@skew(delta)@b0
    for result,scale in ((bounds.inverse_skew(a),1.),(bounds.cayley(a),2.)):
        error=np.linalg.norm(scale*(b-b0-db),ord=2)
        assert error<=result.remainder
        assert np.linalg.norm(scale*(b-b0),ord=2)<=result.change


def test_scalar_vector_product_keeps_joint_change_term():
    a=value(.5,.5);b=value([3.,4.,0.],.2,.01)
    result=bounds.scalar_product(a,b)
    assert result.remainder>=.5*.01+.5*.2


def test_invalid_physics_and_operator_claims_are_rejected():
    with pytest.raises(ValueError):bounds.Matrix(np.eye(3)*2.,0.,0.,'rotation')
    for key,replacement in [('removal',value(.5,.6)),('gravity',value(.1,.2)),('dt',0.),('latitude',value(1.5,.1))]:
        args=inputs();args[key]=replacement
        with pytest.raises(ValueError):bounds.local_bound(**args)


def test_matrix_and_vector_changes_propagate_without_independence():
    rotation=bounds.exponential(value([.1,-.2,.3],.2,.01))
    result=bounds.matrix_vector(rotation,value([1.,2.,3.],.5,.02))
    assert result.remainder>=rotation.remainder*np.sqrt(14)+.02+rotation.change*.5
