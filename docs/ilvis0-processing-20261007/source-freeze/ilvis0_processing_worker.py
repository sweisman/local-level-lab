# SPDX-License-Identifier: AGPL-3.0-or-later
"""Six frozen representatives, new settings/receiver audit; never Earth fitting."""
import argparse
import fcntl
import gzip
import json
import os
from pathlib import Path
import shutil

from lll import ilvis0 as il, ilvis0_followup as follow, ilvis0_observation as observation
from lll import ilvis0_processing as processing, trimble_receiver as trimble, runtime


def load(path):
    with gzip.open(path,'rt') if str(path).endswith('.gz') else Path(path).open() as stream:
        return json.load(stream)


def run(root, output):
    if output.exists() and not (output/'manifest.json').exists():
        raise ValueError('unmarked audit output; use a new owned directory')
    output.mkdir(parents=True,exist_ok=True)
    with (output/'worker.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        prior = root/'docs/ilvis0-forward-20261007'
        old_manifest = load(prior/'manifest.json')
        old_reports = load(prior/'summary.json.gz')['results']
        observation_reports = {r['task_id']:r for r in load(root/'docs/ilvis0-observation-20261007/summary.json.gz')['results']}
        timing = {r['task_id']:r['timing'] for r in load(root/'docs/ilvis0-followup-20261007/summary.json.gz')['results']}
        ledger = root/'data/ilvis0-ready/records.jsonl'
        records = {r['task_id']:r for r in map(json.loads,ledger.read_text().splitlines())}
        sources = dict(old_manifest['sources'])
        for path in (Path(processing.__file__), Path(trimble.__file__), Path(__file__),
                     root/'analysis/tests/test_ilvis0_processing.py', root/'analysis/lll/ilvis0_assessment.py', Path(runtime.__file__)):
            sources[str(path)] = il.sha256(path)
        inputs = [ledger,prior/'manifest.json',prior/'summary.json.gz',
            root/'docs/ilvis0-observation-20261007/summary.json.gz',root/'docs/ilvis0-followup-20261007/summary.json.gz']
        tasks=[]
        for report in old_reports:
            task=report['task_id']
            path=follow.source_path(root/'data/ilvis0-ready',records[task])
            inputs.append(path)
            if not timing[task]['accepted']:
                raise ValueError('requires accepted dated clock basis; not a guessed leap shift')
            tasks.append(dict(task_id=task,filename=report['filename'],path=str(path),
                source_sha256=report['provenance']['source_sha256'],
                expected_frame_counts=observation_reports[task]['provenance']['frame_counts'],
                leap_seconds=timing[task]['gps_minus_utc_s']))
        if len(tasks)!=6:
            raise ValueError('requires the six existing representatives')
        manifest=dict(version=processing.VERSION,sources=sources,inputs={str(p):il.sha256(p) for p in inputs},
            tasks=tasks,environment=runtime.numerical_environment(),scope='settings/clock/receiver evidence only',
            empirical_earth_fit_attempts=0,scientific_eligibility_changes=0,originals_deleted=0)
        manifest_path=output/'manifest.json'
        def verify():
            for p,digest in {**manifest['sources'],**manifest['inputs']}.items():
                if il.sha256(Path(p))!=digest:
                    raise ValueError('frozen source/input changed')
            if runtime.numerical_environment()!=manifest['environment']:
                raise ValueError('numerical environment changed')
        verify()
        if manifest_path.exists():
            if load(manifest_path)!=manifest:
                raise ValueError('source/input/environment mismatch; use a new identified audit')
            if (output/'completion.json').exists():
                raise ValueError('completed audit is frozen; do not resume')
        else:
            follow.atomic_json(manifest_path,manifest)
            snapshots=output/'source-freeze'
            snapshots.mkdir()
            for p in sources:
                shutil.copyfile(p,snapshots/Path(p).name)
        results=[]
        for task in tasks:
            verify()
            target=output/(task['task_id']+'.json.gz')
            receipt=output/(task['task_id']+'.receipt.json')
            if target.exists() and receipt.exists():
                cached=load(receipt)
                if cached.get('manifest_sha256')!=il.sha256(manifest_path) or cached.get('report_sha256')!=il.sha256(target):
                    raise ValueError('corrupt cached report or incompatible resume')
                report=load(target)
                if report['source_sha256']!=task['source_sha256'] or report['task_id']!=task['task_id']:
                    raise ValueError('cached source identity mismatch')
            else:
                follow.atomic_json(output/'status.json',dict(state='running',pid=os.getpid(),task_id=task['task_id'],completed=len(results)))
                report=processing.scan(Path(task['path']),task['source_sha256'],task['expected_frame_counts'],task['leap_seconds'])
                report.update(task_id=task['task_id'],filename=task['filename'])
                verify()
                observation.gzip_json(target,report)
                follow.atomic_json(receipt,dict(manifest_sha256=il.sha256(manifest_path),report_sha256=il.sha256(target)))
            results.append(report)
        summary=dict(version=processing.VERSION,state='complete',files=len(results),results=results,
            source_audit_errors=0,receiver_stream_errors=sum(len(r['receiver']['stream_errors']) for r in results),
            receiver_page_errors=sum(len(r['receiver']['page_errors']) for r in results),
            files_with_raw_satellite_record_envelopes=sum(r['receiver']['raw_satellite_record_envelopes_present'] for r in results),
            complete_survey_records=sum(sum(r['receiver']['survey_record_counts'].values()) for r in results),
            files_with_GST=sum(bool(r['receiver']['gst']) for r in results),
            empirical_earth_fit_attempts=0,scientific_eligibility_changes=0,originals_deleted=0)
        verify()
        observation.gzip_json(output/'summary.json.gz',summary)
        compact={k:v for k,v in summary.items() if k!='results'}
        compact.update(summary_sha256=il.sha256(output/'summary.json.gz'),manifest_sha256=il.sha256(manifest_path))
        follow.atomic_json(output/'completion.json',compact)
        follow.atomic_json(output/'status.json',dict(state='complete',pid=os.getpid(),files=len(results)))
        print(json.dumps(compact,sort_keys=True))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=Path('data/ilvis0-processing-20261007'))
    args=parser.parse_args()
    run(Path(__file__).resolve().parents[2],args.output.resolve())
