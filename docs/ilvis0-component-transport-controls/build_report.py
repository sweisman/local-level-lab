# SPDX-License-Identifier: AGPL-3.0-or-later
"""Render the terminal transport outcome from sealed metadata; no calculations."""
from collections import defaultdict
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_control_shards as runner
from lll import ilvis0_control_publication as publication


def main():
    public=Path(__file__).parent;data=ROOT/'data/ilvis0-component-transport-controls-20261020'
    publication.check(data,public);summary=runner.verify_completion(data);manifest=runner.verify(data)
    groups=defaultdict(list);failed=[]
    for record in summary['results']:
        row=runner._load(data/record['artifact'])['result']
        task=next(t for t in manifest['tasks'] if t['identity']==record['identity'])
        groups[task['payload']['kind']].append(row.get('passed',False))
        if not row.get('passed',False):failed.append((record['identity'],row.get('reason','incomplete check')))
    text=['# Coordinate-preserving native transport','',
        f"**Qualification failed: {sum(sum(v) for v in groups.values())}/24 controls passed.**",'',
        'Four broad globe controls reached the unchanged 60-second limit per bound. '
        'The completed checks retained the original centers, derivative limits, '
        'stationary-motion criteria and nonlinear-containment rules. The failed '
        'controls remain failed; the study will not be restarted.','',
        '| Check | Passed | Total |','|---|---:|---:|']
    for kind,rows in groups.items():text.append(f'| {kind.capitalize()} | {sum(rows)} | {len(rows)} |')
    text+=['',f"The study used {summary['charged']['native_calls']}/78 native evaluations, "
        f"{summary['charged']['bound_calls']}/348 charged bounds and {summary['charged']['bound_steps']}/15,072 "
        f"bound packet-steps. Elapsed time: {summary['elapsed_s']:.2f} seconds.",'',
        'The candidate carries separate coordinate bounds through forces, velocity '
        'and coordinate extraction while preserving useful norm bounds. It does '
        'not yet install the tighter norm-constrained body-source interval. '
        'The next task is to reduce repeated exact-arithmetic validation without '
        'changing the mathematical bounds or time limits.','',
        'No aircraft data, protected ESA data or observed fit was used. Full '
        'propagation qualification, prediction usefulness and observational '
        'coverage remain separate gates.','',
        '## Unfinished controls','', '| Identity | Reason |','|---|---|']
    text += [f'| {identity} | {reason} |' for identity,reason in failed]
    text+=['','[Frozen scope](PLAN.md) · [Interpretation](INTERPRETATION.md) · [Next task](NEXT_PLAN.md) · [Roadmap](../ANALYSIS_ROADMAP.md).']
    (public/'README.md').write_text('\n'.join(text)+'\n')
    receipt=runner._load(public/'evidence-receipt.json')
    receipt['artifacts']['README.md']=runner._sha(public/'README.md')
    runner._replace(public/'evidence-receipt.json',receipt)
    print('Rendered terminal transport outcome from sealed results only.')


if __name__=='__main__':main()
