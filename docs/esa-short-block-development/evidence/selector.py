# SPDX-License-Identifier: AGPL-3.0-or-later
"""Freeze short withheld blocks from already selected ESA development metadata."""

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path

VERSION='esa-development-short-block-v1'
PARENT='docs/esa-broader-development'
OUTPUT='docs/esa-short-block-development'
REQUEST=OUTPUT+'/qualification-request.json'
REPORT=OUTPUT+'/qualification-tests.xml'


def qualification_sources(root):
    from .studies.dependencies import source_closure
    return source_closure(Path(root).resolve(),[
        'analysis/lll/esa_short_block_plan.py',
        'analysis/tests/test_esa_short_block_plan.py',
        OUTPUT+'/PLAN.md'])


def environment():
    import sys
    return dict(python=sys.version,scope='metadata-only short-block selection')


def request_qualification(root):
    from .studies.qualification import request
    root=Path(root).resolve()
    return request(root,sources=qualification_sources(root),
                   environment=environment(),output=REQUEST,report=REPORT)


def select(parent):
    plan=parent.get('plan') if isinstance(parent,dict) else None
    if (not isinstance(plan,dict) or
            plan.get('version')!='esa-development-first-last-windows-v1' or
            plan.get('additional_windows')!=3 or
            plan.get('preparation_authorized') is not False or
            plan.get('confirmation_authorized') is not False):
        raise ValueError('unchanged frozen development-window selection required')
    windows=plan.get('windows')
    if not isinstance(windows,list) or len(windows)!=4:
        raise ValueError('four complete parent windows required')
    used=[row for row in windows if row.get('already_used_for_development') is True]
    selected=[row for row in windows if row.get('already_used_for_development') is False]
    if len(used)!=1 or len(selected)!=3:
        raise ValueError('one prior and three additional windows required')
    result=[];intervals=[];groups=set()
    for row in selected:
        first=row.get('first_index');last=row.get('last_index')
        query=row.get('query_first_index')
        if (type(first) is not int or type(last) is not int or
                type(query) is not int or last-first!=2400 or query!=first+1 or
                row.get('query_last_index')!=last-1 or
                row.get('query_stride')!=2 or row.get('query_epochs')!=1200 or
                row.get('training_epochs')!=800 or row.get('prediction_epochs')!=400 or
                row.get('support_epochs')!=2401 or
                row.get('actual_support_not_yet_revalidated') is not True or
                not isinstance(row.get('receiver_source_sha256'),str) or
                len(row['receiver_source_sha256'])!=64):
            raise ValueError('complete fixed twenty-minute parent support required')
        intervals.append((first,last));groups.add(row.get('group_id'))
        result.append(dict(window_id=row['window_id'],parent_run=row['parent_run'],
            edge=row['edge'],group_id=row['group_id'],
            receiver_source_sha256=row['receiver_source_sha256'],
            original_first_index=first,original_last_index=last,
            training_first_index=query,training_last_index=query+2*799,
            future_first_index=query+2*800,future_last_index=query+2*919,
            query_stride=2,training_reports=800,future_reports=120,
            unused_parent_queries=280,original_reads=0,protected_reads=0,
            fit_starts=0))
    intervals.sort()
    if (len(groups)!=1 or None in groups or
            any(right[0]<=left[1] for left,right in zip(intervals,intervals[1:])) or
            any(row['future_last_index']>=row['original_last_index'] for row in result)):
        raise ValueError('distinct nonoverlapping development windows required')
    return dict(version=VERSION,windows=result,window_count=3,
        conservative_groups=1,independent_replications=None,
        selection_basis='previously frozen receiver-only windows; generated 120-second horizon',
        preparation_authorized=False,fit_authorized=False,
        confirmation_authorized=False,original_reads=0,protected_reads=0,
        native_calls=0,scientific_decision='abstain')


def build(root):
    from .airquantumgrav_window_plan import check as check_parent
    from .studies.artifacts import digest
    root=Path(root).resolve()
    checked=check_parent(root)
    if checked['verified'] is not True or checked['windows']!=4:
        raise ValueError('sealed parent development plan required')
    parent_raw=(root/PARENT/'windows.json').read_bytes()
    parent_receipt=(root/PARENT/'evidence-receipt.json').read_bytes()
    plan=select(json.loads(parent_raw))
    return dict(plan=plan,parent_window_sha256=digest(parent_raw),
        parent_receipt_sha256=digest(parent_receipt),
        selector_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        plan_sha256=digest((root/OUTPUT/'PLAN.md').read_bytes()))


