# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest
from test_native_structured_training import training_kernels,native_training_case

DEFINITION=dict(additional_sources=['analysis/tests/test_native_prediction_benchmark.py',
    'analysis/lll/generated_noise_benchmark.py','analysis/lll/prediction_error_benchmark.py',
    'analysis/tests/test_generated_noise_benchmark.py','analysis/tests/test_prediction_error_benchmark.py',
    'docs/noisy-prediction-benchmark/PLAN.md','docs/noisy-prediction-benchmark/CONSTRUCTION_PLAN.md'],
    allowances={'builds':dict(builds=2),
        'increment:0:0:1':dict(native_calls=700,packet_steps=2000,packet_query_visits=10000,
            generated_samples=610,constructed_intervals=600),
        'point:0:0:1':dict(native_calls=700,packet_steps=2000,packet_query_visits=10000,
            generated_samples=610,constructed_intervals=600)},maximum_wall_s=180.)


@pytest.mark.parametrize('training_kernels',[DEFINITION],indirect=True)
@pytest.mark.parametrize('law',['increment','point'])
@pytest.mark.parametrize('model',[0])
@pytest.mark.parametrize('profile',[False])
@pytest.mark.parametrize('height',[True])
def test_native_known_calibration_noise_benchmark(native_training_case,monkeypatch,law,model,profile,height):
    import numpy as np
    from lll.generated_noise_benchmark import material,build_operator
    from lll.prediction_error_benchmark import summarize
    from lll.ilvis0_shape import TangentProblem
    from lll.ilvis0_estimator import Bounds
    from lll.airquantumgrav_training_controls import parameter_limits
    from lll.ilvis0_wide_tangent import load,evaluate
    from lll.receiver_noise_states import ReceiverAugmentation
    k=native_training_case;construction=[];cutoffs=[]
    def construct_charge(**work):
        k['reserve'](**work);construction.append(work)
    data=material(duration_s=2.,queries=9,query_start_s=.1,query_step_s=.2,reserve=construct_charge)
    assert sum(v.get('generated_samples',0) for v in construction)==610
    assert sum(v.get('constructed_intervals',0) for v in construction)==600
    original=ReceiverAugmentation.__init__
    def receiver(self,*args,**kwargs):
        cutoffs.append(kwargs.get('receiver_epochs'));original(self,*args,**kwargs)
    monkeypatch.setattr(ReceiverAugmentation,'__init__',receiver)
    op,mean,descriptor=build_operator(data,law=law,kernel=k['kernel'],reserve=k['reserve'])
    assert cutoffs==[6] and descriptor['prediction_target']=='physical_position'
    assert descriptor['oracle_nominal_future_geometry_used'] and descriptor['calibration_is_known']
    init=data['initial'];initial=dict(zip(('latitude_rad','longitude_rad','height_m'),init['coordinates']))
    initial.update(velocity_ned_mps=init['velocity'],attitude_body_to_ned=init['rotation'])
    limits=parameter_limits()
    reference,_=load(k['directory'],expected_source_sha256=k['hashes']['analysis/lll/ilvis0_tangent.cpp'],
        gravity_anchor_height_m=data['anchor_height_m'])
    problem=TangentProblem(data['raw_theta'],data['raw_dv'],data['dt'],data['times'],
        np.zeros((9,3)),np.eye(27),initial,Bounds(limits),tangent_kernel=reference,fit_earth_removal=False,
        clock_hypothesis='header_elapsed',processing_hypothesis='unsubtracted_increment_hypothesis',
        maximum_interval_s=.007,gravity_mps2=data['gravity_mps2'],disc_radius_m=data['radius_m'])
    point=np.array([data['sensor_correction'].get(name,0.)/limits[name] for name in problem.bounds.active])
    k['reserve'](native_calls=1,packet_steps=600,packet_query_visits=5400)
    expected=evaluate(problem,point,'sphere_rotating',kernel=reference)[0]
    mean_difference=(mean-expected)*data['nominal_metric']
    np.testing.assert_allclose(mean_difference,0.,rtol=0,atol=1e-5)
    truth_difference=(mean-data['nominal_receiver'])*data['nominal_metric']
    assert float(np.max(np.linalg.norm(truth_difference,axis=1)))<.01
    summary=summarize(op,training_epochs=6,nominal_position_scales=data['nominal_metric'][6:],
        accuracy_limits=dict(horizontal_rms_m=10.,vertical_rms_m=30.))
    l=op.unwhiten(np.eye(27));future=l[18:,18:]
    variance=np.einsum('ij,ij->i',future,future).reshape(3,3)*data['nominal_metric'][6:]**2
    np.testing.assert_allclose(summary['marginal_variance_neu_m2'],variance,rtol=1e-10,atol=1e-16)
    assert not summary['confidence_calibrated'] and not summary['is_expected_realized_rms']
    k['results'].append(dict(law=law,model='sphere_rotating',profile=False,height=True,
        packets=600,training_epochs=6,prediction_epochs=3,oracle_calibration=True,
        mean_reference_maximum_error_m=float(np.max(abs(mean_difference))),
        mean_nominal_maximum_3d_error_m=float(np.max(np.linalg.norm(truth_difference,axis=1))),
        covariance_state_dimension=op.state_dimension,known_calibration_benchmark=summary))
