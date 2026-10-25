# SPDX-License-Identifier: AGPL-3.0-or-later
"""Shared saved-fit invariants, without propagation, fitting or numerical imports.

Callers additionally verify artifact hashes, physical prediction errors, compiled
provenance and whole-study totals. A valid saved fit can remain unconverged.
"""
import math


def training_fit(fit,*,active,maximum_evaluations):
    parameters=fit['normalized_parameters'];cost=fit['residual_sum_squares']
    if (fit['active_parameters']!=active or len(parameters)!=len(active)
            or any(type(v) not in (int,float) or not math.isfinite(v) or abs(v)>1 for v in parameters)
            or type(fit['evaluations']) is not int or not 1<=fit['evaluations']<=maximum_evaluations
            or type(cost) not in (int,float) or not math.isfinite(cost) or cost<0
            or type(fit['converged']) is not bool):
        raise ValueError('saved training columns, bounds, cost or completion status differ')
    return dict(normalized_parameters=dict(zip(active,parameters,strict=True)),last_training_cost=cost,
        training_fit_converged=fit['converged'],fit_saved=True,
        stop_reason=fit.get('termination',fit.get('message')))


def complete_prediction(*,spec,result,fit,forecast,earlier,binding,operations,expected):
    """Check a returned forecast against explicit training-only expectations.

The caller constructs ``expected`` from frozen inputs, never fitted results.
This does not certify accuracy, likelihood calibration or scientific detection.
"""
    e=expected;times=e['times'];cut=e['cut'];later=len(times)-cut
    checked=training_fit(fit,active=e['active'],maximum_evaluations=e['maximum_evaluations'])
    if (any(result[k]!=v for k,v in spec.items())
            or forecast['active_parameters']!=e['active']
            or operations['value']!=0 or operations['tangent']!=fit['evaluations']+1
            or operations['packet_visits']!=e['packet_visits']
            or result['evaluations']!=fit['evaluations'] or result['native_calls']!=operations['tangent']
            or type(result['passed']) is not bool or result['passed']!=fit['converged']
            or type(result['converged']) is not bool or result['converged']!=fit['converged']
            or result['all_columns_retained'] is not True or result['training_cost']!=fit['residual_sum_squares']):
        raise ValueError('saved prediction identity, fit status or exact native charges differ')
    if (earlier['training_epochs']!=cut or earlier['prediction_epochs']!=later
            or earlier['times_s']!=times[:cut] or earlier['coordinates']!=e['training_coordinates']
            or earlier['native_prefix_packets']!=e['prefix_packets']
            or earlier['training_prefix_sha256']!=e['prefix_sha256']
            or earlier['weight_configuration']!=e['configuration']
            or result['weight_configuration']!=e['configuration']
            or earlier['weight_descriptor']!=e['descriptor'] or earlier['weight_source_sha256']!=e['weight_sha256']
            or earlier['time_origin_gps_sow_s']!=e['time_origin_s']
            or earlier['prediction_receiver_positions_used'] is not False
            or earlier['true_initial_state_supplied'] is not False or earlier['true_calibration_supplied'] is not False
            or forecast['times_s']!=times or forecast['training_epochs']!=cut or forecast['prediction_epochs']!=later
            or forecast['continuous_propagation_without_gps_reset'] is not True
            or forecast['prediction_receiver_positions_used'] is not False
            or result['forecast_saved_before_scoring'] is not True
            or result['training_epochs']!=cut or result['prediction_epochs']!=later
            or result['group_id']!=e['group'] or binding['group_id']!=e['group']
            or binding['layout']!=e['layout'] or binding['input_sha256']!=e['input_sha256']
            or binding['original_reads']!=0 or binding['protected_reads']!=0
            or result['original_reads']!=0 or result['protected_reads']!=0):
        raise ValueError('earlier-only training, saved forecast boundary or frozen input binding differs')
    return checked


def start_sensitivity(rows,errors_by_id):
    """Describe paired forecast changes without selecting on later errors."""
    groups={};identities=set()
    for row in rows:
        key=tuple(row[k] for k in ('model','profile','policy_id'))
        if row['identity'] in identities:raise ValueError('distinct saved start identities required')
        identities.add(row['identity']);groups.setdefault(key,[]).append(row)
    result=[]
    for (model,profile,policy),values in sorted(groups.items()):
        values=sorted(values,key=lambda row:row['start'])
        if len({v['start'] for v in values})!=len(values):raise ValueError('distinct starts per setting required')
        item=dict(model=model,profile=profile,policy_id=policy,available=False,calibrated_confidence_interval=False)
        if len(values)==2 and all(v['identity'] in errors_by_id for v in values):
            a,b=(errors_by_id[v['identity']] for v in values)
            if (not a or len(a)!=len(b) or any(len(v)!=3 or any(not math.isfinite(x) for x in v) for v in [*a,*b])):
                raise ValueError('matching complete finite three-axis forecast errors required')
            delta=[[x-y for x,y in zip(u,v,strict=True)] for u,v in zip(a,b,strict=True)]
            item.update(available=True,rms_neu_m=[math.sqrt(math.fsum(v[j]**2 for v in delta)/len(delta)) for j in range(3)],
                maximum_absolute_neu_m=[max(abs(v[j]) for v in delta) for j in range(3)],
                both_numerically_converged=all(v['converged'] for v in values))
        result.append(item)
    return result
