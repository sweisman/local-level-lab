# SPDX-License-Identifier: AGPL-3.0-or-later
"""Trace the 18 available fresh union endpoints without optimization or native predictions."""
import csv
from fractions import Fraction as F
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_control_shards as runner
from lll.ilvis0_certificate_components import decompose

PUBLIC=Path(__file__).resolve().parent
BLOCKS=(('mounting',0,3),('other_physical',3,27),('velocity_lever',27,33),
    ('acceleration',33,42),('force_matrix',42,51),('arithmetic_products',51,78))


def main():
    receipt=runner._load(PUBLIC/'evidence-receipt.json')
    for name,digest in receipt['artifacts'].items():
        if runner._sha(runner.path_within(PUBLIC,name))!=digest:raise ValueError('sealed evidence changed')
    comparison=runner._load(PUBLIC/'comparison.json');summary=runner._load(PUBLIC/'summary.json')
    rows=[runner._load(PUBLIC/item['artifact'])['result'] for item in summary['results']]
    if len(rows)!=48:raise ValueError('all 48 saved outcomes required')
    endpoints=[]
    for case in comparison['cases']:
        if not case['complete']:continue
        group=[r for r in rows if r.get('passed') and (r['task']['model'],r['task']['profile'])==(case['model'],case['profile']) and not r['excluded']]
        for axis in range(3):
            for sign,key in ((1,'upper'),(-1,'lower')):
                # Deterministic ties retain an explicit chosen cell. No favorable-cell filtering.
                selected=sorted(group,key=lambda r:r['identity'])
                extreme=(max if sign==1 else min)(r['future_'+key+'_m'][axis] for r in selected)
                row=next(r for r in selected if r['future_'+key+'_m'][axis]==extreme)
                if extreme!=case['fresh_'+key+'_m'][axis]:raise ValueError('union endpoint changed')
                directory=PUBLIC/'artifacts'/row['identity']
                future=runner._load(directory/'future.json');region=runner._load(directory/'training.json')['region']
                scale=region['coordinate_scale'][axis];bound=future['bound']
                raw=future['jacobian'][axis]+bound['previous_coefficients'][axis]+bound['acceleration_coefficients'][axis]+bound['transform_coefficients'][axis]
                objective=[v*scale for v in raw]+[0.]*27
                if len(objective)!=78:raise ValueError('all 78 columns required')
                cert=future['envelope']['certificates'][axis]
                value=decompose(future['lower'],future['upper'],region['inequality_design'],region['inequality_upper'],
                    [sign*v for v in objective],cert['upper_multipliers' if sign==1 else 'lower_multipliers'],
                    cert['upper' if sign==1 else 'negated_lower'])
                midpoint_center=F(value['center_value']);terms=list(map(F,value['constraint_terms']));boxes=list(map(F,value['box_terms']))
                n=len(region['design']);design=[r+[0.]*27 for r in region['design']]
                if (region['inequality_design'][:n]!=design
                        or region['inequality_design'][n:2*n]!=[[-v for v in r] for r in design]
                        or region['inequality_upper'][:n]!=region['target_upper']
                        or region['inequality_upper'][n:2*n]!=[-v for v in region['target_lower']]):
                    raise ValueError('original training-row ordering changed')
                weights=cert['upper_multipliers' if sign==1 else 'lower_multipliers']
                training_radius=sum(((F(weights[j])+F(weights[n+j]))*
                    (F(region['target_upper'][j])-F(region['target_lower'][j]))/2 for j in range(n)),F(0))
                recent=region['inequality_upper'][-2*n:]
                recent_weights=weights[-2*n:]
                if (region['inequality_design'][-2*n:-n]!=design
                        or region['inequality_design'][-n:]!=[[-v for v in row] for row in design]):
                    raise ValueError('recomputed training-row ordering changed')
                if len(recent)!=2*n or any(F(recent[j])+F(recent[n+j])<0 for j in range(n)):
                    raise ValueError('ordered recomputed training intervals required')
                recent_radius=sum(((F(recent_weights[j])+F(recent_weights[n+j]))*(F(recent[j])+F(recent[n+j]))/2 for j in range(n)),F(0))
                shift=(F(future['nominal'][axis])-F(region['origin'][axis]))*F(scale)-sum(
                    (F(v)*F(c) for v,c in zip(objective,region['center'],strict=True)),F(0))
                radius=F(bound['unshared_remainder'][axis])*F(scale)+F(region['arithmetic_allowance'])
                signed_exact=sign*shift+F(value['total'])+radius
                padding=sign*F(extreme)-signed_exact
                if padding<0:raise ValueError('outward endpoint changed')
                item=dict(model=case['model'],profile=case['profile'],axis=('north','east','height')[axis],
                    endpoint=key,identity=row['identity'],midpoint_feasible=value['midpoint_feasible'],
                    signed_endpoint_m=sign*extreme,center_term_m=float(sign*shift+midpoint_center),
                    inherited_constraints_m=float(sum(terms[:-2*n],F(0))),
                    training_radius_m=float(training_radius+recent_radius),
                    original_training_radius_m=float(training_radius),recomputed_training_radius_m=float(recent_radius),
                    training_center_slack_m=float(sum(terms[:2*n],F(0))-training_radius),
                    older_added_constraints_m=float(sum(terms[2*n:-2*n],F(0))),
                    recomputed_training_constraints_m=float(sum(terms[-2*n:],F(0))),
                    remainder_m=float(radius),rounding_padding_m=float(padding),
                    **{name+'_box_m':float(sum(boxes[start:stop],F(0))) for name,start,stop in BLOCKS})
                # Save all physical columns, including zero contributions, for reproduction.
                item.update({f'physical_{j:02d}_box_m':float(boxes[j]) for j in range(27)})
                for epoch in range(n//3):
                    original_radius=sum(((F(weights[j])+F(weights[n+j]))*
                        (F(region['target_upper'][j])-F(region['target_lower'][j]))/2
                        for j in range(3*epoch,3*epoch+3)),F(0))
                    updated_radius=sum(((F(recent_weights[j])+F(recent_weights[n+j]))*
                        (F(recent[j])+F(recent[n+j]))/2 for j in range(3*epoch,3*epoch+3)),F(0))
                    item[f'training_epoch_{epoch}_original_m']=float(original_radius)
                    item[f'training_epoch_{epoch}_recomputed_m']=float(updated_radius)
                endpoints.append(item)
    if len(endpoints)!=18:raise ValueError('three complete fresh unions, three axes and both endpoints required')
    path=PUBLIC/'endpoint-components.csv'
    with path.open('w',newline='') as handle:
        writer=csv.DictWriter(handle,fieldnames=list(endpoints[0]),lineterminator='\n');writer.writeheader();writer.writerows(endpoints)
    text=['# Where the available fresh prediction ranges come from','',
        'This diagnosis accounts for all 18 fresh endpoints of the three complete groups; the other groups remain incomplete. '
        'Every selected certificate is reproduced with exact rational arithmetic. These are fresh ranges, before intersection with the older complete comparison. It runs no optimizer, '
        'native trajectory calculation or aircraft fit.','',
        '| Candidate / removal | Axis | Mount box (m) | Other physical box (m) | Common-error box (m) | Product box (m) |',
        '|---|---|---:|---:|---:|---:|']
    for case in comparison['cases']:
        if not case['complete']:continue
        for axis in ('north','east','height'):
            selected=[r for r in endpoints if (r['model'],r['profile'],r['axis'])==(case['model'],case['profile'],axis)]
            totals={k:sum(F(r[k]) for r in selected) for k in selected[0] if k.endswith('_box_m')}
            label=('Globe with field','Globe, zero field','Flat disc')[case['model']]+(' / profiled' if case['profile'] else ' / zero')
            common=sum((totals[name+'_box_m'] for name in ('velocity_lever','acceleration','force_matrix')),F(0))
            text.append(f"| {label} | {axis} | {float(totals['mounting_box_m']):.5g} | {float(totals['other_physical_box_m']):.5g} | {float(common):.5g} | {float(totals['arithmetic_products_box_m']):.5g} |")
    text+=['','## Training allowances at the difficult endpoints','',
        '| Specified-field globe / removal | Axis | Weighted training half-widths (m) | Future remainder allowances (m) |',
        '|---|---|---:|---:|']
    for profile in (False,True):
        for axis in ('east','height'):
            selected=[r for r in endpoints if (r['model'],r['profile'],r['axis'])==(0,profile,axis)]
            text.append(f"| {'Profiled' if profile else 'Zero'} | {axis} | "
                f"{sum(r['training_radius_m'] for r in selected):.4f} | {sum(r['remainder_m'] for r in selected):.4f} |")
    text+=['','The training half-width term is the saved dual weight applied to each '
        'training interval radius. It includes the method’s nonlinear allowances and '
        'declared observation/arithmetic errors. It is not measured aircraft noise. '
        'These sizeable contributions support testing tighter propagation allowances '
        'on justified smaller domains before adding more mounting-angle cuts. A new '
        'bound may change the best certificate, so these numbers are not guaranteed '
        'improvements from tightening any one term.','',
        'The CSV separates original and recomputed training contributions, including '
        'every epoch. These are certificate weights on approximation and observation '
        'allowances, not an independent count of calibration errors.','',
        'These nonnegative box terms are what remains after applying each saved dual certificate. '
        'They are not a decomposition into independent physical errors. The CSV also retains signed '
        'constraint terms, endpoint-center separation, remainder allowances and outward rounding. '
        'Those terms must all be included to reconstruct a width. A box midpoint can be infeasible, '
        'so a constraint contribution may be negative.','',
        'Small box terms do not establish accurate calibration: uncertainty may instead enter through '
        'the constraints. A large multiplier or contribution is a property of this certificate, not '
        'proof of the physically dominant error or of an attainable model fit.','',
        '[All endpoint components](endpoint-components.csv) · [Study outcome](INTERPRETATION.md) · [Next step](NEXT_PLAN.md).']
    report=PUBLIC/'ENDPOINT_DIAGNOSIS.md';report.write_text('\n'.join(text)+'\n')
    runner._replace(PUBLIC/'endpoint-diagnosis-receipt.json',dict(
        source_evidence_sha256=runner._sha(PUBLIC/'evidence-receipt.json'),
        builder_sha256=runner._sha(Path(__file__)),helper_sha256=runner._sha(ROOT/'analysis/lll/ilvis0_certificate_components.py'),
        artifacts={p.name:runner._sha(p) for p in (report,path)},saved_endpoint_decompositions=18,
        optimizer_starts=0,native_evaluations=0,original_reads=0))
    print('Published exact saved-endpoint diagnosis: 18 endpoints, zero optimization/native calls.')


if __name__=='__main__':main()
