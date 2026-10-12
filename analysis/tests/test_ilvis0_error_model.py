# SPDX-License-Identifier: AGPL-3.0-or-later
"""Independent answers catch missing cross blocks, split reanchoring and unit errors."""
import numpy as np
import pytest


def api():
    from lll import ilvis0_error_model as model
    return model


def test_white_error_is_independent_per_epoch_with_signed_axis_covariance():
    m=api();w=np.array([[4.,-1.,0.],[-1.,2.,0.],[0.,0.,1.]])
    c=m.covariance([3.,7.],m.Spec(w))
    np.testing.assert_allclose(c[:3,:3],w)
    np.testing.assert_allclose(c[3:,3:],w)
    np.testing.assert_array_equal(c[:3,3:],np.zeros((3,3)))


def test_irregular_ou_times_and_ordered_two_components():
    m=api();t=[0.,np.log(2),3*np.log(2)]
    c=m.covariance(t,m.Spec(np.eye(3),components=((1.,2*np.eye(3)),(2.,np.eye(3)))))
    assert c[0,0]==pytest.approx(4.)
    assert c[0,3]==pytest.approx(1.+np.sqrt(.5))
    assert c[0,6]==pytest.approx(.25+np.sqrt(.125))
    assert c[3,6]==pytest.approx(.5+.5)


def test_drift_keeps_full_record_origin_when_building_a_prediction_subset():
    m=api();s=m.Spec(np.eye(3),offset=2*np.eye(3),drift=4*np.eye(3),
        drift_origin_s=100.,drift_span_s=10.)
    full=m.covariance([100.,105.,110.],s);tail=m.covariance([105.,110.],s)
    np.testing.assert_allclose(tail,full[3:,3:])
    assert tail[0,0]==pytest.approx(4.)
    assert tail[0,3]==pytest.approx(4.)
    assert tail[3,3]==pytest.approx(7.)


def test_epoch_transform_changes_cross_epoch_blocks_and_preserves_cost():
    m=api();s=m.Spec(np.diag([1.,2.,3.]),offset=np.array([[2.,.5,0.],[.5,1.,0.],[0.,0.,1.]]))
    r=np.array([1.,2.,-1.,3.,-2.,4.]);base=m.covariance([0.,2.],s)
    transforms=np.array([np.diag([1e-7,2e-7,1.]),[[0.,1e-7,0.],[-2e-7,0.,0.],[0.,0.,1.]]])
    changed=m.covariance([0.,2.],s,transforms=transforms)
    assert changed[0,3]==pytest.approx(.5e-14)
    assert changed[0,4]==pytest.approx(-4e-14)
    converted=np.concatenate([transforms[i]@r[3*i:3*i+3] for i in range(2)])
    assert m.whiten(converted,changed)['quadratic']==pytest.approx(m.whiten(r,base)['quadratic'])
    expected_shift=2*np.sum(np.linalg.slogdet(transforms)[1])
    assert m.whiten(converted,changed)['log_determinant']-m.whiten(r,base)['log_determinant']==pytest.approx(expected_shift)


def test_whitening_matches_a_hand_cholesky_and_density_includes_determinant():
    m=api();c=np.array([[4.,2.],[2.,10.]])
    out=m.whiten([2.,4.],c)
    np.testing.assert_allclose(out['innovations'],[1.,1.])
    assert out['quadratic']==pytest.approx(2.)
    assert out['log_determinant']==pytest.approx(np.log(36.))
    assert out['negative_log_likelihood']==pytest.approx(1+np.log(6.)+np.log(2*np.pi))


def test_conditioning_uses_training_residuals_and_cross_boundary_dependence():
    m=api();out=m.condition(np.array([[4.,2.],[2.,9.]]),[0],[1],[2.])
    np.testing.assert_allclose(out['mean'],[1.])
    np.testing.assert_allclose(out['covariance'],[[8.]])
    independent=m.condition(np.diag([4.,9.]),[0],[1],[2.])
    np.testing.assert_allclose(independent['mean'],[0.])
    np.testing.assert_allclose(independent['covariance'],[[9.]])


