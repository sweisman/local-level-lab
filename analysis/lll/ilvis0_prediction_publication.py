# SPDX-License-Identifier: AGPL-3.0-or-later
"""Closed-study prediction reports; standard-library metadata operations only."""
import json
import math
from pathlib import Path

from .studies.artifacts import ArchiveStore,digest,encoded


def inspect(root,prefix):
    store=ArchiveStore(root);catalog=store.catalog()
    def read(name,expected=None):
        raw=store._read(prefix+'/'+name,catalog)
        if expected is not None and digest(raw)!=expected:raise ValueError('closed evidence hash mismatch: '+name)
        return json.loads(raw)
    try:completion=read('completion.json')
    except FileNotFoundError as error:raise ValueError('closed study required before reporting') from error
    manifest=read('manifest.json',completion['manifest_sha256'])
    summary=read('summary.json',completion['summary_sha256'])
    if completion['state'] not in ('complete','terminal') or summary['state']!=completion['state']:
        raise ValueError('matching closed completion and summary required')
    tasks=manifest['tasks']
    matrix={(t['payload']['model'],t['payload']['profile']) for t in tasks}
    if (len(tasks)!=6 or len({t['identity'] for t in tasks})!=6
            or matrix!={(m,p) for m in range(3) for p in (False,True)}
            or any(type(t['payload']['profile']) is not bool or
                t['payload']['width_target_m']!=[20.,20.,50.] for t in tasks)):
        raise ValueError('complete six-case model and processing matrix required')
    results={r['identity']:r for r in summary['results']}
    if (len(results)!=len(summary['results']) or not set(results)<={t['identity'] for t in tasks}
            or summary['total']!=6 or summary['completed']!=len(results)
            or summary['passed']!=(len(results)==6 and all(r['passed'] for r in results.values()))
            or (summary['state']=='complete')!=summary['passed']):
        raise ValueError('closed outcome counts or identities differ')
    cases=[]
    for task in sorted(tasks,key=lambda t:(t['payload']['model'],t['payload']['profile'])):
        spec=task['payload'];identity=task['identity'];item=results.get(identity)
        result=None
        if item is not None:
            envelope=read(item['artifact'],item['artifact_sha256']);result=envelope['result']
            if (envelope['identity']!=identity or envelope['manifest_sha256']!=completion['manifest_sha256']
                    or digest(encoded(result))!=envelope['result_sha256'] or item['passed']!=result['passed']):
                raise ValueError('closed result identity or hash differs')
            for name,sha in envelope['artifacts'].items():
                if digest(store._read(prefix+'/'+name,catalog))!=sha:raise ValueError('closed artifact hash mismatch: '+name)
        checked=result is not None and result.get('numerical_checks_passed') is True
        widths=result.get('future_width_m') if result is not None else None
        prior=result.get('previous_width_m') if result is not None else None
        for values in (widths,prior):
            if values is not None and (len(values)!=3 or any(not math.isfinite(v) or v<0 for v in values)):
                raise ValueError('three finite nonnegative reported widths required')
        if checked:
            if (result['model']!=spec['model'] or result['profile']!=spec['profile'] or widths is None
                    or result['width_target_m']!=spec['width_target_m']
                    or result['useful']!=all(w<=t for w,t in zip(widths,spec['width_target_m'],strict=True))
                    or result['passed']!=result['useful']):
                raise ValueError('reported endpoint gate differs from its frozen definition')
        useful=checked and result['useful'] is True
        status=('No completed calculation' if result is None else 'Rejected' if not checked
            else 'Endpoint target passed' if useful else 'Checks passed; ranges too wide')
        cases.append(dict(identity=identity,model=spec['model'],profile=spec['profile'],
            numerical_checks=checked,useful=useful,previous_width_m=prior,future_width_m=widths,status=status))
    return dict(prefix=prefix,state=summary['state'],cases=cases,total=6,completed=len(results),
        numerical_checks=sum(c['numerical_checks'] for c in cases),useful_cases=sum(c['useful'] for c in cases),
        elapsed_s=summary['elapsed_s'],reserved_bounds=summary['charged']['bound_calls'],
        manifest_sha256=completion['manifest_sha256'],summary_sha256=completion['summary_sha256'])


