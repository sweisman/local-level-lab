# SPDX-License-Identifier: AGPL-3.0-or-later
"""Separate frozen receiver-only audit of the existing six representatives."""
import argparse
import fcntl
import gzip
import json
import os
from pathlib import Path
import shutil

from lll import ilvis0 as il, ilvis0_followup as follow, ilvis0_observation as observation
from lll import ilvis0_gnss as gnss, trimble_observations as decode, runtime


def load(path):
    with gzip.open(path,'rt') if str(path).endswith('.gz') else Path(path).open() as stream:
        return json.load(stream)


def verify_cached(output, task, manifest_digest):
    target=output/(task['task_id']+'.json.gz')
    receipt=output/(task['task_id']+'.receipt.json')
    if not target.exists() or not receipt.exists():
        return None
    cached=load(receipt)
    if cached.get('manifest_sha256')!=manifest_digest or cached.get('report_sha256')!=il.sha256(target):
        raise ValueError('corrupt report or incompatible resume')
    report=load(target)
    if report['task_id']!=task['task_id'] or report['source_sha256']!=task['source_sha256']:
        raise ValueError('cached source identity mismatch')
    for name,digest in report['artifacts_sha256'].items():
        if Path(name).name!=name or il.sha256(output/name)!=digest:
            raise ValueError('corrupt receiver export; no silent regeneration')
    return report


def run(root,output):
    if output.exists() and not (output/'manifest.json').exists():
        raise ValueError('unmarked output directory; use new owned output')
    output.mkdir(parents=True,exist_ok=True)
    with (output/'worker.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        prior=root/'docs/ilvis0-processing-v2-20261007'
        original=load(prior/'manifest.json')
        completion=load(prior/'completion.json')
        for name,key in (('manifest.json','manifest_sha256'),('summary.json.gz','summary_sha256')):
            if il.sha256(prior/name)!=completion[key]:
                raise ValueError('prior evidence hash mismatch')
        reports={r['task_id']:r for r in load(prior/'summary.json.gz')['results']}
        sources=dict(original['sources'])
        for path in (Path(gnss.__file__),Path(decode.__file__),Path(__file__),
                root/'analysis/tests/test_trimble_observations.py',root/'analysis/tests/test_ilvis0_gnss.py'):
            sources[str(path)]=il.sha256(path)
        inputs=dict(original['inputs'])
        for name in ('manifest.json','summary.json.gz','completion.json'):
            inputs[str(prior/name)]=il.sha256(prior/name)
        tasks=original['tasks']
        if len(tasks)!=6:
            raise ValueError('requires the same six representatives')
        manifest=dict(version=gnss.VERSION,sources=sources,inputs=inputs,tasks=tasks,
            environment=runtime.numerical_environment(),references=decode.REFERENCES,
            scope='strict receiver observations, ephemeris/sky geometry and continuity diagnostics; no positioning or Earth fits',
            empirical_earth_fit_attempts=0,scientific_eligibility_changes=0,originals_deleted=0)
        def verify():
            for name,digest in {**sources,**inputs}.items():
                if il.sha256(Path(name))!=digest:
                    raise ValueError('frozen source/input changed')
            if runtime.numerical_environment()!=manifest['environment']:
                raise ValueError('frozen numerical environment changed')
        verify()
        path=output/'manifest.json'
        if path.exists():
            if load(path)!=manifest:
                raise ValueError('source/input/environment mismatch; use a new audit')
            if (output/'completion.json').exists():
                raise ValueError('completed audit is frozen; do not resume')
        else:
            follow.atomic_json(path,manifest)
            snapshots=output/'source-freeze'; snapshots.mkdir()
            for name in sources:
                shutil.copyfile(name,snapshots/Path(name).name)
        results=[]
        for task in tasks:
            verify()
            report=verify_cached(output,task,il.sha256(path))
            if report is None:
                follow.atomic_json(output/'status.json',dict(state='running',pid=os.getpid(),
                    task_id=task['task_id'],completed=len(results)))
                report=gnss.scan(task,reports[task['task_id']],output)
                verify()
                target=output/(task['task_id']+'.json.gz')
                observation.gzip_json(target,report)
                follow.atomic_json(output/(task['task_id']+'.receipt.json'),dict(
                    manifest_sha256=il.sha256(path),report_sha256=il.sha256(target)))
            results.append(report)
            print(json.dumps(dict(task_id=task['task_id'],decoded_epochs=report['decoded_epochs'],
                decoded_signal_epochs=report['decoded_signal_epochs'],boundary_failures=len(report['boundary_failures']))),flush=True)
        summary=dict(version=gnss.VERSION,state='complete',files=len(results),results=results,
            decoded_epochs=sum(r['decoded_epochs'] for r in results),
            decoded_signal_epochs=sum(r['decoded_signal_epochs'] for r in results),
            gps_ephemeris_packets=sum(len(r['gps_ephemerides']) for r in results),
            same_epoch_receiver_positions=sum(r['same_epoch_receiver_positions'] for r in results),
            matched_sky_angle_pairs=sum(r['sky_angle_check']['matched_gps_satellite_epochs'] for r in results),
            source_audit_errors=0,empirical_earth_fit_attempts=0,gnss_position_fits=0,
            scientific_eligibility_changes=0,originals_deleted=0)
        verify()
        observation.gzip_json(output/'summary.json.gz',summary)
        compact={k:v for k,v in summary.items() if k!='results'}
        compact.update(manifest_sha256=il.sha256(path),summary_sha256=il.sha256(output/'summary.json.gz'))
        follow.atomic_json(output/'completion.json',compact)
        follow.atomic_json(output/'status.json',dict(state='complete',pid=os.getpid(),files=len(results)))
        print(json.dumps(compact,sort_keys=True),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=Path('data/ilvis0-gnss-v2-20261007'))
    args=parser.parse_args()
    run(Path(__file__).resolve().parents[2],args.output.resolve())
