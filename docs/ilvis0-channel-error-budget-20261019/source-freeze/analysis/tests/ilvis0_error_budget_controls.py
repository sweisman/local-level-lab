# SPDX-License-Identifier: AGPL-3.0-or-later
"""Deterministic approximation stresses; no recorded-data or significance tests."""
import math

import numpy as np

from ilvis0_channel_reference import reference,BACKGROUND,GRAVITY,RADIUS,MODELS
from lll.ilvis0_receiver_derivatives import LocalPolynomial
from lll.ilvis0_nonlinear_response import local_response
from lll import ilvis0_receiver_force


def motion(time_s):
    result={}
    for names,base,slope,amplitude,period in (
        (('phi','p','pp'),.7,3e-5,2e-6,70.),
        (('longitude','l','ll'),.2,3e-5,3e-6,90.),
        (('height','h','hh'),1500.,0.,5.,55.)):
        frequency=2*math.pi/period;angle=frequency*time_s
        result.update(zip(names,(base+slope*time_s+amplitude*math.sin(angle),
            slope+amplitude*frequency*math.cos(angle),-amplitude*frequency**2*math.sin(angle))))
    return result


def receiver_covariance(times,noise_multiplier):
    times=np.asarray(times,float)
    correlation=.9*np.exp(-abs(times[:,None]-times[None,:])/60.)+.1*np.eye(len(times))
    axis=np.array([[1.,.2,.1],[.2,1.,.15],[.1,.15,1.]])
    scale=np.array([.3/(RADIUS+1500.),.3/((RADIUS+1500.)*math.cos(.7)),.7])*noise_multiplier
    return np.kron(correlation,axis*scale[:,None]*scale[None,:])


def approximation_screen(report,bias):
    scale=max(report['linear_sigma'],1e-15)
    spread=abs(report['cubature_sigma']-report['linear_sigma'])/scale
    shift=abs(report['mean_shift'])/scale;truncation=abs(bias)/scale
    linear=bool(report['relative_gradient_disagreement']<=.01 and spread<=.05 and shift<=.1)
    return dict(linear_screen_passed=linear,truncation_screen_passed=bool(truncation<=.25),
        screen_passed=bool(linear and truncation<=.25),relative_sigma_difference=spread,
        mean_shift_over_linear_sigma=shift,truncation_over_linear_sigma=truncation,
        scientific_eligible=False)


def trajectory_control(task):
    center=7.;times=np.arange(center-task['half_window_s'],center+task['half_window_s']+1.)
    observations=np.array([[motion(t)[k] for k in ('phi','longitude','height')] for t in times])
    covariance=receiver_covariance(times,task['noise_multiplier'])
    operator=LocalPolynomial(times,center,covariance,degree=task['degree'],maximum_gap_s=1.1)
    estimate=operator.apply(observations)
    mean=np.concatenate((estimate['position'],estimate['rate'],estimate['acceleration']))
    truth=reference(task['model'],motion(center),0.)
    exact_point=np.concatenate((truth['coordinates'],truth['rate'],truth['second']))
    calls=0;candidates={};agreement=None
    for model in MODELS:
        def magnitude(point):
            nonlocal calls
            calls+=1
            result=ilvis0_receiver_force.evaluate(point[:3],point[3:6],point[6:],model=model,
                background_rate_rads=BACKGROUND if model=='sphere_rotating' else 0.,
                gravity_mps2=GRAVITY,disc_radius_m=RADIUS)
            return float(np.linalg.norm(result['specific_force_ned_mps2']))
        exact=magnitude(exact_point)
        response=local_response(magnitude,mean,estimate['covariance'])
        if model==task['model']:agreement=abs(exact-float(np.linalg.norm(truth['force'])))
        bias=response['center']-exact
        candidates[model]=dict(response,exact_magnitude_mps2=exact,trajectory_bias_mps2=bias,
                               **approximation_screen(response,bias))
    return dict(task,candidates=candidates,passed=bool(agreement<=1e-9 and calls==168),
        true_model_reference_error_mps2=agreement,force_evaluations=calls,
        times_s=times.tolist(),sample_coordinates=observations.tolist(),joint_estimate=mean.tolist(),
        joint_covariance=estimate['covariance'].tolist(),derivative_policy=estimate['policy'],
        polynomial_residuals=estimate['coordinate_residuals'].tolist(),scientific_decision='abstain')


def rotation_control(angle_deg):
    angle=math.radians(angle_deg);dt=.005;times=(np.arange(200)+.5)*dt
    packet_scale=float(np.sinc(angle*dt/(2*math.pi)))
    increments=GRAVITY*dt*packet_scale*np.column_stack((np.sin(angle*times),np.zeros(200),np.cos(angle*times)))
    mean_magnitude=float(np.mean(np.linalg.norm(increments,axis=1)/dt))
    summed=float(np.linalg.norm(np.sum(increments,axis=0)))
    expected_packet=GRAVITY*packet_scale;expected_sum=GRAVITY*float(np.sinc(angle/(2*math.pi)))
    error=max(abs(mean_magnitude-expected_packet),abs(summed-expected_sum))
    return dict(angle_deg=angle_deg,mean_packet_magnitude_mps2=mean_magnitude,
        summed_vector_magnitude_mps2=summed,packet_integration_loss_mps2=GRAVITY-mean_magnitude,
        uncorrected_vector_average_loss_mps2=GRAVITY-summed,closed_form_error_mps2=error,
        constructed_increments=200,passed=bool(error<=1e-11),scientific_decision='abstain')


def noise_control(sigma):
    means={}
    for order in (5,9):
        nodes,weights=np.polynomial.hermite.hermgauss(order)
        x,y,z=np.meshgrid(nodes,nodes,nodes,indexing='ij')
        wx,wy,wz=np.meshgrid(weights,weights,weights,indexing='ij')
        norms=np.sqrt((math.sqrt(2)*sigma*x)**2+(math.sqrt(2)*sigma*y)**2
                      +(GRAVITY+math.sqrt(2)*sigma*z)**2)
        means[order]=float(np.sum(norms*wx*wy*wz)/math.pi**1.5)
    bias=means[9]-GRAVITY;difference=abs(means[5]-means[9])
    return dict(sigma_mps2=sigma,bias_order5_mps2=means[5]-GRAVITY,bias_order9_mps2=bias,
        small_noise_prediction_mps2=sigma**2/GRAVITY,quadrature_disagreement_mps2=difference,
        quadrature_evaluations=854,passed=bool(difference<=max(1e-11,.01*abs(bias))),
        scientific_decision='abstain')
