# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest
from scipy.linalg import solve_triangular

from lll.ilvis0_error_model import Spec, covariance, factor
from lll.ilvis0_structured_covariance import Innovations


def fixture(components=2, transforms=False, axes=(0,1,2)):
    times=np.array([10.,10.2,11.7,14.,15.3,21.])
    a=np.array([[.8,.1,0.],[.1,1.2,.2],[0.,.2,2.]])
    b=np.array([[.4,-.1,.1],[-.1,.6,0.],[.1,0.,.5]])
    spec=Spec(white=.1*a, components=tuple([(2.,a),(70.,b)][:components]),
        offset=.3*b,drift=.2*a,drift_origin_s=0.,drift_span_s=100.)
    transform=None
    if transforms:
        transform=np.array([np.array([[1e-7,0.,0.],[.1e-7,2e-7,0.],[0.,.1,1.]])
            @np.diag([1.+i/10.,1.,1.]) for i in range(len(times))])
    dense=covariance(times,spec,transform)
    indices=np.array([3*i+axis for i in range(len(times)) for axis in axes])
    return Innovations(times,spec,transforms=transform,axes=axes),dense[np.ix_(indices,indices)]


@pytest.mark.parametrize('components', [0,1,2])
@pytest.mark.parametrize('transforms', [False,True])
def test_innovations_and_determinant_match_dense_reference(components,transforms):
    operator,dense=fixture(components,transforms)
    values=np.sin(np.arange(len(dense))+.2)
    if transforms:
        values=np.einsum('nij,nj->ni',operator.transforms,values.reshape(-1,3)).ravel()
    expected=solve_triangular(factor(dense),values,lower=True)
    actual=operator.whiten(values)
    np.testing.assert_allclose(actual,expected,rtol=3e-11,atol=3e-8 if transforms else 3e-12)
    assert operator.log_determinant == pytest.approx(np.linalg.slogdet(dense)[1],abs=3e-11)
    np.testing.assert_allclose(operator.unwhiten(actual),values,rtol=1e-12,atol=1e-12)


def test_extreme_cross_unit_round_trip_has_dense_reference_backward_accuracy():
    operator,dense=fixture(transforms=True)
    values=np.sin(np.arange(len(dense))+.2)  # Intentionally millions of angle sigmas.
    lower=factor(dense); whitened=operator.whiten(values)
    reconstructed=operator.unwhiten(whitened)
    scale=np.linalg.norm(lower,ord=2)*np.linalg.norm(whitened)+np.linalg.norm(values)
    assert np.linalg.norm(reconstructed-values)/scale < 4*np.finfo(float).eps
    expected=lower@solve_triangular(lower,values,lower=True)
    assert np.linalg.norm(expected-values)/scale < 4*np.finfo(float).eps


def test_every_jacobian_column_uses_same_linear_operator():
    operator,dense=fixture()
    values=np.sin(np.arange(len(dense)*27).reshape(len(dense),27)/17.)
    actual=operator.whiten(values)
    np.testing.assert_allclose(actual,solve_triangular(factor(dense),values,lower=True),atol=3e-12)
    np.testing.assert_allclose(operator.unwhiten(actual),values,atol=3e-12)


@pytest.mark.parametrize('axes', [(0,1),(2,),(2,0,1)])
def test_coordinate_subset_projection_matches_dense_marginal(axes):
    full,full_dense=fixture(transforms=True)
    target,marginal=fixture(transforms=True,axes=axes)
    values=np.sin(np.arange(len(full_dense)))
    source_whitened=full.whiten(values)
    result=full.project_to(source_whitened,target)
    selected=values.reshape(-1,3)[:,axes].ravel()
    np.testing.assert_allclose(result,solve_triangular(factor(marginal),selected,lower=True),rtol=1e-11,atol=1e-7)


def test_block_continuation_matches_whole_record_in_both_directions():
    operator,dense=fixture(); values=np.cos(np.arange(len(dense)))
    one,state=operator.apply_block(values[:6],first_epoch=0)
    two,state=operator.apply_block(values[6:12],first_epoch=2,state=state)
    three,state=operator.apply_block(values[12:],first_epoch=4,state=state)
    joined=np.concatenate([one,two,three])
    np.testing.assert_allclose(joined,operator.whiten(values),atol=1e-13)
    first,inverse_state=operator.apply_block(joined[:9],first_epoch=0,inverse=True)
    last,_=operator.apply_block(joined[9:],first_epoch=3,state=inverse_state,inverse=True)
    np.testing.assert_allclose(np.concatenate([first,last]),values,atol=1e-12)


def test_later_block_cannot_reset_or_change_direction_columns_or_configuration():
    operator,_=fixture(); _,state=operator.apply_block(np.zeros(6),first_epoch=0)
    with pytest.raises(ValueError): operator.apply_block(np.zeros(3),first_epoch=2)
    with pytest.raises(ValueError): operator.apply_block(np.zeros(3),first_epoch=3,state=state)
    with pytest.raises(ValueError): operator.apply_block(np.zeros((3,2)),first_epoch=2,state=state)
    with pytest.raises(ValueError): operator.apply_block(np.zeros(3),first_epoch=2,state=state,inverse=True)
    other,_=fixture(components=1)
    with pytest.raises(ValueError): other.apply_block(np.zeros(3),first_epoch=2,state=state)


def test_rank_deficient_latent_covariances_do_not_require_clipping():
    times=np.array([0.,.00001,1.,2.])
    vector=np.array([1.,2.,-1.]); component=np.outer(vector,vector)
    spec=Spec(white=np.eye(3)*.01,components=((1e8,component),),offset=component,drift=np.zeros((3,3)))
    operator=Innovations(times,spec)
    dense=covariance(times,spec)
    np.testing.assert_allclose(operator.whiten(np.ones(12)),solve_triangular(factor(dense),np.ones(12),lower=True),atol=2e-12)


@pytest.mark.parametrize('axes', [(),(0,0),(3,),(True,)])
def test_invalid_retained_axes_rejected(axes):
    with pytest.raises(ValueError): fixture(axes=axes)


def test_invalid_values_and_timestamps_rejected_without_repair():
    operator,_=fixture()
    for values in [np.zeros(17),np.full(18,np.nan)]:
        with pytest.raises(ValueError): operator.whiten(values)
    with pytest.raises(ValueError): Innovations([0.,0.],Spec(white=np.eye(3)))


def test_cache_storage_scales_linearly_without_a_whole_record_matrix():
    spec=Spec(white=np.eye(3),components=((10.,np.eye(3)),))
    small=Innovations(np.arange(10.),spec); large=Innovations(np.arange(20.),spec)
    assert large.storage_bytes == 2*small.storage_bytes
    assert large.state_dimension == 9
