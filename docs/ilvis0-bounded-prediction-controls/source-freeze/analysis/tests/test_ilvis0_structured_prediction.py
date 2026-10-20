# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest
from scipy.linalg import solve_triangular

from lll.ilvis0_error_model import Spec,covariance,factor
from lll.ilvis0_structured_covariance import Innovations
from lll.ilvis0_structured_prediction import Forecast


def fixture(q=2,axes=(0,1,2),transformed=False):
    train=np.array([0.,.2,1.,4.,5.,8.]);future=np.array([8.1,11.,20.])
    a=np.array([[1.,.2,.1],[.2,2.,-.2],[.1,-.2,1.5]])
    spec=Spec(white=.1*a,components=tuple([(2.,a),(90.,.3*a)][:q]),
        offset=.2*a,drift=.5*a,drift_origin_s=-10.,drift_span_s=50.)
    transform=None
    if transformed:
        transform=np.array([np.diag([1e-7*(1.+i/20.),2e-7,1.]) for i in range(9)])
    operator=Innovations(train,spec,axes=axes,transforms=None if transform is None else transform[:6])
    prediction=Forecast(operator,future,transforms=None if transform is None else transform[6:])
    full=covariance(np.concatenate((train,future)),spec,transforms=transform)
    selected=[3*i+axis for i in range(9) for axis in axes];full=full[np.ix_(selected,selected)]
    return operator,prediction,full


@pytest.mark.parametrize('q',[0,1,2])
@pytest.mark.parametrize('axes',[(0,1,2),(2,),(1,0)])
@pytest.mark.parametrize('transformed',[False,True])
def test_conditional_forecast_and_error_response_match_dense(q,axes,transformed):
    operator,prediction,full=fixture(q,axes,transformed)
    cut=len(operator.times)*len(axes);lower=factor(full[:cut,:cut])
    cross=solve_triangular(lower,full[:cut,cut:],lower=True)
    values=np.sin(np.arange(cut*4).reshape(cut,4)*.1)
    if transformed:
        values*=np.tile(np.array([1e-7,2e-7,1.])[list(axes)],len(operator.times))[:,None]
    expected=cross.T@solve_triangular(lower,values,lower=True)
    conditional=full[cut:,cut:]-cross.T@cross
    np.testing.assert_allclose(prediction.mean(values),expected,rtol=5e-11,atol=1e-12)
    np.testing.assert_allclose(prediction.variance,np.diag(conditional),rtol=5e-11,atol=1e-25)
    np.testing.assert_allclose(prediction.training_response_norm,np.linalg.norm(cross,axis=0),rtol=5e-11,atol=1e-25)
    np.testing.assert_allclose(prediction.mean(values[:,0]),expected[:,0],rtol=5e-11,atol=1e-12)


def test_white_only_errors_have_zero_training_response_and_unchanged_future_variance():
    spec=Spec(white=np.diag([1.,2.,3.]))
    prediction=Forecast(Innovations([0.,1.],spec),[2.,3.])
    np.testing.assert_array_equal(prediction.mean(np.ones(6)),np.zeros(6))
    np.testing.assert_array_equal(prediction.training_response_norm,np.zeros(6))
    np.testing.assert_array_equal(prediction.variance,[1.,2.,3.,1.,2.,3.])


def test_singular_latent_components_preserve_response_norm_without_eigenvalue_clipping():
    vector=np.array([1.,2.,-1.]);matrix=np.outer(vector,vector)
    spec=Spec(white=np.eye(3)*.1,components=((1e8,matrix),),offset=matrix)
    train=np.array([0.,.001,1.]);future=np.array([2.,10.])
    prediction=Forecast(Innovations(train,spec),future)
    full=covariance(np.concatenate((train,future)),spec)
    lower=factor(full[:9,:9]);cross=solve_triangular(lower,full[:9,9:],lower=True)
    np.testing.assert_allclose(prediction.training_response_norm,np.linalg.norm(cross,axis=0),atol=3e-12)


@pytest.mark.parametrize('future',[[8.],[7.,10.],[10.,10.],[],[np.inf]])
def test_future_epochs_cannot_overlap_or_reset_training(future):
    operator,_,_=fixture()
    with pytest.raises(ValueError):Forecast(operator,future)


def test_future_coordinate_transforms_must_be_explicit_when_training_used_them():
    operator,_,_=fixture(transformed=True)
    with pytest.raises(ValueError):Forecast(operator,[9.,10.])


def test_forecast_accepts_no_future_observations_and_rejects_bad_training_shape():
    operator,prediction,_=fixture()
    with pytest.raises(TypeError):Forecast(operator,[9.,10.],future_values=np.ones(6))
    with pytest.raises(ValueError):prediction.mean(np.ones(17))
    with pytest.raises(ValueError):prediction.mean(np.full(18,np.nan))
