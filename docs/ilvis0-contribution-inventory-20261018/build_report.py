# SPDX-License-Identifier: AGPL-3.0-or-later
"""Inventory declared saved primaries; no originals, native predictions or fits."""
import argparse
import csv
import fcntl
import importlib.metadata
import importlib.util
import json
from collections import Counter
from pathlib import Path
import platform
import shutil
import sys

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
OUTPUT=ROOT/'data'/HERE.name
CURRENT=ROOT/'docs/ilvis0-current-findings-20261015'
BASELINE=ROOT/'docs/ilvis0-highspeed-segments-20261008'
sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_artifact_inventory as inventory
from lll.ilvis0_receipt_journal import durable_write,encoded

load,sha=inventory.load,inventory.sha


def write(path,value):durable_write(path,encoded(value),replace=True)


def module(path,name):
    spec=importlib.util.spec_from_file_location(name,path);result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result


def origin_directory(origin):
    names={'original_first_pass':BASELINE,'completed_recovery':ROOT/'docs/ilvis0-position-recovery-20261013',
        'qualified_paired_precision':ROOT/'docs/ilvis0-paired-precision-trial-20261014',
        'completed_cost_precision':ROOT/'docs/ilvis0-cost-precision-recovery-20261014'}
    if origin in names:return names[origin]
    if origin.startswith('completed_ilvis0-'):return ROOT/'docs'/origin.removeprefix('completed_')
    raise ValueError('unsupported current result origin: '+origin)


def render():
    c=load(OUTPUT/'completion.json')
    if c['manifest_sha256']!=sha(OUTPUT/'manifest.json') or c['summary_sha256']!=sha(OUTPUT/'summary.json'):
        raise ValueError('completed inventory changed')
    s=load(OUTPUT/'summary.json');rows=s['rows']
    with (HERE/'inventory.csv').open('w',newline='') as stream:
        fields=list(dict.fromkeys(k for row in rows for k in row));writer=csv.DictWriter(stream,fields,lineterminator='\n')
        writer.writeheader();writer.writerows(rows)
    text='# Saved artifacts for the measurement-contribution study\n\n'
    text+=f"Inventoried **{len(rows)} final primary fits across 53 stretches**, with no original-recording reads, native predictions or new fits. "
    text+='The published model comparisons remain **53 globe / 0 flat / 0 unresolved**. '
    text+='This inventory asks which exact saved arrays can support another diagnostic.\n\n'
    text+='| Artifact disposition | Primary fits |\n|---|---:|\n'
    for status,count in sorted(s['counts'].items()):text+=f'| {status} | {count} |\n'
    text+=f"\n**{s['complete_stretches']} stretches** have all six required saved primary artifacts ready for a matched projection comparison. "
    text+='The [downloadable inventory](inventory.csv) records each authoritative result origin, declared artifact/hash, '
    text+='resolved public copy, array dimensions, time-context checks and any reason preventing reuse.\n\n'
    text+='“Not saved” refers to a residual/Jacobian artifact, not an unfinished model comparison. '
    text+='A missing artifact is never replaced by a lower-cost historical fit or by a repeat. '
    text+='Any later replay at saved parameters needs a separately frozen finite allowance.\n\n'
    text+='The inventory checks receiver layout and a consistent relative-time origin; it does not independently '
    text+='establish the instrument clock. It changes no measurement, interval, parameter or published fit label.\n\n'
    text+='[Finite plan](PLAN.md) · [Measurement-contribution scope](../ilvis0-measurement-contribution/README.md) · '
    text+='[Current findings](../CURRENT_STATUS.md).\n'
    (HERE/'README.md').write_text(text)
    for name in ('manifest.json','summary.json','completion.json'):shutil.copyfile(OUTPUT/name,HERE/name)
    names=('manifest.json','summary.json','completion.json','README.md','inventory.csv','PLAN.md')
    write(HERE/'evidence-receipt.json',dict(artifacts={n:sha(HERE/n) for n in names},original_files_read=0,native_predictions=0,observed_starts=0))


