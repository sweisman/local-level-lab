# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest
from test_ilvis0_prediction import prediction


@pytest.fixture(scope='module')
def forecast_kernels(tmp_path_factory):
    from lll.ilvis0_shape import load_tangent
    from lll.ilvis0_exploratory import load_kernel
    directory=tmp_path_factory.mktemp('forecast-kernels')
    return load_kernel(directory)[0],load_tangent(directory)[0]


def forecast_fixture(kernels,profile,clock):
    from lll.ilvis0_shape import TangentProblem,instrument_limits
    from lll.ilvis0_estimator import Bounds
    n=80;dt=np.full(n,.005)
    if clock=='header_elapsed':dt[::2]=.0049;dt[1::2]=.0051
    theta=np.tile([1e-5,-2e-5,3e-6],(n,1));dv=np.c_[np.zeros(n),np.zeros(n),-9.81*dt]
    times=np.linspace(.02,.37,9);gps=np.tile([-.8,1.,10000.],(len(times),1))
    initial=dict(latitude_rad=-.8,longitude_rad=1.,height_m=10000.,velocity_ned_mps=np.array([220.,-30.,.1]),
        attitude_body_to_ned=np.eye(3));limits=instrument_limits(1.);limits['time_offset']=.001
    common=dict(initial=initial,bounds=Bounds(limits),kernel=kernels[0],tangent_kernel=kernels[1],
        fit_earth_removal=profile,clock_hypothesis=clock,processing_hypothesis='unsubtracted_increment_hypothesis',
        maximum_interval_s=.0075,gravity_mps2=9.81,disc_radius_m=6371000.)
    cut=prediction().split(times)['training_epochs'];count=np.searchsorted(np.cumsum(dt),times[cut-1]+.001)+1
    train=TangentProblem(theta[:count],dv[:count],dt[:count],times[:cut],gps[:cut],np.eye(3*cut),**common)
    whole=TangentProblem(theta,dv,dt,times,gps,np.eye(3*len(times)),**common)
    return train,whole,theta,dv,dt,times


@pytest.mark.parametrize('model',['sphere_rotating','sphere_still','flat_still'])
@pytest.mark.parametrize('profile',[False,True])
@pytest.mark.parametrize('clock',['header_elapsed','nominal_200Hz'])
def test_observation_free_forecast_matches_native_values_and_all_active_columns(forecast_kernels,model,profile,clock):
    from lll.ilvis0_forecast import native_forecast
    train,whole,theta,dv,dt,times=forecast_fixture(forecast_kernels,profile,clock)
    point=np.full(len(train.bounds.active),.03);charges=[]
    expected,jac,counter=whole.prediction_tangent(point,model)
    result=native_forecast(train,point,model,theta=theta,dv=dv,dt=dt,times=times,
        maximum_interval_s=.0075,reserve=lambda **v:charges.append(v))
    np.testing.assert_array_equal(result['coordinates'],expected)
    np.testing.assert_array_equal(result['jacobian'],jac)
    assert result['boundary_counter']==counter and result['active_parameters']==list(train.bounds.active)
    assert charges==[dict(native_calls=1,packet_visits=len(dt)*len(times))]
    assert result['prediction_receiver_positions_used'] is False and not result['confidence_calibrated']
    whole.gps=np.full_like(whole.gps,999.)  # No later receiver array is supplied to the forecast API.
    again=native_forecast(train,point,model,theta=theta,dv=dv,dt=dt,times=times,
        maximum_interval_s=.0075,reserve=lambda **v:None)
    np.testing.assert_array_equal(again['coordinates'],expected)


@pytest.mark.parametrize('change',['past_gyro','past_force','past_clock','queries','gap','point','unsupported_clock'])
def test_forecast_rejects_changed_training_prefix_before_charging(forecast_kernels,change):
    from lll.ilvis0_forecast import native_forecast
    train,_,theta,dv,dt,times=forecast_fixture(forecast_kernels,False,'nominal_200Hz')
    point=np.zeros(len(train.bounds.active));charges=[]
    if change=='past_gyro':theta[0,0]+=.01
    elif change=='past_force':dv[0,0]=-.0
    elif change=='past_clock':dt[0]+=.0001
    elif change=='queries':times[0]+=.001
    elif change=='gap':dt[-1]=.01
    elif change=='point':point[0]=2.
    else:train.clock_hypothesis='unknown'
    with pytest.raises(ValueError):native_forecast(train,point,'sphere_rotating',theta=theta,dv=dv,dt=dt,times=times,
        maximum_interval_s=.0075,reserve=lambda **v:charges.append(v))
    assert charges==[]
