# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved-only comparison against the actual training-conditioned baseline."""
from fractions import Fraction as F
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_control_shards as runner

PUBLIC=Path(__file__).resolve().parent


def main():
    receipt=runner._load(PUBLIC/'evidence-receipt.json')
    for name,digest in receipt['artifacts'].items():
        if runner._sha(runner.path_within(PUBLIC,name))!=digest:raise ValueError('sealed comparison changed')
    manifest=runner._load(PUBLIC/'manifest.json');summary=runner._load(PUBLIC/'summary.json');rows=[]
    for item in summary['results']:
        result=runner._load(PUBLIC/item['artifact'])['result']
        if not result.get('passed'):continue
        identity=result['identity'];bundle=runner._load(PUBLIC/manifest['inputs'][identity]['path'])
        old=bundle['future']['bound'];prior=old['conditioning']
        new=runner._load(PUBLIC/'artifacts'/identity/'directional-proof.json')
        if (prior['reference_binding']!=new['reference_binding'] or prior['source_id']!=new['source_id']
                or any(not a<=b<=c<=d for a,b,c,d in zip(old['lower'],new['lower'],new['upper'],old['upper'],strict=True))):
            raise ValueError('training proof must cover the new physical subdomain and same reference')
        a=list(map(F,prior['component_changes']));b=list(map(F,new['component_changes']))
        if len(a)!=3 or len(b)!=3 or min(a+b+[F(prior['norm_change']),F(new['norm_change'])])<0:
            raise ValueError('complete nonnegative acceleration radii required')
        dominated=all(x<=y for x,y in zip(a,b)) and F(prior['norm_change'])<=F(new['norm_change'])
        rows.append(dict(identity=identity,model=result['task']['model'],profile=result['task']['profile'],sector=result['task']['sector'],
            training_norm=prior['norm_change'],physical_norm=new['norm_change'],
            training_components=prior['component_changes'],physical_components=new['component_changes'],
            physical_bound_adds_no_tightening=dominated))
    comp=runner._load(PUBLIC/'comparison.json');complete=[c for c in comp['cases'] if c['complete']]
    unchanged=sum(all(F(v)==1 for v in c['ratio_to_inherited']) for c in complete)
    dominates=sum(r['physical_bound_adds_no_tightening'] for r in rows)
    data=PUBLIC/'baseline-diagnosis.json';runner._replace(data,dict(cases=rows,checked_cases=len(rows),
        training_dominates=dominates,complete_groups=len(complete),unchanged_complete_groups=unchanged,
        new_native_evaluations=0,new_bound_calls=0,optimizer_starts=0))
    text=['# Compare with the baseline actually in use','',
        f"The existing training-conditioned acceleration bound is at least as tight in all three components "
        f"and in vector norm for **{dominates}/{len(rows)} completed cases**. The saved reference and domain "
        'checks establish that it applies to the new domain. Intersecting these particular static '
        'bounds would leave the old acceleration limits unchanged.','',
        f"All {unchanged}/{len(complete)} complete candidate/processing groups retain exactly their inherited "
        'combined prediction widths. Both specified-field globe groups still miss the fixed width target. '
        'Completing the unstarted or interrupted disc calculations cannot change that failed all-group gate.','',
        'The earlier static comparison used the broad physical prior as its baseline. '
        'The complete prediction method already had a much tighter training-derived '
        'acceleration range. Replacing it with the new physical-only range lost useful '
        'information. The comparison with the actual prediction baseline should have '
        'preceded this run.','',
        'This diagnosis uses saved proof radii and qualified range endpoints only. It '
        'performs no native prediction, propagation bound, support calculation or fit. '
        'It does not reinterpret the numerical failures or change their labels.','',
        '[Complete comparison](README.md) · [Interpretation](INTERPRETATION.md) · [Next step](NEXT_PLAN.md).']
    report=PUBLIC/'BASELINE_DIAGNOSIS.md';report.write_text('\n'.join(text)+'\n')
    runner._replace(PUBLIC/'baseline-diagnosis-receipt.json',dict(
        source_evidence_sha256=runner._sha(PUBLIC/'evidence-receipt.json'),builder_sha256=runner._sha(Path(__file__)),
        artifacts={p.name:runner._sha(p) for p in (data,report)},new_native_evaluations=0,new_bound_calls=0,optimizer_starts=0))
    print(f'Checked {len(rows)} saved proofs; training dominates {dominates}; {unchanged}/{len(complete)} complete groups unchanged.')


if __name__=='__main__':main()