def build():
    current=module(CURRENT/'build_report.py','_contribution_inventory_current')
    status=module(ROOT/'docs/build_current_status.py','_contribution_inventory_status')
    snapshot=status.load_snapshot(ROOT)
    if snapshot['tally']!=dict(globe=53,flat=0,unresolved=0,ambiguous=0):raise ValueError('complete selected corpus required')
    rows=current.verified_rows(ROOT)
    if len(rows)!=53 or len({r['segment_id'] for r in rows})!=53:raise ValueError('exact 53-stretch inventory required')
    selection=load(BASELINE/'selection.json.gz')
    fixes={r['segment']['segment_id']:r['segment']['receiver_fixes'] for r in selection['selected']}
    inputs={};cache={};tasks=[]
    def remember(path):inputs[str(path.relative_to(ROOT))]=sha(path)
    for path in (CURRENT/'findings-receipt.json',CURRENT/'current-stretches.csv',BASELINE/'selection.json.gz',BASELINE/'evidence-receipt.json'):remember(path)
    for row in rows:
        sid=row['segment_id'];directory=origin_directory(row['result_origin'])
        if directory not in cache:
            receipt=load(directory/'evidence-receipt.json')
            name='summary.json.gz' if directory==BASELINE else 'review.json' if (directory/'review.json').is_file() else 'summary.json'
            if sha(directory/name)!=receipt['artifacts'][name]:raise ValueError('authoritative comparison changed')
            data=load(directory/name);manifest=load(directory/'manifest.json') if (directory/'manifest.json').is_file() else {}
            records=data.get('comparisons',data.get('results'))
            if not isinstance(records,list):raise ValueError('unique comparison list required')
            cache[directory]=({r['segment_id']:r for r in records},manifest)
            for filename in (name,'evidence-receipt.json'):
                remember(directory/filename)
            if manifest:remember(directory/'manifest.json')
        comparisons,manifest=cache[directory]
        for case in inventory.CASES:
            for model in inventory.MODELS:
                fit=inventory.primary_fit(comparisons[sid],case,model)
                tasks.append(dict(segment_id=sid,case_id=case,model=model,origin=row['result_origin'],
                    directory=str(directory.relative_to(ROOT)),fit=fit))
    sources={str(p.relative_to(ROOT)):sha(p) for p in (Path(__file__),HERE/'PLAN.md',Path(inventory.__file__),
        ROOT/'analysis/tests/test_ilvis0_artifact_inventory.py',CURRENT/'build_report.py',ROOT/'docs/build_current_status.py')}
    write(OUTPUT/'manifest.json',dict(version=inventory.VERSION,tasks=tasks,inputs=inputs,sources=sources,
        environment=dict(python=platform.python_version(),numpy=importlib.metadata.version('numpy'),scipy=importlib.metadata.version('scipy')),
        maximum_batches=1,maximum_primary_inspections=318,maximum_linearization_reads=318,maximum_epoch_reads=318,
        dense_factorizations=0,singular_decompositions=0,native_predictions=0,observed_starts=0,original_files_read=0,retries=0))
    write(OUTPUT/'start.json',dict(manifest_sha256=sha(OUTPUT/'manifest.json')))
    result=[];artifact_hashes={}
    for task in tasks:
        sid=task['segment_id'];fit=task['fit'];directory=ROOT/task['directory'];manifest=cache[directory][1]
        row={k:task[k] for k in ('segment_id','case_id','model','origin')}
        row.update(source_file=next(r['filename'] for r in rows if r['segment_id']==sid),
            declared_linearization=fit.get('linearization_file',''),declared_sha256=fit.get('linearization_sha256',''),
            primary_cost=fit['residual_sum_squares'],status='not_saved',reason='no_declared_linearization')
        try:
            artifact=inventory.find_artifact(ROOT,directory,fit,manifest,'linearization')
            if artifact is not None:
                row.update(linearization_file=str(artifact.relative_to(ROOT)),linearization_sha256=sha(artifact))
                artifact_hashes[str(artifact.relative_to(ROOT))]=sha(artifact)
                saved=load(artifact);epochs=None
                if 'times_s' not in saved:
                    epoch=inventory.find_artifact(ROOT,directory,fit,manifest,'epoch')
                    if epoch is not None:
                        artifact_hashes[str(epoch.relative_to(ROOT))]=sha(epoch);epochs=load(epoch)
                        row.update(epoch_file=str(epoch.relative_to(ROOT)),epoch_sha256=sha(epoch))
                row.update(inventory.validate_payload(fit,saved,epochs,fixes[sid]),status='ready',reason='')
            elif fit.get('linearization_file'):row.update(status='missing_declared_artifact',reason='declared_digest_not_found_in_publication_or_recorded_inputs')
        except (ValueError,KeyError,TypeError) as error:
            row.update(status='incompatible_saved_artifact',reason=str(error))
        result.append(row)
    if len(result)!=318:raise ValueError('finite primary population changed')
    for name,digest in {**inputs,**sources,**artifact_hashes}.items():
        if sha(ROOT/name)!=digest:raise ValueError('inventory dependency changed')
    complete=sum(all(r['status']=='ready' for r in result if r['segment_id']==sid) for sid in fixes)
    write(OUTPUT/'summary.json',dict(state='complete',rows=result,counts=dict(Counter(r['status'] for r in result)),
        artifact_hashes=artifact_hashes,complete_stretches=complete,primary_inspections=318,native_predictions=0,observed_starts=0,
        original_files_read=0,dense_factorizations=0,singular_decompositions=0,labels_changed=False))
    write(OUTPUT/'completion.json',dict(state='complete',manifest_sha256=sha(OUTPUT/'manifest.json'),summary_sha256=sha(OUTPUT/'summary.json')))
    render();print(json.dumps(dict(counts=Counter(r['status'] for r in result),complete_stretches=complete,primary_inspections=318)))


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--render-only',action='store_true');args=parser.parse_args()
    OUTPUT.mkdir(exist_ok=True)
    with (OUTPUT/'worker.lock').open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (OUTPUT/'completion.json').exists():render();return
        if args.render_only or (OUTPUT/'start.json').exists():raise ValueError('charged inventory cannot restart')
        build()


if __name__=='__main__':main()
