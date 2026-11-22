# SPDX-License-Identifier: AGPL-3.0-or-later
"""Allocate a nominal whole-path error budget across dual forecast targets."""

import math


def evaluate(physical, receiver, problem, point, forecast, *, theta, dv, dt,
             times, reserve, save):
    from .dual_target_forecast_wrapper import evaluate as dual

    m = len(getattr(problem, 'gps_times', ()))
    q = len(times)-m
    if (not 2 <= m < len(times) or not callable(save)
            or not callable(reserve)):
        raise ValueError('finite earlier and withheld epochs with saving required')
    calibration_alpha=.025
    future_alpha=.025/(3*q)
    seen=set()

    def save_joint(name, value):
        if name in ('bounded-physical.json','bounded-receiver.json'):
            target=('physical_position' if name=='bounded-physical.json'
                    else 'receiver_measurement')
            if (name in seen or not isinstance(value,dict)
                    or value.get('prediction_target')!=target
                    or value.get('later_observations_used') is not False
                    or value.get('scientific_decision')!='abstain'
                    or not math.isclose(
                        value.get('marginal_coverage_lower_bound',float('nan')),
                        1-calibration_alpha-future_alpha,
                        rel_tol=0,abs_tol=1e-12)):
                raise ValueError('declared marginal bound and target required')
            value=dict(value,
                       nominal_joint_coverage_lower_bound=.95,
                       joint_future_coordinate_count=3*q,
                       joint_allowance_method='shared-calibration-and-Bonferroni-future-v1',
                       assumptions_qualified_for_aircraft=False,
                       scientific_decision='abstain')
            seen.add(name)
        save(name,value)

    result=dual(physical,receiver,problem,point,forecast,
                theta=theta,dv=dv,dt=dt,times=times,reserve=reserve,
                save=save_joint,calibration_alpha=calibration_alpha,
                future_alpha=future_alpha,rank_rtol=1e-10)
    if seen!={'bounded-physical.json','bounded-receiver.json'}:
        raise ValueError('both target bounds required before later truth')
    return result
