# SPDX-License-Identifier: AGPL-3.0-or-later
"""Audit saved joint profiles; no observation extraction, integration or optimization."""
import math

from . import ilvis0_saved_audit as saved, ilvis0_solver_diagnosis as diagnosis

VERSION = 'ilvis0-saved-joint-z-audit-v1'
MODELS = ('sphere_rotating', 'sphere_still', 'flat_still')


def compare(summary, manifest):
    fits = summary['fits']
    identities = [f['identity'] for f in fits]
    if (summary['state']!='complete' or summary['starts']!=27 or len(fits)!=27 or
            identities!=manifest['identities'] or len(set(identities))!=27):
        raise ValueError('incomplete or changed profile identities')
    case = manifest['cases'][0]
    rows, parameters, modes, boundary = [], [], [], []
    points = {}
    for f in fits:
        gain, bias = f['fixed_z_gain_percent'], f['fixed_z_bias_dph']
        key = (gain,bias,f['model'])
        if key in points: raise ValueError('duplicate grid coordinate')
        points[key] = f
        if (gain not in (-2,0,2) or bias not in (-1,0,1) or f['model'] not in MODELS or
                f['fixed_normalized_coordinates']!={'gyro_gain_z':gain/2.,'gyro_bias_z':float(bias)} or
                not math.isclose(f['parameters']['gyro_gain_z'],gain/100.,abs_tol=1e-15) or
                not math.isclose(f['parameters']['gyro_bias_z'],bias*math.pi/648000,abs_tol=1e-15)):
            raise ValueError('fixed profile coordinates disagree')
        physical = saved.parameter_rows(f,case['limits'],profile=case['profile'])
        diagnostic, weak = diagnosis.parameter_diagnostics(f)
        full = dict(zip(f['full_coordinate_order'],f['full_gradient']))
        if len(full)!=len(f['full_coordinate_order']) or len(full)!=len(f['active_parameters'])+2:
            raise ValueError('invalid full derivative coordinates')
        for n,g in zip(f['active_parameters'],f['gradient']):
            if not math.isclose(full[n],g,rel_tol=1e-8,abs_tol=1e-10):
                raise ValueError('full/free gradient disagreement')
        for value in full.values(): diagnosis.finite(value)
        common=dict(identity=f['identity'],model=f['model'],gain_percent=gain,bias_dph=bias)
        parameters.extend(dict(**common,**a,physical_value=b['value'],unit=b['unit']) for a,b in zip(diagnostic,physical))
        modes.extend(dict(**common,**m) for m in weak)
        boundary.extend(dict(**common,parameter=n) for n in f['active_bounds'])
        cost = diagnosis.finite(f['residual_sum_squares'],True)
        rms = [diagnosis.finite(v,True) for v in f['residual_rms_neu_m']]
        if len(rms)!=3: raise ValueError('invalid residual axes')
        rows.append(dict(**common,status=saved.fit_status(f),cost=cost,
            horizontal_rms_m=math.hypot(*rms[:2]),vertical_rms_m=rms[2],
            remaining_boundary_count=len(f['active_bounds']),fixed_gain_gradient=full['gyro_gain_z'],
            fixed_bias_gradient=full['gyro_bias_z'],stationarity=f['exact_projected_gradient_relative']))
    models=[]
    for model in MODELS:
        group=[r for r in rows if r['model']==model]
        low,high=min(r['cost'] for r in group),max(r['cost'] for r in group)
        models.append(dict(model=model,cost_min=low,cost_max=high,
            cost_range_percent=100*(high-low)/low if low else None,
            horizontal_rms_min_m=min(r['horizontal_rms_m'] for r in group),
            horizontal_rms_max_m=max(r['horizontal_rms_m'] for r in group),
            remaining_boundary_count_min=min(r['remaining_boundary_count'] for r in group),
            remaining_boundary_count_max=max(r['remaining_boundary_count'] for r in group)))
    complete=all(r['status']=='converged' for r in rows)
    globe=complete and all(min(points[(a,b,m)]['residual_sum_squares'] for m in MODELS[:2])<
        points[(a,b,'flat_still')]['residual_sum_squares'] for a in (-2,0,2) for b in (-1,0,1))
    specified=globe and all(points[(a,b,'sphere_rotating')]['residual_sum_squares']<
        points[(a,b,'sphere_still')]['residual_sum_squares'] for a in (-2,0,2) for b in (-1,0,1))
    return dict(version=VERSION,starts=27,converged=sum(r['status']=='converged' for r in rows),
        optimizer_starts=0,native_predictions=0,models=models,fits=rows,parameters=parameters,
        weak_directions=modes,remaining_boundaries=boundary,
        shape_preference='globe' if globe else 'unresolved',
        background_field_preference='specified_field' if specified else None,
        hardware_calibration_identified=False,scientific_decision='abstain')