def render(report):
    useful=report['useful_cases'];checked=report['numerical_checks']
    labels=('Globe, specified field','Globe, zero field','Flat disc')
    def widths(values):
        return 'Unavailable' if values is None else ' / '.join(f'{v:,.3f}'.rstrip('0').rstrip('.') for v in values)
    lines=['# Full-history prediction comparison','',
        f'**{useful}/6 endpoint targets passed; {checked}/6 numerical checks passed.**',
        ('All six generated endpoints meet their frozen width targets.' if useful==6 else
         'The long-history prediction method remains unqualified.'),'',
        'These are generated software cases. They test the prediction-bound method,',
        'not which physical model the aircraft measurements support. Passing requires',
        'both the numerical checks and useful ranges: at most 20 m north, 20 m east',
        'and 50 m in height. A wide range fails even if it contains the known answer.','',
        '| Candidate | Removal assumption | Previous N / E / height, m | New N / E / height, m | Outcome |',
        '|---|---|---|---|---|']
    for case in report['cases']:
        lines.append('| '+ ' | '.join((labels[case['model']],'Profiled' if case['profile'] else 'None',
            widths(case['previous_width_m']),widths(case['future_width_m']),case['status']))+' |')
    lines+=['','Displayed widths are rounded for readability; the sealed results preserve',
        'their full precision. Rejected or incomplete cases remain in the table.',
        'The calculation reuses the saved training observations, constraints and',
        'baseline trajectory values and Jacobians. It changes neither the physical calibration limits nor',
        'the original shared-coordinate normalization.','',
        f'The closed comparison records {report["completed"]}/6 completed outcomes and',
        f'{report["reserved_bounds"]} reserved bounds over {report["elapsed_s"]/3600:.2f} wall hours.',
        'There are no new aircraft fits or baseline trajectory-oracle queries;',
        'the interval-bound source streams are recomputed.','',
        'The 53-stretch model comparisons are unchanged. Even a complete endpoint',
        'pass would leave whole-period coverage, numerical treatment and the aircraft',
        'observation-error model to be qualified before new withheld-position fits.','',
        '[Method and limits](PLAN.md) ·',
        '[Original long-history result](../ilvis0-long-staged-feasibility-v2/README.md) ·',
        '[Prediction requirements](../ilvis0-long-staged-feasibility-v2/V01_GATES.md) ·',
        '[Reproducibility](../REPRODUCIBILITY.md).','']
    return '\n'.join(lines)


def publish(root,prefix,output,*,plan):
    """Package closed evidence and archive the renderer beside its output."""
    from .ilvis0_control_publication import publish as package
    from .studies.artifacts import atomic,safe_path
    from .studies.publication import archive_publication
    root=Path(root).resolve();data=safe_path(root,prefix);public=safe_path(root,output)
    if (public/'evidence-receipt.json').exists():raise ValueError('publication already sealed; verify or render only')
    report=inspect(root,prefix);package(data,public,render(report),plan=plan)
    receipt=json.loads((public/'evidence-receipt.json').read_text())
    source='artifacts/publication/renderer.py';source_bytes=Path(__file__).read_bytes()
    atomic(public/source,source_bytes)
    provenance='artifacts/publication/report-provenance.json'
    metadata=encoded(dict(renderer_sha256=digest(source_bytes),manifest_sha256=report['manifest_sha256'],
        summary_sha256=report['summary_sha256'],renderer_module='lll.ilvis0_prediction_publication',
        renderer_package_path='analysis/lll/ilvis0_prediction_publication.py',numerical_work=0))
    atomic(public/provenance,metadata)
    receipt['artifacts'].update({source:digest(source_bytes),provenance:digest(metadata)})
    atomic(public/'evidence-receipt.json',encoded(receipt))
    return dict(archive_publication(root,data,public),published=output,useful_cases=report['useful_cases'],numerical_work=0)
