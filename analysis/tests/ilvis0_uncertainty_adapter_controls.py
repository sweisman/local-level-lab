# SPDX-License-Identifier: AGPL-3.0-or-later
"""Fixed six-case software matrix; independent increments, no fitting or NASA reads."""
import numpy as np

from lll import ilvis0_geographic_controls as geographic, ilvis0_latitude_controls as latitude
from lll import ilvis0_estimator as estimator, ilvis0_shape as shape, ilvis0_uncertainty_adapter as adapter


def full_problem(f,kernels):
    sigma=np.tile(.01/f['metric'],len(f['gps_times']))
    return shape.TangentProblem(f['theta'],f['dv'],f['dt'],f['gps_times'],f['gps'],
        np.diag(sigma**2),f['initial'],estimator.Bounds(shape.instrument_limits(1.)),
        fit_earth_removal=True,kernel=kernels[0],tangent_kernel=kernels[1],
        clock_hypothesis='header_elapsed',processing_hypothesis='unsubtracted_increment_hypothesis',
        maximum_interval_s=.0075,gravity_mps2=9.81,disc_radius_m=6371000.)


def run_case(model,degrees,kernels):
    f=latitude.fixture(model,degrees,'near_roll' if degrees<0 else 'interior')
    p=full_problem(f,kernels)
    truth=np.array([f['truth'].get(name,0.)/p.bounds.limits[name] for name in p.bounds.active]);truth[-1]=-1.
    budget=adapter.SweepBudget(2,56)
    reference=budget.call('tangent',p.prediction_tangent,truth,model)[0]
    reference_error=geographic.position_error(f,reference)
    point=truth*.5;point[-1]=-.8
    probes=np.array([point,point+np.eye(27)[0]*1e-4,point+np.eye(27)[-1]*1e-4])
    metric=np.tile(f['metric'],(len(f['gps_times']),1))
    out=adapter.evaluate(p,model,point,probes,metric,.01**2*np.eye(72),16,budget)
    errors=[]
    for column in range(27):
        step=np.eye(27)[column]*1e-4
        plus=budget.call('value',p.predict,point+step,model)
        minus=budget.call('value',p.predict,point-step,model)
        finite=adapter.physical_delta(plus,minus,metric).ravel()/2e-4
        errors.append(float(np.max(abs(finite-out['physical_jacobian'][:,column]))))
    return dict(identity=f'{model}::{degrees:+g}',model=model,latitude_deg=degrees,
        clock_construction=f['clock'],parameters=out['parameter_names'],training_epochs=16,
        prediction_epochs=8,truth_maximum_position_error_m=reference_error,
        maximum_derivative_error_m_per_normalized_parameter=max(errors),
        derivative_errors_by_parameter=dict(zip(out['parameter_names'],errors)),geometry=out['geometry'],
        gps_epochs_at_packet_boundaries=out['gps_epochs_at_packet_boundaries'],
        future_probe_shape=list(out['future_probe_deltas_m'].shape),native_sweeps=dict(budget.counts),
        all_sweeps_complete=all(r['status']=='complete' for r in budget.journal),
        passed=bool(reference_error<.002 and max(errors)<2e-4 and len(out['parameter_names'])==27
            and budget.counts=={'tangent':2,'value':56}),observed_fit_starts=0,archive_records_loaded=0)
