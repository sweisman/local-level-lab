# SPDX-License-Identifier: AGPL-3.0-or-later
"""Render sealed conditional-remainder controls without numerical evaluation."""
import argparse
import math
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_control_shards as runner,ilvis0_control_publication as publication
from lll.ilvis0_remainder_controls import limits
DATA=ROOT/'data/ilvis0-remainder-native-controls-20261021'
PUBLIC=ROOT/'docs/ilvis0-remainder-native-controls'
PLAN='docs/ilvis0-remainder-native-controls/PLAN.md'


def render(manifest,summary,results):
    tasks=manifest['tasks'];ids=[t['identity'] for t in tasks]
    combinations={(t['payload']['model'],t['payload']['profile'],t['payload']['scope']) for t in tasks}
    expected={(m,p,s) for m in range(3) for p in (False,True) for s in ('physical','conditioned')}
    maxima=dict(native_calls=48,packet_visits=38400,bound_calls=24,bound_steps=172800)
    if (len(tasks)!=12 or len(set(ids))!=12 or combinations!=expected or not set(results)<=set(ids)
            or summary['completed']!=len(results) or summary['total']!=12
            or any(summary['charged'][k]>v for k,v in maxima.items())):
        raise ValueError('complete declared matrix and finite accounting required')
    required=dict(native_evaluations=4,bound_evaluations=2,physical_parameter_count=27,parameter_count=51,
        probe_count=4,all_probes_contained=True,maps_preserved=True,remainders_nonwidening=True,
        force_remainder_reduced=True,original_reads=0,optimizer_starts=0)
    for task in tasks:
        row=results.get(task['identity'])
        if row is None or not row.get('passed'):continue
        if (any(row.get(k)!=v for k,v in required.items()) or row.get('work')!=limits(task['payload']['scope'])
                or not 0<=row.get('conditional_force_remainder',math.inf)<row.get('original_force_remainder',0)):
            raise ValueError('passing component lacks complete qualification evidence')
        for name in ('original_unshared_m','candidate_unshared_m'):
            values=row.get(name,[])
            if len(values)!=3 or any(not math.isfinite(v) or v<0 for v in values):
                raise ValueError('complete finite output radii required')
        if any(a>b for a,b in zip(row['candidate_unshared_m'],row['original_unshared_m'])):
            raise ValueError('claimed nonwidening output widened')
    passed=sum(bool(r.get('passed')) for r in results.values())
    lines=['# Conditional remainder in numerical integration','',
        f"{passed}/12 controls pass; {summary['completed']}/12 completed. Elapsed {summary['elapsed_s']:.2f} seconds.",'',
        '| Model | Processing | Force domain | Outcome | Force remainder, old → new (m/s²) |',
        '|---|---|---|---|---:|']
    for task in tasks:
        spec=task['payload'];row=results.get(task['identity'])
        label=('Specified-field globe','Zero-field globe','Flat disc')[spec['model']]
        state='Not started' if row is None else 'Pass' if row.get('passed') else 'Failed'
        change=f"{row['original_force_remainder']:.5g} → {row['conditional_force_remainder']:.5g}" if row and 'original_force_remainder' in row else 'Unavailable'
        lines.append(f"| {label} | {'Profiled removal' if spec['profile'] else 'Zero removal'} | {spec['scope']} | {state} | {change} |")
    lines+=['',f"Charged {summary['charged']['native_calls']}/48 native queries and {summary['charged']['bound_calls']}/24 bounds.",'',
        'These four-second generated controls preserve all 27 physical directions, 24 shared error columns, '
        'the broad calibration region and ±1-second clock. Passing requires unchanged coefficient maps, '
        'nonwidening bounds and containment of all four fixed known probes.','',
        'This qualifies a short numerical component, not recording-length prediction ranges, an aircraft '
        'observation-error law, whole-program rounding or scientific significance. No aircraft measurements '
        'or protected ESA outcomes are used. Earlier failed bounds and their targets remain unchanged.','',
        '[Frozen scope](PLAN.md) · [Mathematical component](../ilvis0-conditional-remainder/README.md) · '
        '[Requirements before aircraft prediction](../ilvis0-long-staged-feasibility-v2/V01_GATES.md).']
    return '\n'.join(lines)


def publish():
    manifest=runner.verify(DATA);summary=runner.verify_completion(DATA);rows={}
    if runner._sha(Path(__file__))!=manifest['sources'][str(Path(__file__).resolve().relative_to(ROOT))]:
        raise ValueError('report changed from frozen source')
    for item in summary['results']:
        envelope=runner._load(DATA/item['artifact']);row=envelope['result'];rows[item['identity']]=row
        task=next(t for t in manifest['tasks'] if t['identity']==item['identity'])
        maximum=limits(task['payload']['scope']);counts=dict.fromkeys(maximum,0)
        for name in sorted(n for n in envelope['artifacts'] if Path(n).name.startswith('reservation-')):
            event=runner._load(DATA/name);inc=event['increase']
            if not inc or any(k not in counts or type(v) is not int or v<1 for k,v in inc.items()):
                raise ValueError('invalid reservation journal')
            counts={k:v+inc.get(k,0) for k,v in counts.items()}
            if counts!=event['counts'] or any(v>maximum[k] for k,v in counts.items()):
                raise ValueError('reservation accounting mismatch')
        if row.get('passed') and counts!=row['work']:raise ValueError('passing result lacks saved work')
    publication.publish(DATA,PUBLIC,render(manifest,summary,rows),plan=PLAN)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');args=p.parse_args()
    if args.check:publication.check(DATA,PUBLIC);print('Verified conditional-remainder publication.')
    else:publish();print('Published saved conditional-remainder controls; no numerical work.')
