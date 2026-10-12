# SPDX-License-Identifier: AGPL-3.0-or-later
"""Compare sealed Z profiles using saved diagnostics only; never revise fit status."""
import math
from collections import Counter

from . import ilvis0_z_profile_audit as profiles
from . import ilvis0_saved_audit as saved

VERSION='ilvis0-saved-z-followup-audit-v1'
STUDIES=('original','removal','replication')
TARGETS=dict(original='570b37d23af5e245dd461051',removal='570b37d23af5e245dd461051',
             replication='d9d91c8edba5721931856fc9')


def coordinate(fit):
    return fit['fixed_z_gain_percent'],fit['fixed_z_bias_dph'],fit['model']


def compare(grids):
    if set(grids)!=set(STUDIES):raise ValueError('all three declared grids required')
    out=dict(version=VERSION,optimizer_starts=0,native_predictions=0,
        scientific_decision='abstain',studies=[],fits=[],models=[],nodes=[],failures=[],
        processing_changes=[],boundary_frequencies=[],weak_directions=[])
    indexed={};limits=None
    for study in STUDIES:
        summary,manifest=grids[study];case=manifest['cases'][0]
        if (len(manifest['cases'])!=1 or case['profile']!=(study=='removal') or
            summary['provenance']['segment_id']!=TARGETS[study] or
            manifest['clock']!='header_elapsed' or manifest['integration']!='original' or
            manifest['maximum_starts']!=27 or manifest['maximum_evaluations_per_start']!=200 or
            manifest['maximum_native_sweeps']!=5400 or manifest['retry_reserve']!=0):
            raise ValueError('changed recording, processing, timing or allowance')
        if limits is None:limits=case['limits']
        if case['limits']!=limits:raise ValueError('unmatched calibration bounds')
        expected=[f"{TARGETS[study]}::{case['case_id']}::{m}::gain{a:+d}::bias{b:+d}"
                  for a in (-2,0,2) for b in (-1,0,1) for m in profiles.MODELS]
        if manifest['identities']!=expected:raise ValueError('unregistered grid identities')
        audited=profiles.compare(summary,manifest)
        indexed[study]={coordinate(f):f for f in summary['fits']}
        for fit,row in zip(summary['fits'],audited['fits']):
            tolerance=fit['stationarity_tolerance']
            if (fit['case_id']!=case['case_id'] or not math.isfinite(tolerance) or tolerance<=0 or
                not isinstance(fit['evaluations'],int) or not 0<=fit['evaluations']<=200):
                raise ValueError('invalid saved stopping metadata')
            grad=list(zip(fit['active_parameters'],fit['scaled_projected_gradient']))
            top=sorted(grad,key=lambda r:abs(r[1]),reverse=True)[:3]
            weak=[r for r in audited['weak_directions'] if r['identity']==fit['identity'] and r['weak_rank']==1]
            weak=sorted(weak,key=lambda r:abs(r['loading']),reverse=True)[:3]
            detail=dict(study=study,**row,evaluations=fit['evaluations'],
                stationarity_ratio=fit['exact_projected_gradient_relative']/tolerance,
                saved_stationarity_passed=fit['exact_projected_gradient_relative']<=tolerance,
                solver_reported_success=fit['solver_reported_success'],
                stopping_message=fit['message'],budget_exhausted='maximum number of function evaluations' in fit['message'].lower(),
                removal_fraction=fit['parameters']['earth_removal'],
                top_gradient_parameters=';'.join(n for n,_ in top),
                top_gradient_values=';'.join(f'{v:.12g}' for _,v in top),
                weakest_parameters=';'.join(r['parameter'] for r in weak),
                weakest_loadings=';'.join(f"{r['loading']:.12g}" for r in weak),
                accepted_step_history_available=fit['accepted_step_history_available'])
            out['fits'].append(detail)
            if row['status']!='converged':out['failures'].append(detail)
        out['weak_directions'].extend(dict(study=study,**r) for r in audited['weak_directions'])
        complete_nodes=0
        for a in (-2,0,2):
            for b in (-1,0,1):
                fits=[indexed[study][a,b,m] for m in profiles.MODELS]
                complete=all(saved.fit_status(f)=='converged' for f in fits)
                complete_nodes+=complete
                globe=min(f['residual_sum_squares'] for f in fits[:2])
                disc=fits[2]['residual_sum_squares']
                preference=('globe' if globe<disc else 'disc' if disc<globe else 'tie') if complete else 'unresolved'
                out['nodes'].append(dict(study=study,gain_percent=a,bias_dph=b,
                    complete=complete,shape_preference=preference,
                    achieved_globe_cost=globe,achieved_disc_cost=disc,
                    achieved_still_minus_specified_cost=fits[1]['residual_sum_squares']-fits[0]['residual_sum_squares'],
                    background_field_preference=('specified_field' if fits[0]['residual_sum_squares']<fits[1]['residual_sum_squares'] else 'zero_field')
                        if audited['shape_preference']=='globe' else None))
        out['studies'].append(dict(study=study,converged=audited['converged'],complete_nodes=complete_nodes,
            shape_preference=audited['shape_preference'],background_field_preference=audited['background_field_preference'],
            native_sweeps=sum(f['evaluations'] for f in summary['fits'])))
        for model in profiles.MODELS:
            group=[r for r in out['fits'] if r['study']==study and r['model']==model]
            good=[r for r in group if r['status']=='converged'];bad=[r for r in group if r['status']!='converged']
            extrema=lambda rows,key,fn:fn(r[key] for r in rows) if rows else None
            raw=[f for f in summary['fits'] if f['model']==model]
            frequencies=Counter((r['parameter'],r['boundary']) for r in audited['parameters']
                if r['model']==model and r['boundary']!='interior')
            out['boundary_frequencies'].extend(dict(study=study,model=model,parameter=n,boundary=b,count=count,
                inspected_fits=len(group)) for (n,b),count in sorted(frequencies.items()))
            out['models'].append(dict(study=study,model=model,converged=len(good),unresolved=len(bad),
                completed_cost_min=extrema(good,'cost',min),completed_cost_max=extrema(good,'cost',max),
                unfinished_achieved_cost_min=extrema(bad,'cost',min),unfinished_achieved_cost_max=extrema(bad,'cost',max),
                completed_horizontal_min_m=extrema(good,'horizontal_rms_m',min),
                completed_horizontal_max_m=extrema(good,'horizontal_rms_m',max),
                remaining_bounds_min=extrema(group,'remaining_boundary_count',min),
                remaining_bounds_max=extrema(group,'remaining_boundary_count',max),
                removal_fraction_min=min(f['parameters']['earth_removal'] for f in raw),
                removal_fraction_max=max(f['parameters']['earth_removal'] for f in raw)))
    if grids['original'][0]['provenance']!=grids['removal'][0]['provenance']:
        raise ValueError('processing grids do not use identical measurements')
    for key,original in indexed['original'].items():
        changed=indexed['removal'][key];gain,bias,model=key
        out['processing_changes'].append(dict(gain_percent=gain,bias_dph=bias,model=model,
            paired_status='converged' if all(saved.fit_status(f)=='converged' for f in (original,changed)) else 'unresolved',
            relative_cost_change=(changed['residual_sum_squares']-original['residual_sum_squares'])/original['residual_sum_squares'],
            removal_fraction=changed['parameters']['earth_removal'],
            remaining_boundary_count_change=len(changed['active_bounds'])-len(original['active_bounds'])))
    return out
