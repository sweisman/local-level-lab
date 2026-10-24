# SPDX-License-Identifier: AGPL-3.0-or-later
"""Metadata-only, outcome-independent development window planning.

This chooses receiver index ranges inside an already verified inventory. It
opens no original measurement, certifies no new support and authorizes no fit.
"""
import math
import re

VERSION='esa-development-first-last-windows-v1'


def plan(inventory,*,previous):
    try:
        receiver=previous['source_references']['receiver']
        valid=(inventory['verified'] is True and previous['verified'] is True
            and inventory['group_id']==previous['group_id']
            and previous['source_references']['imu']['filename']=='187_rqh01.txt'
            and receiver['filename']=='187_air1_ppp_2Hz_final.txt'
            and inventory['source_sha256']==receiver['sha256']
            and isinstance(inventory['source_sha256'],str) and re.fullmatch('[0-9a-f]{64}',inventory['source_sha256']))
        used=(previous['chosen']['first_index'],previous['chosen']['last_index'])
        runs=sorted(inventory['eligible'],key=lambda v:v['first_index'])
        count=inventory['receiver_epochs']
    except (KeyError,TypeError):raise ValueError('verified matching recording-187 metadata required') from None
    if not valid or not 1<=len(runs)<=16 or type(count) is not int or count<2401:
        raise ValueError('verified bounded development metadata required')
    windows=[];skipped=[];prior_end=-1
    for ordinal,run in enumerate(runs,1):
        first,last=run['first_index'],run['last_index']
        if (any(type(v) is not int for v in (first,last,run['epochs'])) or not 0<=first<=last<count
                or first<=prior_end or run['epochs']!=last-first+1 or run['epochs']<2401
                or not math.isfinite(run['duration_s']) or run['duration_s']<1199.5 or run['rejection_reasons']):
            raise ValueError('complete nonoverlapping eligible run metadata required')
        prior_end=last
        for edge,start in (('first',first),('last',last-2400)):
            if edge=='last' and start<=first+2400:
                skipped.append(dict(parent_run=ordinal,edge=edge,reason='last window overlaps the first window'))
                continue
            end=start+2400
            windows.append(dict(window_id=f'187-{start:06d}-{end:06d}',parent_run=ordinal,edge=edge,
                group_id=inventory['group_id'],receiver_source_sha256=inventory['source_sha256'],
                first_index=start,last_index=end,support_epochs=2401,nominal_duration_s=1200.,
                actual_support_not_yet_revalidated=True,query_epochs=1200,query_stride=2,
                query_first_index=start+1,query_last_index=end-1,training_epochs=800,prediction_epochs=400,
                training_last_index=start+1599,prediction_first_index=start+1601,
                already_used_for_development=(start,end)==used))
    if sum(v['already_used_for_development'] for v in windows)!=1:
        raise ValueError('the original used window must remain represented exactly once')
    return dict(version=VERSION,windows=windows,skipped=skipped,
        additional_windows=sum(not v['already_used_for_development'] for v in windows),
        conservative_groups=1,independent_replications=None,original_reads=0,protected_reads=0,
        native_calls=0,fit_starts=0,preparation_authorized=False,confirmation_authorized=False,
        scientific_decision='abstain')


def read_parents(root):
    from lll.studies.closed import ClosedStudy
    from lll.airquantumgrav_inventory import validate_context,METADATA
    from lll.studies.artifacts import ArchiveStore
    result={};proof={}
    for key,prefix in [('inventory','docs/esa-development-selection-v2'),('previous','docs/esa-development-pilot-preparation')]:
        study=ClosedStudy(root,prefix)
        try:
            receipt=study.read('evidence-receipt.json');name='artifacts/publication/verified-report.json'
            report=study.read(name,receipt['artifacts'][name])
            if (report['verified'] is not True or report['manifest_sha256']!=study.completion['manifest_sha256']
                    or report['summary_sha256']!=study.completion['summary_sha256']):
                raise ValueError('verified closed metadata reports required')
            if key=='previous':
                context={k:study.input(k) for k in METADATA}
                store=ArchiveStore(root)
                try:
                    import json
                    for k in ('groups','reservation'):context[k]=json.loads(store.read(METADATA[k]))
                finally:store.close()
                if validate_context(**context)!=study.input('context'):
                    raise ValueError('current development membership differs from the prepared source')
            result[key]=report
            proof[key]=dict(path=prefix,manifest_sha256=report['manifest_sha256'],summary_sha256=report['summary_sha256'],
                verified_report_sha256=receipt['artifacts'][name])
        finally:study.close()
    return dict(result,parents=proof)


def qualification_sources(root):
    from lll.studies.dependencies import source_closure
    return source_closure(root,['analysis/lll/airquantumgrav_window_plan.py',
        'analysis/tests/test_airquantumgrav_window_plan.py','docs/esa-broader-development/PLAN.md'])


def environment():
    import sys
    return dict(python=sys.version,scope='metadata-only planning; zero numerical allocation')


