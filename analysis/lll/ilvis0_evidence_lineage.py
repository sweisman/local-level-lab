# SPDX-License-Identifier: AGPL-3.0-or-later
"""Metadata-only acquisition and execution lineage; never infer missing evidence."""
import collections
import json
import math


def _unique(rows,key):
    result={}
    for row in rows:
        identity=row[key]
        if not identity or identity in result:raise ValueError('missing or duplicate '+key)
        result[identity]=row
    return result


def _removed_events(events):
    prepared={};removed={}
    for event in events:
        identity=event['task_id'];state=event['state']
        if state=='prepared':
            if identity in prepared or identity in removed:raise ValueError('ambiguous prepared cleanup event')
            prepared[identity]=event
        elif state=='removed':
            if identity not in prepared or identity in removed:raise ValueError('removal lacks a unique preceding preparation')
            previous=prepared[identity]
            if any(previous.get(k)!=event.get(k) for k in ('source_sha256','canonical_task_id','reason')):
                raise ValueError('cleanup source or reason changed')
            removed[identity]=event
        else:raise ValueError('unsupported cleanup event state')
    return removed


def reconcile_catalog(*,catalog,inventory,retained,followup,duplicates,selected):
    catalog=_unique(catalog,'task_id');initial=_unique(inventory,'task_id');kept=_unique(retained,'task')
    if set(catalog)!=set(initial):raise ValueError('catalog and original inventory populations differ')
    if not set(kept)<=set(catalog):raise ValueError('retained ledger contains an uncataloged source')
    late=_removed_events(followup);aliases=_removed_events(duplicates)
    if not (set(late)|set(aliases))<=set(catalog):raise ValueError('cleanup references an unknown catalog entry')
    counts=collections.Counter();selected_counts=collections.Counter()
    for stretch in selected:
        task=stretch['task']
        if task not in kept or stretch['source_sha256']!=kept[task]['source_sha256']:
            raise ValueError('selection includes a discarded or mismatched source')
        selected_counts[task]+=1
    output=[]
    for task,record in catalog.items():
        first=initial[task];source=first.get('source_sha256','');original_discard=first['state']=='discarded_no_level'
        if source and (len(source)!=64 or any(c not in '0123456789abcdef' for c in source)):
            raise ValueError('invalid recorded original-byte SHA-256')
        if any(first[k]!=record[k] for k in ('filename','url')):raise ValueError('catalog/inventory source identity changed')
        evidence=[task in kept,original_discard,task in late,task in aliases]
        if sum(evidence)>1:raise ValueError('conflicting storage dispositions')
        state='retained' if task in kept else 'discarded_no_level' if original_discard or task in late else 'duplicate_removed' if task in aliases else 'unresolved'
        counts[state]+=1;canonical=''
        if task in kept:
            row=kept[task]
            if row['filename']!=record['filename'] or row['source_sha256']!=source:raise ValueError('retained source changed')
            if int(row['selected_stretches'])!=selected_counts[task]:raise ValueError('retained selection counts disagree')
        for journal in (late,aliases):
            if task in journal and journal[task]['source_sha256']!=source:raise ValueError('cleanup source hash mismatch')
        if task in aliases:
            canonical=aliases[task]['canonical_task_id']
            if canonical==task or canonical not in kept or kept[canonical]['source_sha256']!=source:
                raise ValueError('duplicate does not match a retained canonical source')
        stage='retained selection ledger' if task in kept else 'initial screening inventory' if original_discard else 'follow-up cleanup journal' if task in late else 'duplicate cleanup journal' if task in aliases else 'missing final storage evidence'
        output.append(dict(record,source_sha256=source,source_bytes=first.get('source_bytes'),initial_screen_state=first['state'],
            recorded_pipeline_storage=state,storage_evidence_stage=stage,canonical_task_id=canonical,
            selected_stretches=selected_counts[task],current_eligibility_state=kept[task]['state'] if task in kept else 'outside_retained_selection_pool',
            selection_version=kept[task].get('selection_version','') if task in kept else '',
            selection_sha256=kept[task].get('selection_sha256','') if task in kept else ''))
    missing_hashes=sum(not r['source_sha256'] for r in output)
    return dict(rows=output,summary=dict(catalog_rows=len(output),storage_counts={k:counts[k] for k in ('retained','discarded_no_level','duplicate_removed','unresolved')},
        initial_no_level_rejections=sum(r['state']=='discarded_no_level' for r in initial.values()),later_no_level_rejections=len(late),
        duplicate_removals=len(aliases),selected_stretches=sum(selected_counts.values()),selected_files=len(selected_counts),
        missing_source_hashes=missing_hashes,complete=counts['unresolved']==0 and missing_hashes==0,
        original_reads=0,originals_deleted=0,downloads=0))


def resolve_owner(identity,candidates,*,interrupted=False):
    exact=[c for c in candidates if identity in c['tasks'] and identity in c['owned_results']]
    if len(exact)==1:return exact[0]
    if len(exact)>1:raise ValueError('ambiguous execution owner with multiple owned results')
    possible=[c for c in candidates if identity in c['tasks']]
    if interrupted and len(possible)==1:return possible[0]
    raise ValueError('execution ownership lacks unique saved evidence')


def validate_published(row,fit,*,interrupted=False):
    if (row['converged']=='True')!=bool(fit.get('converged',False)):raise ValueError('published convergence label changed')
    cost=fit.get('residual_sum_squares');published=row.get('cost')
    if cost is None:
        if published not in ('',None):raise ValueError('published cost has no saved value')
    elif published in ('',None) or not math.isclose(float(published),float(cost),rel_tol=1e-12,abs_tol=1e-12):
        raise ValueError('published cost disagrees with its saved record')
    if json.loads(row.get('parameters') or '{}')!=fit.get('parameters',{}):raise ValueError('published fitted parameters changed')
    if interrupted:
        if row.get('evaluations') not in ('',None):raise ValueError('interrupted evaluation count must remain unasserted')
    elif row.get('evaluations') not in ('',None) and fit.get('evaluations') is not None:
        if int(row['evaluations'])!=int(fit['evaluations']):raise ValueError('published evaluation count changed')
