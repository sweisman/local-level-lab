#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Audit the interrupted trial using saved metadata; no original reads or fits."""
import argparse
from contextlib import ExitStack
import fcntl
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import sys

ROOT=Path(__file__).resolve().parents[2]
PARENT=ROOT/'data/ilvis0-profile-seeded-trial-20261017'
OUTPUT=ROOT/'data/ilvis0-profile-seeded-audit-20261017'
GUIDE=Path(__file__).resolve().parent


def load(path):return json.loads(path.read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def write(path,value):path.write_text(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n')


def render():
    summary=load(OUTPUT/'summary.json');fit=summary['target'];clock=summary['clock_geometry']
    completion=load(OUTPUT/'completion.json')
    if completion['summary_sha256']!=sha(OUTPUT/'summary.json'):raise ValueError('saved audit changed')
    text='# Why the profile-seeded trial stopped\n\n'
    text+='The trial preserved two passing controls and one full-time fit that failed its stopping check. '
    text+='Its fourth identity was interrupted during an accounting write. The original study cannot resume; '
    text+='the incomplete transaction and all charged starts remain unchanged.\n\n'
    text+=f"The completed target's stationarity measure was **{fit['stationarity']:.9g}**, against the unchanged limit **{fit['limit']:.9g}**. "
    text+='Only the time-alignment coordinate exceeded the limit. '
    text+=f"All {fit['trial_steps']} proposed steps were rejected; none improved the actual fitting cost. "
    text+='Holding time fixed had passed, but that did not qualify the full-time solution.\n\n'
    text+=f"The nearest receiver epoch lies **{summary['nearest_boundary_s']*1e9:.6g} nanoseconds** from an integration-packet boundary. "
    text+='A step can therefore cross an integration branch even when it is very small. '
    text+='This is a concrete reason to check both sides of that boundary before attributing the failed step to an incorrect derivative.\n\n'
    if clock:
        text+=f"Exact saved-clock geometry supports the existing two-sided check: **{clock['side_geometry_supported']}**. "
        text+=f"The canonical knot requires a time relocation of {clock['center_relocation_s']*1e9:.6g} nanoseconds.\n\n"
    text+='This audit reads preserved results and receiver timestamps only. It makes zero native predictions, '
    text+='reads no original IMU measurements, performs no fits and changes no labels. '
    text+='A fresh exact-boundary diagnostic needs a separately frozen finite allowance. '
    text+='Published findings remain 49 globe / zero flat / four unresolved.\n'
    (GUIDE/'README.md').write_text(text)
    for name in ('manifest.json','summary.json','completion.json'):shutil.copyfile(OUTPUT/name,GUIDE/name)
    write(GUIDE/'evidence-receipt.json',dict(artifacts={n:sha(GUIDE/n) for n in
        ('manifest.json','summary.json','completion.json','README.md')},scientific_decision='abstain'))


def build():
    OUTPUT.mkdir(exist_ok=True)
    with ExitStack() as stack:
        for path,mode,lockkind in ((OUTPUT/'worker.lock','a+',fcntl.LOCK_EX),(PARENT/'worker.lock','r',fcntl.LOCK_SH)):
            lock=stack.enter_context(path.open(mode));fcntl.flock(lock,lockkind|fcntl.LOCK_NB)
        if (OUTPUT/'start.json').exists():raise ValueError('charged metadata audit cannot rerun; use --render-only')
        sys.path.insert(0,str(ROOT/'analysis'))
        sys.path.insert(0,str(ROOT/'analysis/tests'))
        import importlib.util
        spec=importlib.util.spec_from_file_location('_status_reader',ROOT/'analysis/status.py')
        status=importlib.util.module_from_spec(spec);spec.loader.exec_module(status)
        parent=load(PARENT/'manifest.json');digest=sha(PARENT/'manifest.json')
        counts=status.receipt_counts(PARENT,digest)
        if not counts or not counts['incomplete_transaction']:raise ValueError('expected stopped transaction is missing')
        inputs={str(PARENT/'manifest.json'):digest,str(PARENT/'charges/HEAD.json'):sha(PARENT/'charges/HEAD.json')}
        saved=[];missing=[]
        for task in parent['plan']['tasks']:
            path=PARENT/(task['identity'].replace('::','-')+'.json')
            if not path.exists():missing.append(task['identity']);continue
            envelope=load(path);result=envelope['result']
            if envelope['manifest_sha256']!=digest or envelope['result_sha256']!=status.result_digest(result):
                raise ValueError('saved result changed')
            inputs[str(path)]=sha(path);saved.append(result)
        targets=[r for r in saved if r['kind']=='target']
        if len(saved)!=3 or len(targets)!=1 or len(missing)!=1:raise ValueError('exact stopped evidence required')
        fit=targets[0];names=fit['active_parameters'];relative=fit['scaled_projected_gradient'];limit=fit['stationarity_tolerance']
        failed=[name for name,g in zip(names,relative) if abs(g)>limit]
        if failed!=['time_offset']:raise ValueError('expected time-only stationarity failure changed')
        artifact=PARENT/fit['linearization_file']
        if sha(artifact)!=fit['linearization_sha256']:raise ValueError('native endpoint artifact changed')
        inputs[str(artifact)]=sha(artifact)
        with gzip.open(artifact,'rt') as stream:local=json.load(stream)
        sources={str(Path(__file__)):sha(Path(__file__)),str(ROOT/'analysis/status.py'):sha(ROOT/'analysis/status.py'),
            str(ROOT/'analysis/lll/ilvis0_clock_brackets.py'):sha(ROOT/'analysis/lll/ilvis0_clock_brackets.py')}
        manifest=dict(inputs=inputs,sources=sources,maximum_geometry_queries=1024,maximum_clock_checks=1,
            native_predictions=0,optimizer_starts=0,original_reads=0,numerical_threads=4)
        write(OUTPUT/'manifest.json',manifest);write(OUTPUT/'start.json',dict(manifest_sha256=sha(OUTPUT/'manifest.json')))
        import numpy as np
        from lll.ilvis0_clock_brackets import bracket
        times=np.array(local['times_s']);offset=fit['parameters']['time_offset'];scale=.15
        # Extra trailing packets do not affect earlier saved receiver epochs.
        count=int(np.ceil((max(times)+scale)/.005))+2
        ends=np.cumsum(np.full(count,.005));shifted=times+offset;indices=np.searchsorted(ends,shifted)
        nearest=np.minimum(abs(shifted-ends[indices]),abs(shifted-ends[np.maximum(0,indices-1)]))
        geometry=bracket(times,count,scale,fit['normalized_parameters'][names.index('time_offset')],maximum_queries=1024)
        steps=fit['step_history']
        summary=dict(state='complete',charged_native_calls=counts['sweeps'],charged_identities=counts['starts'],
            saved_results=len(saved),missing_result_identities=missing,original_labels_changed=False,
            target=dict(identity=fit['identity'],stationarity=fit['exact_projected_gradient_relative'],limit=limit,
                failing_coordinates=failed,trial_steps=len(steps),accepted_steps=sum(s['accepted'] for s in steps),
                starting_point_unchanged=fit['normalized_parameters']==fit['selected_profile']['normalized_parameters']),
            nearest_boundary_s=float(min(nearest)),clock_geometry=geometry,native_predictions=0,optimizer_starts=0)
        for path,h in dict(inputs,**sources).items():
            if sha(Path(path))!=h:raise ValueError('audit source changed')
        write(OUTPUT/'summary.json',summary)
        write(OUTPUT/'completion.json',dict(state='complete',manifest_sha256=sha(OUTPUT/'manifest.json'),summary_sha256=sha(OUTPUT/'summary.json')))
        render();print(json.dumps(summary))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--render-only',action='store_true')
    if parser.parse_args().render_only:render()
    else:build()
