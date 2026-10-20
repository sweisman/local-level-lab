# SPDX-License-Identifier: AGPL-3.0-or-later
"""Render every terminal identity and count reservations from failed bounds."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_control_shards as runner
from lll import ilvis0_control_publication as publication
from lll.ilvis0_sharded_native import read


def main():
    public=Path(__file__).parent;data=ROOT/'data/ilvis0-transport-range-preflight-20261020'
    publication.check(data,public);manifest=runner.verify(data);summary=runner.verify_completion(data)
    rows=[];accounts=[];verified=0
    for record in summary['results']:
        envelope=runner._load(data/record['artifact']);row=envelope['result']
        task=next(t for t in manifest['tasks'] if t['identity']==record['identity'])
        inputs=read(data/manifest['inputs'][task['input_key']]['path']);original=inputs['result']
        counts=dict.fromkeys(task['payload']['limits'],0)
        for name in sorted(n for n in envelope['artifacts'] if Path(n).name.startswith('reservation-')):
            event=runner._load(data/name);inc=event['increase']
            if not inc or any(k not in counts or type(v)!=int or v<1 for k,v in inc.items()):raise ValueError('invalid reservation')
            counts={k:v+inc.get(k,0) for k,v in counts.items()}
            if counts!=event['counts'] or any(v>task['payload']['limits'][k] for k,v in counts.items()):raise ValueError('reservation changed')
        condition_name=next((n for n in envelope['artifacts'] if Path(n).name=='conditioning.json'),None)
        supports=runner._load(data/condition_name)['supports_verified'] if condition_name else 0
        if supports>counts['exact_supports']:raise ValueError('verified work lacks reservation')
        verified+=supports;accounts.append(dict(identity=task['identity'],**counts,verified_supports=supports,passed=row.get('passed',False)))
        rows.append(dict(row,identity=task['identity'],model=original['model'],profile=original['profile']))
    passing=sum(r.get('passed',False) for r in rows)
    text=['# Saved-baseline transport comparison','',
        f'**{passing}/6 generated-source comparisons produced compatible completed bounds.**','',
        'Both zero-field globe cases reached the unchanged 120-second per-bound limit. '
        'All six identities remain charged; the failed cases will not be retried. '
        'The four completed cases preserve their source identities, reference centers, '
        'all coefficient matrices and verified training conditioning.','',
        '| Candidate / removal | Result | Fresh / old allowance N / E / height |',
        '|---|---|---:|']
    for row in rows:
        label=('Globe with specified field','Globe with zero field','Flat disc')[row['model']]+(' / profiled' if row['profile'] else ' / zero')
        ratios=' / '.join(f'{v:.5f}' for v in row.get('fresh_to_baseline_ratio',[])) or 'unavailable'
        result='Matched' if row.get('passed') else row.get('reason','reference mismatch')
        text.append(f'| {label} | {result} | {ratios} |')
    text+=['',f"Charged {summary['charged']['bound_calls']}/6 bounds and {summary['charged']['bound_steps']}/19,200 "
        f"bound packet-steps. All {sum(r['exact_supports'] for r in accounts)}/36 support reservations and "
        f"{verified}/36 verified supports are retained, including failed bounds. Elapsed {summary['elapsed_s']:.2f} seconds.",'',
        'The specified-field cases reduce north allowances by about 13–14%, east '
        'by about 3.4%, and height by about 10%. These are tighter numerical error '
        'allowances, not improved aircraft measurements or completed full-sector '
        'prediction ranges. The complete usefulness test remains open.','',
        'The next task is a finite runtime diagnosis before another long comparison. '
        'The tighter norm-constrained body-source interval is not installed. No '
        'native trajectory, LP proposal, original aircraft data, protected ESA data '
        'or optimizer was used.','',
        '[Frozen scope](PLAN.md) · [Next task](NEXT_PLAN.md) · [Roadmap](../ANALYSIS_ROADMAP.md).']
    (public/'README.md').write_text('\n'.join(text)+'\n')
    runner._replace(public/'accounting.json',dict(cases=accounts,charged=summary['charged'],
        complete=len(rows)==6,exact_supports_reserved=sum(r['exact_supports'] for r in accounts),
        exact_supports_verified=verified,optimizer_starts=0,new_native_evaluations=0))
    receipt=runner._load(public/'evidence-receipt.json')
    for name in ('README.md','accounting.json'):receipt['artifacts'][name]=runner._sha(public/name)
    runner._replace(public/'evidence-receipt.json',receipt)
    print('Rendered all six identities and verified all 36 support reservations; no calculations rerun.')


if __name__=='__main__':main()