def publish(root,*,qualification=None):
    from .studies.artifacts import atomic,digest,encoded
    from .studies.qualification import checked
    root=Path(root).resolve();base=root/OUTPUT
    if qualification is None:
        raise ValueError('passing source-bound qualification required')
    if (base/'receipt.json').exists():
        raise ValueError('short-block selection already frozen')
    request_raw,tests_raw=checked(root,qualification,
        sources=qualification_sources(root),environment=environment(),
        required_tests=('test_short_block_selects_all_three_without_outcomes',
                        'test_short_block_rejects_changed_parent'),
        minimum_tests=3)
    document=build(root)
    rows=document['plan']['windows']
    table=io.StringIO();writer=csv.DictWriter(table,fieldnames=list(rows[0]))
    writer.writeheader();writer.writerows(rows)
    lines=['# Three short-block development windows','',
        'Three previously selected twenty-minute windows from recording 187',
        'now each have **800 training reports and 120 future reports**. All three',
        'belong to one development flight group; none is independent confirmation.','',
        '| Parent run | Part | Original receiver indices | Future query indices |',
        '| --- | --- | ---: | ---: |']
    for row in rows:
        lines.append(f"| {row['parent_run']} | {row['edge']} | "
            f"{row['original_first_index']}–{row['original_last_index']} | "
            f"{row['future_first_index']}–{row['future_last_index']} |")
    lines+=['','The selection uses only the frozen receiver-window metadata and',
        'a 120-second horizon chosen from generated uncertainty calculations.',
        'It opens no measurement, certifies no sample support, starts no fit and',
        'does not change the original 400-report failure. Error-law and physical',
        'prediction gates still apply before any fit. Seven ESA confirmation',
        'groups remain sealed.','',
        '[Selection CSV](selection.csv) · [Policy](PLAN.md) ·',
        '[Parent windows](../esa-broader-development/README.md) ·',
        '[Next analyses](../NEXT_STEPS.md).']
    files={'selection.json':encoded(document),
           'selection.csv':table.getvalue().encode(),
           'README.md':('\n'.join(lines)+'\n').encode(),
           'evidence/selector.py':Path(__file__).read_bytes(),
           'evidence/parent-windows.json':(root/PARENT/'windows.json').read_bytes(),
           'evidence/parent-receipt.json':(root/PARENT/'evidence-receipt.json').read_bytes(),
           'evidence/qualification-request.json':request_raw,
           'evidence/qualification-report.xml':tests_raw}
    receipt=dict(version=VERSION,artifacts={name:digest(raw)
                 for name,raw in files.items()},
                 parent_window_sha256=document['parent_window_sha256'],
                 parent_receipt_sha256=document['parent_receipt_sha256'],
                 plan_sha256=document['plan_sha256'])
    for name,raw in files.items():atomic(base/name,raw)
    atomic(base/'receipt.json',encoded(receipt))
    return verify(root)


def verify(root):
    from .studies.artifacts import digest
    from .studies.closed import load_python_reference
    root=Path(root).resolve();base=root/OUTPUT
    receipt=json.loads((base/'receipt.json').read_bytes())
    if receipt['version']!=VERSION:
        raise ValueError('different short-block receipt')
    for name,sha in receipt['artifacts'].items():
        if digest((base/name).read_bytes())!=sha:
            raise ValueError('short-block artifact changed: '+name)
    doc=json.loads((base/'selection.json').read_bytes())
    parent_raw=(base/'evidence/parent-windows.json').read_bytes()
    source=(base/'evidence/selector.py').read_bytes()
    frozen=load_python_reference(source,
        name='lll._esa_short_block_'+digest(source),sha256=doc['selector_sha256'])
    if (doc['plan']!=frozen.select(json.loads(parent_raw)) or
            digest(parent_raw)!=receipt['parent_window_sha256'] or
            digest((base/'evidence/parent-receipt.json').read_bytes())!=
                receipt['parent_receipt_sha256'] or
            digest((base/'PLAN.md').read_bytes())!=receipt['plan_sha256']):
        raise ValueError('short-block selection or parent changed')
    return dict(verified=True,windows=3,training_reports=800,
        future_reports=120,original_reads=0,protected_reads=0,
        native_calls=0,fit_starts=0,scientific_decision='abstain')


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('request','publish','verify'))
    parser.add_argument('--root',default='.')
    args=parser.parse_args(argv)
    result=(request_qualification(args.root) if args.action=='request' else
            publish(args.root,qualification=REQUEST) if args.action=='publish'
            else verify(args.root))
    print(json.dumps(result,sort_keys=True))


if __name__=='__main__':main()