def test_exact_gaussian_cubature_recovers_identity_whitening_and_prediction_covariance():
    # Independent generating factor, not the covariance builder/whitener.
    m=api();factor=np.array([[2.,0.,0.],[1.,3.,0.],[.5,-1.,2.]])
    c=np.array([[4.,2.,1.],[2.,10.,-2.5],[1.,-2.5,5.25]])
    points=np.sqrt(3)*np.concatenate((factor.T,-factor.T))
    innovations=np.array([m.whiten(p,c)['innovations'] for p in points])
    np.testing.assert_allclose(innovations.T@innovations/6,np.eye(3),atol=1e-14)
    errors=[]
    for point in points:
        out=m.condition(c,[0],[1,2],point[:1])
        errors.append(point[1:]-out['mean'])
    np.testing.assert_allclose(np.array(errors).T@np.array(errors)/6,[[9.,-3.],[-3.,5.]],atol=1e-14)
    np.testing.assert_allclose(out['covariance'],[[9.,-3.],[-3.,5.]])


def test_nearly_singular_positive_covariance_is_not_repaired_or_overwhitened():
    m=api();eps=1e-10;c=np.array([[1.,1.],[1.,1.+eps]])
    original=c.copy();out=m.whiten([1.,1.],c)
    assert out['quadratic']==pytest.approx(1.,abs=1e-8)
    np.testing.assert_array_equal(c,original)
    assert out['log_determinant']==pytest.approx(np.log(eps),abs=1e-6)


@pytest.mark.parametrize('case',['negative_white','singular_white','asymmetric','nonfinite',
    'negative_component','zero_tau','unordered_tau','third_component','negative_span'])
def test_invalid_specifications_fail_before_covariance_is_used(case):
    m=api();kw={};white=np.eye(3)
    if case=='negative_white':white[0,0]=-1.
    if case=='singular_white':white[0,0]=0.
    if case=='asymmetric':white[0,1]=1.
    if case=='nonfinite':white[0,0]=np.nan
    if case=='negative_component':kw['offset']=-np.eye(3)
    if case=='zero_tau':kw['components']=((0.,np.eye(3)),)
    if case=='unordered_tau':kw['components']=((2.,np.eye(3)),(1.,np.eye(3)))
    if case=='third_component':kw['components']=tuple((i,np.eye(3)) for i in (1.,2.,3.))
    if case=='negative_span':kw['drift_span_s']=-1.
    with pytest.raises(ValueError):m.Spec(white,**kw)


@pytest.mark.parametrize('times',[[0.,0.],[2.,1.],[0.,np.nan],[]])
def test_invalid_times_are_not_repaired(times):
    m=api()
    with pytest.raises(ValueError):m.covariance(times,m.Spec(np.eye(3)))


@pytest.mark.parametrize('case',['singular','indefinite','asymmetric','nonfinite','residual_shape',
    'overlap','duplicate_index','bad_index','fractional_index','empty_train','nonfinite_residual'])
def test_invalid_whitening_and_prediction_inputs_are_rejected(case):
    m=api();c=np.eye(2);r=np.ones(2)
    if case=='singular':c[:]=1.
    if case=='indefinite':c[0,0]=-1.
    if case=='asymmetric':c[0,1]=.1
    if case=='nonfinite':c[0,0]=np.inf
    if case=='residual_shape':r=r[:1]
    if case=='nonfinite_residual':r[0]=np.nan
    if case in ('overlap','duplicate_index','bad_index','fractional_index','empty_train'):
        train,test={'overlap':([0],[0]),'duplicate_index':([0,0],[1]),
            'bad_index':([0],[2]),'fractional_index':([.5],[1]),'empty_train':([],[1])}[case]
        with pytest.raises(ValueError):m.condition(c,train,test,np.ones(len(train)))
    else:
        with pytest.raises(ValueError):m.whiten(r,c)


def test_singular_axis_transform_is_rejected():
    m=api()
    with pytest.raises(ValueError):m.covariance([0.],m.Spec(np.eye(3)),transforms=np.zeros((1,3,3)))


def test_shared_spec_is_not_changed_by_original_arrays_or_consumer_mutation():
    m=api();white=np.eye(3);offset=np.eye(3);s=m.Spec(white,offset=offset)
    white[0,0]=100.;offset[0,0]=100.
    assert m.covariance([0.],s)[0,0]==pytest.approx(2.)
    with pytest.raises(ValueError):s.white[0,0]=10.


def test_block_prediction_transforms_the_mean_and_full_conditional_covariance():
    m=api();s=m.Spec(np.eye(3),offset=np.eye(3))
    transforms=np.array([np.diag([2.,1.,1.]),np.diag([3.,4.,5.])])
    c=m.covariance([0.,1.],s,transforms=transforms)
    out=m.condition(c,[0,1,2],[3,4,5],[2.,2.,3.])
    np.testing.assert_allclose(out['mean'],[1.5,4.,7.5])
    np.testing.assert_allclose(out['covariance'],np.diag([13.5,24.,37.5]))
