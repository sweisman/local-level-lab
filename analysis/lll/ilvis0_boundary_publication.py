# SPDX-License-Identifier: AGPL-3.0-or-later
"""Metadata-only qualification of complete boundary-recovery comparisons."""
import math

VERSION='ilvis0-boundary-publication-v1'
CASES={'bias1_unsubtracted','bias1_profiled_removal'}
MODELS={'sphere_rotating','sphere_still','flat_still'}
PAIR_COST_TOLERANCE=1e-6
PAIR_TRACK_RMS_TOLERANCE_M=.01


def classify(review,previous):
    targets=review['target_segment_ids'];rows=review['comparisons'];by_id={r['segment_id']:r for r in rows}
    required=review['required_repeat_identities'];pairs={r['identity']:r for r in review['pairs']}
    if (len(set(targets))!=len(targets) or set(by_id)!=set(targets) or len(by_id)!=len(rows)
            or len(set(required))!=len(required) or set(pairs)!=set(required) or len(pairs)!=len(review['pairs'])
            or any(sid not in previous or previous[sid]!='unresolved' for sid in targets)
            or any(i.split('::')[0] not in by_id for i in required)):
        raise ValueError('complete unresolved population and every unique repeat pair required')
    for pair in pairs.values():
        checked=False
        if pair['primary_passed'] and pair['repeat_passed']:
            cost=pair.get('relative_cost_difference');rms=pair.get('track_rms_neu_m')
            if (not isinstance(cost,(int,float)) or not math.isfinite(cost) or cost<0
                    or not isinstance(rms,list) or len(rms)!=3 or any(not math.isfinite(x) or x<0 for x in rms)):
                raise ValueError('passing endpoints require finite saved repeat metrics')
            checked=bool(cost<=PAIR_COST_TOLERANCE and max(rms)<=PAIR_TRACK_RMS_TOLERANCE_M)
        if pair['passed']!=checked:raise ValueError('repeat flag disagrees with saved checks')
    controls=review['controls'];controls_ok=len(controls)==2 and all(r['passed'] for r in controls)
    output={}
    for sid,row in by_id.items():
        cases=row['cases']
        if len(cases)!=2 or {c['case_id'] for c in cases}!=CASES:raise ValueError('both processing cases required')
        complete=True;contrasts=[];field=[]
        for case in cases:
            fits=case['fits'];models={f['model']:f for f in fits}
            if len(fits)!=3 or set(models)!=MODELS:raise ValueError('three unique models required')
            if any(not isinstance(f['residual_sum_squares'],(int,float)) or not math.isfinite(f['residual_sum_squares'])
                   or f['residual_sum_squares']<0 for f in fits):raise ValueError('finite nonnegative saved costs required')
            complete=complete and all(f['converged'] for f in fits)
            costs={m:f['residual_sum_squares'] for m,f in models.items()}
            contrasts.append(costs['flat_still']-min(costs['sphere_rotating'],costs['sphere_still']))
            field.append(costs['sphere_still']-costs['sphere_rotating'])
        own=[p for identity,p in pairs.items() if identity.split('::')[0]==sid]
        checks=bool(complete and controls_ok and own and all(p['passed'] for p in own))
        shape=('globe' if all(x>0 for x in contrasts) else 'flat' if all(x<0 for x in contrasts) else 'ambiguous') if checks else 'unresolved'
        output[sid]=dict(shape_preference=shape,specified_background_preferred=bool(shape=='globe' and all(x>0 for x in field)),
            all_primaries_passed=bool(complete),controls_passed=bool(controls_ok),required_repeat_pairs=len(own),
            passed_repeat_pairs=sum(p['passed'] for p in own),all_required_repeat_checks_passed=bool(own and all(p['passed'] for p in own)),
            failed_repeat_identities=[p['identity'] for p in own if not p['passed']],
            scientific_shape_decision='abstain',scientific_rotation_decision='abstain')
    return output
