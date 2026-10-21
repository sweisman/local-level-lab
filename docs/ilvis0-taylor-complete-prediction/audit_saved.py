#!/usr/bin/env python3
"""Decompose sealed per-region widths; no native integration or optimization."""
from collections import Counter
from fractions import Fraction as F
import hashlib
import json
import math
from pathlib import Path
from statistics import median

HERE=Path(__file__).resolve().parent


def audit():
    receipt=json.loads((HERE/'evidence-receipt.json').read_text())['artifacts'];used={}
    def read(name):
        content=(HERE/name).read_bytes();digest=hashlib.sha256(content).hexdigest()
        if receipt.get(name)!=digest:raise ValueError('sealed artifact changed: '+name)
        used[name]=digest
        return json.loads(content)
    summary=read('summary.json');groups={};failures=Counter();regions=[]
    if summary['state']!='terminal' or summary['completed']!=48:raise ValueError('complete frozen study required')
    for item in summary['results']:
        record=read(item['artifact']);row=record['result'];identity=item['identity']
        if not row.get('passed',False):
            failures[(row.get('reason','unspecified'),record['charged']['bound_calls'])]+=1
            continue
        group=(row['task']['model'],row['task']['profile']);directory='artifacts/'+identity+'/'
        training=read(directory+'training.json');future=read(directory+'future.json');bound=read(directory+'bound-07.json')
        if future['bound']!=bound:raise ValueError('future/bound identity changed')
        region=training['region'];axes=[]
        for axis,scale in enumerate(region['coordinate_scale']):
            cert=future['envelope']['certificates'][axis]
            affine=F(cert['upper'])+F(cert['negated_lower'])
            radius=F(bound['unshared_remainder'][axis])*F(scale)+F(region['arithmetic_allowance'])
            total=affine+2*radius
            endpoints=[future['envelope'][k][axis] for k in ('lower','upper')]
            exported=F(endpoints[1])-F(endpoints[0]);rounding=exported-total
            if affine<0 or radius<0 or not F(0)<=rounding<=8*F(math.ulp(max(map(abs,endpoints)))):
                raise ValueError('saved support/remainder decomposition does not reconstruct outward width')
            axes.append(dict(axis=axis,affine_width_m=float(affine),unshared_width_m=float(2*radius),
                total_width_m=float(total),exported_width_m=float(exported),rounding_padding_m=float(rounding),
                unshared_fraction=float(2*radius/total) if total else 0.))
        saved=dict(identity=identity,model=group[0],profile=group[1],axes=axes)
        regions.append(saved);groups.setdefault(group,[]).append(saved)
    table=[]
    for model in range(3):
        for profile in (False,True):
            selected=groups.get((model,profile),[])
            entry=dict(model=model,profile=profile,passing_regions=len(selected),complete=len(selected)==8,axes=[])
            for axis in range(3):
                values=[r['axes'][axis] for r in selected]
                if values:entry['axes'].append(dict(axis=axis,**{
                    'median_'+key:median(v[key] for v in values)
                    for key in ('affine_width_m','unshared_width_m','total_width_m','unshared_fraction')}))
            table.append(entry)
    result=dict(regions=regions,groups=table,failures=[dict(reason=reason,charged_bounds=count,regions=n)
        for (reason,count),n in sorted(failures.items())],inputs=used,
        input_receipt_sha256=hashlib.sha256((HERE/'evidence-receipt.json').read_bytes()).hexdigest(),
        native_evaluations=0,optimizer_starts=0,new_support_solves=0,
        per_region_only=True,observational_coverage_qualified=False,scientific_decision='abstain')
    (HERE/'width-audit.json').write_text(json.dumps(result,sort_keys=True,separators=(',',':'))+'\n')
    lines=['# What makes the saved prediction ranges wide','',
        'This audit reads the 32 passing regions only. It exactly reconstructs each saved '
        'axis width from its affine support range and twice its unshared error allowance, '
        'checking the final outward-rounding padding. No integration, fitting or new support solve runs.','',
        '| Candidate / removal | Passing regions | Axis | Median affine width (m) | Median unshared width (m) | Median unshared share |',
        '|---|---:|---|---:|---:|---:|']
    for g in table:
        label=('Specified-field globe','Zero-field globe','Flat disc')[g['model']]+(' / profiled' if g['profile'] else ' / zero')
        for a in g['axes']:
            lines.append(f"| {label} | {g['passing_regions']}/8 | {('North','East','Height')[a['axis']]} | "
                f"{a['median_affine_width_m']:.5g} | {a['median_unshared_width_m']:.5g} | {100*a['median_unshared_fraction']:.1f}% |")
    lines+=['','These are **per-region medians**, not a decomposition of the combined union. '
        'The affine range includes physical calibration and shared-error uncertainty under '
        'training constraints. The unshared allowance bounds the remaining approximation '
        'error; it is not observed sensor noise. Nested force, position and lever allowances '
        'must not be added as independent contributions.','',
        'Missing regions remain missing. The audit cannot qualify an incomplete group, '
        'turn numerical allowances into statistical uncertainty or change aircraft findings.','',
        '[Study outcome](INTERPRETATION.md) · [Next work](NEXT_PLAN.md).']
    (HERE/'WIDTH_AUDIT.md').write_text('\n'.join(lines)+'\n')
    print('Verified and decomposed',len(regions)*3,'saved per-region axis widths; zero new numerical evaluations.')


if __name__=='__main__':audit()
