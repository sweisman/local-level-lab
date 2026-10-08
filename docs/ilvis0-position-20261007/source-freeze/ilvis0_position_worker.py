# SPDX-License-Identifier: AGPL-3.0-or-later
"""Receiver-only code positioning at frozen GPS epochs; no IMU/Earth fitting."""
import argparse
import fcntl
import gzip
import json
import os
from pathlib import Path
import shutil

from lll import ilvis0 as il, ilvis0_followup as follow, ilvis0_observation as observation
from lll import ilvis0_position as position, gnss_position as gps, runtime
from ilvis0_gnss_worker import verify_cached


def load(path):
    with gzip.open(path,'rt') if str(path).endswith('.gz') else Path(path).open() as stream:
        return json.load(stream)


def run(root,output):
    if output.exists() and not (output/'manifest.json').exists():
        raise ValueError('unmarked output; use a separately identified directory')
    output.mkdir(parents=True,exist_ok=True)
    with (output/'worker.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        prior=root/'docs/ilvis0-gnss-v2-20261007'
        old=load(prior/'manifest.json'); old_summary=load(prior/'summary.json.gz')
        completion=load(prior/'completion.json')
        for name,key in (('manifest.json','manifest_sha256'),('summary.json.gz','summary_sha256')):
            if il.sha256(prior/name)!=completion[key]:
                raise ValueError('prior decoder evidence hash mismatch')
        reports={r['task_id']:r for r in old_summary['results']}
        context=root/'docs/ilvis0-processing-v2-20261007'
        context_completion=load(context/'completion.json')
        if il.sha256(context/'summary.json.gz')!=context_completion['summary_sha256']:
            raise ValueError('prior receiver context hash mismatch')
        references={r['task_id']:r['receiver']['gsof_records'] for r in load(context/'summary.json.gz')['results']}
        sources=dict(old['sources'])
        for path in (Path(gps.__file__),Path(position.__file__),Path(__file__),
                root/'analysis/tests/test_gnss_position.py',root/'analysis/tests/test_ilvis0_position.py'):
            sources[str(path)]=il.sha256(path)
        inputs=dict(old['inputs'])
        for path in (prior/'manifest.json',prior/'summary.json.gz',prior/'completion.json',
                context/'summary.json.gz',context/'completion.json'):
            inputs[str(path)]=il.sha256(path)
        measurement_directory=root/'data/ilvis0-gnss-v2-20261007'
        for report in reports.values():
            for name,digest in report['artifacts_sha256'].items():
                inputs[str(measurement_directory/name)]=digest
        tasks=old['tasks']
        target_epochs=sum(len(references[t['task_id']]) for t in tasks)
        if len(tasks)!=6 or target_epochs!=2968:
            raise ValueError('requires six frozen representatives and 2968 receiver epochs')
        manifest=dict(version=position.VERSION,sources=sources,inputs=inputs,tasks=tasks,
            environment=runtime.numerical_environment(),references=gps.REFERENCES,
            target_epochs=target_epochs,methods=list(position.METHODS),
            primary_position_fit_calls=2*target_epochs,alternate_seed_fit_calls=4*len(tasks),
            iterations_per_solve=12,elevation_mask_deg=5.,relative_humidity=.5,
            selection='all previously dated GSOF epochs, matched without interpolation; no residual-driven selection',
            scope='GPS-only conventional code positioning and uncertainty consistency; not an Earth-model comparison',
            empirical_earth_fit_attempts=0,scientific_eligibility_changes=0,originals_deleted=0)
        def verify():
            for name,digest in {**sources,**inputs}.items():
                if il.sha256(Path(name))!=digest:
                    raise ValueError('frozen source/input changed')
            if runtime.numerical_environment()!=manifest['environment']:
                raise ValueError('numerical environment changed')
        verify(); path=output/'manifest.json'
        if path.exists():
            if load(path)!=manifest:
                raise ValueError('source/input/environment mismatch; use new freeze')
            if (output/'completion.json').exists():
                raise ValueError('completed positioning check is frozen; do not resume')
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
                report=position.run_file(task,reports[task['task_id']],references[task['task_id']],measurement_directory,output)
                verify()
                target=output/(task['task_id']+'.json.gz')
                observation.gzip_json(target,report)
                follow.atomic_json(output/(task['task_id']+'.receipt.json'),dict(
                    manifest_sha256=il.sha256(path),report_sha256=il.sha256(target)))
            results.append(report)
            print(json.dumps(dict(task_id=task['task_id'],primary=report['primary_solutions'],
                converged={method:summary['converged'] for method,summary in report['method_summaries'].items()})),flush=True)
        summary=dict(version=position.VERSION,state='complete',files=len(results),results=results,
            preselected_epochs=target_epochs,primary_position_fit_calls=sum(r['primary_solutions'] for r in results),
            alternate_seed_fit_calls=sum(len(r['alternate_seed_checks']) for r in results),
            position_fit_calls=sum(r['position_fit_calls'] for r in results),
            primary_converged=sum(s['converged'] for r in results for s in r['method_summaries'].values()),
            primary_abstained=sum(s['abstained'] for r in results for s in r['method_summaries'].values()),
            alternate_seed_converged=sum(c['status']=='converged' for r in results for c in r['alternate_seed_checks']),
            covariance_calibrated=False,source_audit_errors=0,
            empirical_earth_fit_attempts=0,scientific_eligibility_changes=0,originals_deleted=0)
        verify(); observation.gzip_json(output/'summary.json.gz',summary)
        compact={k:v for k,v in summary.items() if k!='results'}
        compact.update(manifest_sha256=il.sha256(path),summary_sha256=il.sha256(output/'summary.json.gz'))
        follow.atomic_json(output/'completion.json',compact)
        follow.atomic_json(output/'status.json',dict(state='complete',pid=os.getpid(),files=len(results)))
        print(json.dumps(compact,sort_keys=True),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=Path('data/ilvis0-position-20261007'))
    args=parser.parse_args()
    run(Path(__file__).resolve().parents[2],args.output.resolve())
