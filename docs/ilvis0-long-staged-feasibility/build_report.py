# SPDX-License-Identifier: AGPL-3.0-or-later
"""Publish sealed full-history feasibility evidence without numerical reruns."""
import argparse
import math
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_control_shards as runner, ilvis0_control_publication as publication
from lll.ilvis0_long_staged import limits, recipe
DATA=ROOT/'data/ilvis0-long-staged-feasibility-20261021'
PUBLIC=ROOT/'docs/ilvis0-long-staged-feasibility'
PLAN='docs/ilvis0-long-staged-feasibility/PLAN.md'


def render(manifest, summary, results):
    tasks=manifest['tasks'];identities=[t['identity'] for t in tasks]
    maxima=dict(native_calls=72,packet_visits=6912000,bound_calls=36,bound_steps=31104000)
    if (len(tasks)!=6 or len(set(identities))!=6 or not set(results)<=set(identities)
            or summary['completed']!=len(results) or summary['total']!=6
            or any(summary['charged'][k]>v for k,v in maxima.items())):
        raise ValueError('complete fixed matrix and finite charges required')
    expected=dict(native_evaluations=12,bound_evaluations=6,physical_parameter_count=27,parameter_count=51,
        stages=2,training_epochs=5,inequalities=30,known_truth_retained=True,future_truth_contained=True,
        future_observations_used=False,original_reads=0,optimizer_starts=0)
    for row in results.values():
        if row.get('passed') and not row.get('numerical_checks_passed'):
            raise ValueError('qualification requires complete numerical checks')
        if not row.get('numerical_checks_passed'):continue
        widths=row.get('future_width_m',[]);targets=recipe()['width_target_m']
        if (row.get('work')!=limits() or any(row.get(k)!=v for k,v in expected.items())
                or len(widths)!=3 or any(not math.isfinite(v) or v<0 for v in widths)):
            raise ValueError('numerical claim lacks complete checks or resource accounting')
        useful=all(v<=t for v,t in zip(widths,targets,strict=True))
        if row.get('width_target_m')!=targets or row.get('passed')!=useful or row.get('useful')!=useful:
            raise ValueError('fixed width qualification differs from saved result')
    numerical=sum(bool(r.get('numerical_checks_passed')) for r in results.values())
    passed=sum(bool(r.get('passed')) for r in results.values())
    text=['# Full-history prediction feasibility','',
        f"{numerical}/6 numerical checks complete; {passed}/6 useful predictions. Elapsed {summary['elapsed_s']:.2f} seconds.",'',
        '| Candidate | Processing | Outcome | Total widths N / E / height |',
        '|---|---|---|---:|']
    for task in tasks:
        spec=task['payload'];row=results.get(task['identity'])
        label=('Specified-field globe','Zero-field globe','Flat disc')[spec['model']]
        outcome='Not started' if row is None else ('Pass' if row.get('passed') else
            'Too wide' if row.get('numerical_checks_passed') else 'Failed: '+row.get('reason','unsupported'))
        outcome=outcome.replace('|','/').replace('\n',' ')
        widths=' / '.join(f'{v:.5g}' for v in row['future_width_m'])+' m' if row and row.get('numerical_checks_passed') else 'Unavailable'
        text.append(f"| {label} | {'Profiled removal' if spec['profile'] else 'Zero removal'} | {outcome} | {widths} |")
    text+=['',f"Charged {summary['charged']['native_calls']}/72 native queries, "
        f"{summary['charged']['bound_calls']}/36 bounds and {summary['charged']['bound_steps']}/31,104,000 logical bound steps.",'',
        'The full eight-minute generated inputs and broad 27-parameter domains are retained, including ±1 second '
        'of clock uncertainty. Five training epochs ending at 290 seconds constrain a prediction at 438 seconds. '
        'Both stages retain every earlier inequality. The declared training error is ±1 metre per coordinate.','',
        'The fixed usefulness target is total width ≤20 m north/east and ≤50 m vertically in every case. '
        'It is a development target, not a scientific detection threshold or aircraft accuracy specification. '
        'Future truth is generated only after the prediction is saved.','',
        'These controls use no aircraft observations, protected ESA outcomes or optimizer starts. Even a complete '
        'pass does not establish all later epochs, an observational error law or whole-program floating-point '
        'coverage. Earlier failures remain preserved; no observed prediction fits follow automatically.','',
        '[Frozen calculation and limits](PLAN.md) · [Roadmap](../ANALYSIS_ROADMAP.md).']
    return '\n'.join(text)


def publish():
    manifest=runner.verify(DATA);summary=runner.verify_completion(DATA);results={};accounts=[]
    relative=str(Path(__file__).resolve().relative_to(ROOT))
    if runner._sha(Path(__file__))!=manifest['sources'][relative]:raise ValueError('report source changed')
    for item in summary['results']:
        envelope=runner._load(DATA/item['artifact']);row=envelope['result'];results[item['identity']]=row
        counts=dict.fromkeys(limits(),0)
        for name in sorted(n for n in envelope['artifacts'] if Path(n).name.startswith('reservation-')):
            event=runner._load(DATA/name);inc=event['increase']
            if not inc or any(k not in counts or type(v) is not int or v<1 for k,v in inc.items()):
                raise ValueError('invalid resource reservation')
            counts={k:v+inc.get(k,0) for k,v in counts.items()}
            if counts!=event['counts'] or any(v>limits()[k] for k,v in counts.items()):
                raise ValueError('reservation history changed')
        if row.get('numerical_checks_passed') and (row.get('work')!=counts or counts!=limits()):
            raise ValueError('complete result lacks complete reservations')
        accounts.append(dict(identity=item['identity'],work=counts))
    publication.publish(DATA,PUBLIC,render(manifest,summary,results),plan=PLAN)
    runner._replace(PUBLIC/'accounting.json',dict(cases=accounts,charged=summary['charged'],original_reads=0,
        optimizer_starts=0,observational_coverage_qualified=False))
    receipt=runner._load(PUBLIC/'evidence-receipt.json')
    for name in ('build_report.py','accounting.json'):receipt['artifacts'][name]=runner._sha(PUBLIC/name)
    runner._replace(PUBLIC/'evidence-receipt.json',receipt)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    if args.check:publication.check(DATA,PUBLIC);print('Verified sealed long-history feasibility evidence.')
    else:publish();print('Published sealed long-history feasibility evidence; no numerical work.')
