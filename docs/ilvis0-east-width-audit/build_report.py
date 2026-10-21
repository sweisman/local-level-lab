# SPDX-License-Identifier: AGPL-3.0-or-later
"""Audit saved east-coordinate endpoints without integration or optimization."""
from fractions import Fraction as F
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_control_shards as storage
from lll.ilvis0_saved_prediction_audit import support,endpoint

HERE=Path(__file__).resolve().parent
SOURCE=ROOT/'docs/ilvis0-reused-complete-prediction'


def build():
    receipt=storage._load(SOURCE/'evidence-receipt.json');used={}
    def read(name):
        path=storage.path_within(SOURCE,name);digest=storage._sha(path)
        if receipt['artifacts'].get(name)!=digest:raise ValueError('unsealed or changed audit input: '+name)
        used[name]=digest;return storage._load(path)
    manifest=read('manifest.json');completion=read('completion.json');summary=read('summary.json')
    if (completion['manifest_sha256']!=used['manifest.json'] or completion['summary_sha256']!=used['summary.json']
            or completion['state']!=summary['state'] or not summary['passed']):
        raise ValueError('complete passing saved calculations required')
    comp=read('comparison.json');baseline=read(manifest['inputs']['baseline']['path'])['cases']
    rows=[];checks=0
    for item in summary['results']:
        task=next(t for t in manifest['tasks'] if t['identity']==item['identity'])
        if task['payload']['model']!=0:continue
        envelope=read(item['artifact']);result=envelope['result']
        def artifact(basename):
            names=[n for n in envelope['artifacts'] if Path(n).name==basename]
            if len(names)!=1:raise ValueError('one exact saved audit artifact required')
            value=read(names[0])
            if envelope['artifacts'][names[0]]!=used[names[0]]:raise ValueError('result artifact hash differs')
            return value
        future=artifact('future.json');region=artifact('training.json')['region'];bound=future['bound'];axis=1
        if (not result['passed'] or result['excluded'] or region['parameter_count']!=78
                or future['envelope']['future_truth_used'] or region['future_truth_used']):
            raise ValueError('complete unchanged 78-column no-future-input result required')
        blocks=(future['jacobian'][axis],bound['previous_coefficients'][axis],
            bound['acceleration_coefficients'][axis],bound['transform_coefficients'][axis])
        if tuple(map(len,blocks))!=(27,6,9,9):raise ValueError('all coefficient blocks required')
        unit=F(region['coordinate_scale'][axis])
        objective=[v*region['coordinate_scale'][axis] for block in blocks for v in block]+[0.]*27
        cert=future['envelope']['certificates'][axis]
        args=(future['lower'],future['upper'],region['inequality_design'],region['inequality_upper'])
        high=support(*args,objective,cert['upper_multipliers']);checks+=1
        low=support(*args,[-v for v in objective],cert['lower_multipliers']);checks+=1
        if high!=F(cert['upper']) or low!=F(cert['negated_lower']):raise ValueError('saved support does not reproduce')
        shift=(F(future['nominal'][axis])-F(region['origin'][axis]))*unit-sum(
            (F(v)*F(c) for v,c in zip(objective,region['center'],strict=True)),F(0))
        remainder=F(bound['unshared_remainder'][axis])*unit;arithmetic=F(region['arithmetic_allowance'])
        if unit<=0 or remainder<0 or arithmetic<0:raise ValueError('nonnegative physical allowances required')
        left=endpoint(shift-low-remainder-arithmetic,False);right=endpoint(shift+high+remainder+arithmetic,True)
        if (left!=future['envelope']['lower'][axis] or right!=future['envelope']['upper'][axis]
                or left!=result['future_lower_m'][axis] or right!=result['future_upper_m'][axis]):
            raise ValueError('saved outward endpoints differ')
        rows.append(dict(identity=item['identity'],profile=task['payload']['profile'],sector=task['payload']['sector'],
            lower_m=left,upper_m=right,width_m=endpoint(F(right)-F(left),True),
            affine_width_m=endpoint(high+low,True),future_remainder_radius_m=endpoint(remainder,True),
            arithmetic_radius_m=endpoint(arithmetic,True),
            diagnostic_without_future_remainder_lower_m=endpoint(shift-low-arithmetic,False),
            diagnostic_without_future_remainder_upper_m=endpoint(shift+high+arithmetic,True),
            future_provider=bound['certificate_reuse']['coordinate_providers'][axis]))
    if len(rows)!=16 or checks!=32:raise ValueError('all 16 regions and exactly 32 support checks required')
    groups=[]
    for profile in (False,True):
        selected=[r for r in rows if r['profile']==profile]
        if len(selected)!=8 or {r['sector'] for r in selected}!=set(range(8)):raise ValueError('complete original group required')
        lower=min(selected,key=lambda r:r['lower_m']);upper=max(selected,key=lambda r:r['upper_m'])
        verified=next(c for c in comp['cases'] if c['model']==0 and c['profile']==profile)
        if lower['lower_m']!=verified['lower'][1] or upper['upper_m']!=verified['upper'][1]:
            raise ValueError('region union differs from saved complete group')
        target=F(next(c for c in baseline if c['model']==0 and c['profile']==profile)['union_width_m'][1])/2
        width=F(upper['upper_m'])-F(lower['lower_m'])
        diagnostic_lower=min(r['diagnostic_without_future_remainder_lower_m'] for r in selected)
        diagnostic_upper=max(r['diagnostic_without_future_remainder_upper_m'] for r in selected)
        groups.append(dict(profile=profile,lower_sector=lower['sector'],upper_sector=upper['sector'],
            lower_provider=lower['future_provider'],upper_provider=upper['future_provider'],
            width_m=endpoint(width,True),target_m=float(target),excess_percent=float((width/target-1)*100),
            diagnostic_without_future_remainder_width_m=endpoint(F(diagnostic_upper)-F(diagnostic_lower),True),
            diagnostic_is_valid_prediction=False))
    report=dict(regions=rows,groups=groups,exact_saved_support_checks=checks,native_evaluations=0,
        bound_evaluations=0,optimizer_starts=0,original_reads=0,source_artifacts=used,
        source_receipt_sha256=storage._sha(SOURCE/'evidence-receipt.json'),
        implementation_sha256=storage._sha(Path(__file__)),plan_sha256=storage._sha(HERE/'PLAN.md'),
        observational_coverage_qualified=False,scientific_decision='abstain')
    storage._replace(HERE/'audit.json',report)
    text=['# Why the two east-coordinate ranges remain too wide','',
        'All 32 saved east-coordinate support certificates and all 16 interval endpoints reproduce exactly. '
        'No integration, new bound or optimization ran.','',
        '| Processing | Actual width | Target | Lower / upper sectors | Future providers | Remainder-removed diagnostic |',
        '|---|---:|---:|---|---|---:|']
    for g in groups:
        text.append(f"| {'Profiled removal' if g['profile'] else 'Zero removal'} | {g['width_m']:.6f} m | {g['target_m']:.6f} m | "
            f"{g['lower_sector']} / {g['upper_sector']} | {g['lower_provider']} / {g['upper_provider']} | "
            f"{g['diagnostic_without_future_remainder_width_m']:.6f} m |")
    text+=['','The final column removes the future remainder algebraically while leaving training constraints '
        'and the saved support certificates fixed. **It is not a valid tighter prediction range.** '
        'It measures sensitivity to that allowance; it does not prove an attainable improvement or an optimum.','',
        'All eight regions in each case were included. No future truth or aircraft residual was consulted. '
        'The earlier width failure and all 53 aircraft comparisons remain unchanged.','',
        '[Finite audit scope](PLAN.md) · [Source outcome](../ilvis0-reused-complete-prediction/INTERPRETATION.md).']
    (HERE/'README.md').write_text('\n'.join(text)+'\n')
    print(json.dumps(dict(exact_saved_support_checks=checks,regions=len(rows),groups=groups),indent=2))


if __name__=='__main__':build()