def freeze(root,*,qualification,output='docs/esa-broader-development'):
    if qualification is None:raise ValueError('source-bound metadata qualification required')
    import csv
    import io
    import json
    from pathlib import Path
    from lll.studies.qualification import checked
    from lll.studies.artifacts import atomic,digest,encoded,safe_path
    root=Path(root).resolve();public=safe_path(root,output)
    if (public/'evidence-receipt.json').exists():raise ValueError('window plan already sealed')
    request,tests=checked(root,qualification,sources=qualification_sources(root),environment=environment(),minimum_tests=12,
        required_tests=['test_window_plan_selects_fixed_first_last_support_and_marks_already_used_window',
            'test_window_plan_is_order_invariant_and_cannot_use_gyro_or_fit_outcomes',
            'test_window_freeze_requires_qualification_before_reading_parents_or_writing'])
    parents=read_parents(root);result=plan(parents['inventory'],previous=parents['previous'])
    document=dict(plan=result,parents=parents['parents'],environment=environment())
    table=io.StringIO();writer=csv.DictWriter(table,fieldnames=list(result['windows'][0]));writer.writeheader();writer.writerows(result['windows'])
    files={'windows.json':encoded(document),'windows.csv':table.getvalue().encode(),
        'evidence/inventory-report.json':encoded(parents['inventory']),
        'evidence/previous-preparation-report.json':encoded(parents['previous']),
        'evidence/qualification-request.json':request,'evidence/qualification-report.xml':tests,
        'evidence/window-planner.py':Path(__file__).read_bytes(),
        'PLAN.md':(root/'docs/esa-broader-development/PLAN.md').read_bytes()}
    lines=['# Three more development intervals','',
        '**The metadata rule selects four nonoverlapping twenty-minute ranges.** One has already been analyzed;',
        'three are additional candidates. These all belong to the same ESA development group, not independent replications.','',
        'Take the first and last twenty minutes of each of the two eligible full-motion runs. The original receiver',
        'inventory stays unchanged. No gyro value or model result enters the choice.','',
        '| Parent run | Part | Status | Receiver support indices |',
        '|---|---|---|---|']
    for row in result['windows']:
        lines.append(f"| {row['parent_run']} | {row['edge'].capitalize()} twenty minutes | "
            +('Already analyzed' if row['already_used_for_development'] else 'Candidate; not prepared')
            +f" | {row['first_index']}–{row['last_index']} |")
    lines+=['', 'Indices identify original receiver records; they are not interpolated time estimates.',
        'Each candidate keeps 800 earlier training queries and 400 later prediction queries.',
        'Exact timing, IMU support, source hashes and trajectory summaries still need their own preparation checks.',
        'No original recording is opened, and no fit or native calculation runs in this planning step.','',
        'Preparation and fitting wait for the preceding error-assumption assessment and their separately qualified',
        'finite definitions. These ranges are not confirmation data. All seven confirmation groups remain protected.','',
        '[Selected ranges CSV](windows.csv) · [Selection rules](PLAN.md) ·',
        '[Parent inventory](../esa-development-selection-v2/README.md) · [Next analyses](../NEXT_STEPS.md)']
    files['README.md']=('\n'.join(lines)+'\n').encode()
    receipt=dict(version=VERSION,artifacts={name:digest(raw) for name,raw in files.items()},parents=parents['parents'])
    for name,raw in files.items():atomic(public/name,raw)
    atomic(public/'evidence-receipt.json',encoded(receipt))
    return check(root,output)


def check(root,prefix='docs/esa-broader-development'):
    import csv
    import json
    from pathlib import Path
    from lll.studies.artifacts import digest,encoded,safe_path
    from lll.studies.closed import load_python_reference
    root=Path(root).resolve();public=safe_path(root,prefix);receipt=json.loads((public/'evidence-receipt.json').read_bytes())
    for name,sha in receipt['artifacts'].items():
        if digest(safe_path(public,name).read_bytes())!=sha:raise ValueError('window planning artifact changed: '+name)
    request=json.loads((public/'evidence/qualification-request.json').read_bytes())
    source=(public/'evidence/window-planner.py').read_bytes();sha=request['sources']['analysis/lll/airquantumgrav_window_plan.py']
    module=load_python_reference(source,name='lll._window_plan_'+sha,sha256=sha)
    inventory=json.loads((public/'evidence/inventory-report.json').read_bytes())
    previous=json.loads((public/'evidence/previous-preparation-report.json').read_bytes())
    document=json.loads((public/'windows.json').read_bytes())
    if encoded(module.plan(inventory,previous=previous))!=encoded(document['plan']) or document['parents']!=receipt['parents']:
        raise ValueError('window selection or parent bindings changed')
    with (public/'windows.csv').open(newline='') as stream:table=list(csv.DictReader(stream))
    if table!=[{k:str(v) for k,v in row.items()} for row in document['plan']['windows']]:
        raise ValueError('window CSV differs from the frozen index ranges')
    if digest((public/'PLAN.md').read_bytes())!=request['sources']['docs/esa-broader-development/PLAN.md']:
        raise ValueError('window selection rule changed')
    return dict(verified=True,windows=len(document['plan']['windows']),additional_windows=document['plan']['additional_windows'],
        artifact_hashes_verified=len(receipt['artifacts']),original_reads=0,protected_reads=0,native_calls=0,fit_starts=0)
