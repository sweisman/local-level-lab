# SPDX-License-Identifier: AGPL-3.0-or-later
"""Render sealed duration/clock results, including failed or unstarted cases."""
import argparse
import math
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_control_shards as runner,ilvis0_control_publication as publication
DATA=ROOT/'data/ilvis0-recording-duration-controls-20261021'
PUBLIC=ROOT/'docs/ilvis0-recording-duration-controls'
PLAN='docs/ilvis0-recording-duration-controls/PLAN.md'


def render(manifest,summary,results):
    tasks=manifest['tasks'];identities=[t['identity'] for t in tasks]
    if (len(tasks)!=6 or len(set(identities))!=6 or not set(results)<=set(identities)
            or summary['completed']!=len(results) or summary['total']!=6
            or summary['charged']['native_calls']>24 or summary['charged']['packet_visits']>2304000
            or summary['charged']['bound_calls'] or summary['charged']['bound_steps']):
        raise ValueError('complete declared task list, saved outcomes and finite charges required')
    for task in tasks:
        row=results.get(task['identity']); spec=task['payload']
        if row is None or not row.get('passed'):continue
        norms=row.get('clock_column_norms',[])
        if (row.get('model')!=spec['model'] or row.get('profile') is not spec['profile']
                or row.get('packets')!=96000 or row.get('query_times_s')!=[438.,478.]
                or row.get('clock_offset_limit_s')!=1. or row.get('physical_parameter_count')!=27
                or row.get('bitwise_api_equivalent') is not True or row.get('native_evaluations')!=4
                or len(norms)!=2 or any(not math.isfinite(v) or v<=0. for v in norms)
                or any(row.get(k)!=0 for k in ('bound_evaluations','original_reads','optimizer_starts'))):
            raise ValueError('saved passing outcome lacks the duration/clock requirements')
    passed=sum(bool(r.get('passed')) for r in results.values());unstarted=6-len(results)
    text=['# Eight-minute input and clock handling','',
        f"{passed}/6 API cases pass; {unstarted} unstarted. Elapsed {summary['elapsed_s']:.2f} seconds.",'',
        'Each generated history contains 96,000 packets, retaining the original four-minute prefix '
        'bit for bit. The new clock-offset bound is ±1 second; all other physical settings are preserved.','',
        '| Candidate | Processing | Saved outcome |','|---|---|---|']
    for task in tasks:
        spec=task['payload'];row=results.get(task['identity'])
        label=('Specified-field globe','Zero-field globe','Flat disc')[spec['model']]
        outcome='Not started' if row is None else 'Exact API agreement' if row.get('passed') else 'Failed'
        text.append(f"| {label} | {'Profiled removal' if spec['profile'] else 'Zero removal'} | {outcome} |")
    text+=['',f"Charged {summary['charged']['native_calls']}/24 native queries, no interval bounds or optimizer starts. "
        'Queries at 438 and 478 seconds retain the complete declared clock support. Passing cases match '
        'positions, all 27 Jacobian columns and warning bits exactly, with nonzero clock derivatives.','',
        'Both callers use the same compiled kernel. This is input/API qualification, '
        'not independent physical validation, useful nonlinear prediction ranges or an established '
        'observation-error law. No aircraft or protected ESA observations enter the study.','',
        'No new numerical work is performed by this saved-only report builder. It preserves the sealed '
        'outcomes and charges. Rebuild with `build_report.py`; `build_report.py --check` verifies publication.','',
        '[Frozen scope](PLAN.md) · [Full-horizon requirements](../ilvis0-three-source-complete/NEXT_PLAN.md).']
    return '\n'.join(text)


def publish():
    manifest=runner.verify(DATA);summary=runner.verify_completion(DATA)
    results={item['identity']:runner._load(DATA/item['artifact'])['result'] for item in summary['results']}
    publication.publish(DATA,PUBLIC,render(manifest,summary,results),plan=PLAN)
    name='rendering.json'
    runner._replace(PUBLIC/name,dict(renderer_sha256=runner._sha(Path(__file__)),
        frozen_numerical_sources_preserved=True,native_calls=0,optimizer_starts=0,
        recording_length_usefulness_qualified=False,observational_coverage_qualified=False))
    receipt=runner._load(PUBLIC/'evidence-receipt.json')
    for item in ('build_report.py',name):receipt['artifacts'][item]=runner._sha(PUBLIC/item)
    runner._replace(PUBLIC/'evidence-receipt.json',receipt)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    if args.check:publication.check(DATA,PUBLIC);print('Verified saved duration/clock publication.')
    else:publish();print('Published saved duration/clock results; no numerical work.')
