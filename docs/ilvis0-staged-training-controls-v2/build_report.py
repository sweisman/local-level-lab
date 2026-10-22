# SPDX-License-Identifier: AGPL-3.0-or-later
"""Publish sealed staged-native controls without repeating any calculation."""
import argparse
import math
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_control_shards as runner,ilvis0_control_publication as publication
from lll.ilvis0_staged_native_controls_v2 import LIMITS
DATA=ROOT/'data/ilvis0-staged-native-controls-v2-20261021';PUBLIC=ROOT/'docs/ilvis0-staged-training-controls-v2'
PLAN='docs/ilvis0-staged-training-controls-v2/PLAN.md'


def render(manifest,summary,results):
    tasks=manifest['tasks'];identities=[t['identity'] for t in tasks]
    maxima=dict(native_calls=60,packet_visits=1920,bound_calls=30,bound_steps=8640)
    if (len(tasks)!=6 or len(set(identities))!=6 or not set(results)<=set(identities)
            or summary['completed']!=len(results) or summary['total']!=6
            or any(summary['charged'][k]>v for k,v in maxima.items())):
        raise ValueError('declared complete matrix, saved outcomes and finite charges required')
    expected=dict(native_evaluations=10,bound_evaluations=5,physical_parameter_count=27,parameter_count=51,
                  stages=2,training_epochs=4,inequalities=24,known_truth_retained=True,original_reads=0,optimizer_starts=0)
    for row in results.values():
        if not row.get('passed'):continue
        widths=row.get('future_width_m',[])
        if (row.get('work')!=LIMITS or any(row.get(k)!=v for k,v in expected.items())
                or len(widths)!=3 or any(not math.isfinite(v) or v<0. for v in widths)):
            raise ValueError('passing control lacks complete constraints, witness or accounting')
    passed=sum(bool(r.get('passed')) for r in results.values())
    text=['# Staged training: generated software controls','',
        f"{passed}/6 cases pass; elapsed {summary['elapsed_s']:.2f} seconds.",'',
        '| Candidate | Processing | Saved outcome | Future widths N / E / height |',
        '|---|---|---|---:|']
    for task in tasks:
        spec=task['payload'];row=results.get(task['identity'])
        label=('Specified-field globe','Zero-field globe','Flat disc')[spec['model']]
        outcome='Not started' if row is None else 'Pass' if row.get('passed') else 'Failed'
        widths=' / '.join(f'{v:.5g}' for v in row['future_width_m'])+' m' if row and row.get('passed') else 'Unavailable'
        text.append(f"| {label} | {'Profiled removal' if spec['profile'] else 'Zero removal'} | {outcome} | {widths} |")
    text+=['',f"Charged {summary['charged']['native_calls']}/60 native queries, "
        f"{summary['charged']['bound_calls']}/30 bounds and {summary['charged']['bound_steps']}/8,640 logical bound steps.",'',
        'The two training stages retain every earlier inequality and all 27 physical directions. '
        'Passing cases include independent exact prediction-endpoint checks and a feasible known witness '
        'examined after saving the prediction. Native warnings and all reservations are preserved.','',
        'These are 32-packet examples with a 0.13-second prediction and a supplied 1 mm observation allowance. '
        'They check the staged software path, not recording-length usefulness, an observational error law, '
        'whole-program floating-point enclosure or independent physical truth. No aircraft or protected '
        'ESA measurements are used.','',
        '[Frozen scope](PLAN.md) · [Recording-length requirements](../ilvis0-three-source-complete/NEXT_PLAN.md).']
    return '\n'.join(text)


def publish():
    manifest=runner.verify(DATA);summary=runner.verify_completion(DATA);results={};accounts=[]
    relative=str(Path(__file__).resolve().relative_to(ROOT))
    if runner._sha(Path(__file__))!=manifest['sources'][relative]:raise ValueError('report source differs from the freeze')
    for item in summary['results']:
        envelope=runner._load(DATA/item['artifact']);row=envelope['result'];results[item['identity']]=row
        counts=dict.fromkeys(LIMITS,0)
        for name in sorted(n for n in envelope['artifacts'] if Path(n).name.startswith('reservation-')):
            event=runner._load(DATA/name);inc=event['increase']
            if not inc or any(k not in counts or type(v) is not int or v<1 for k,v in inc.items()):
                raise ValueError('invalid staged resource reservation')
            counts={k:v+inc.get(k,0) for k,v in counts.items()}
            if counts!=event['counts'] or any(v>LIMITS[k] for k,v in counts.items()):
                raise ValueError('staged resource accounting changed')
        if row.get('passed') and (row.get('work')!=counts or counts!=LIMITS):
            raise ValueError('passing staged result lacks its complete reservation history')
        accounts.append(dict(identity=item['identity'],work=counts))
    publication.publish(DATA,PUBLIC,render(manifest,summary,results),plan=PLAN)
    runner._replace(PUBLIC/'accounting.json',dict(cases=accounts,charged=summary['charged'],
        original_reads=0,optimizer_starts=0,observational_coverage_qualified=False))
    receipt=runner._load(PUBLIC/'evidence-receipt.json')
    for name in ('build_report.py','accounting.json'):receipt['artifacts'][name]=runner._sha(PUBLIC/name)
    runner._replace(PUBLIC/'evidence-receipt.json',receipt)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    if args.check:publication.check(DATA,PUBLIC);print('Verified saved staged-control publication.')
    else:publish();print('Published sealed staged-control results; no numerical work.')
