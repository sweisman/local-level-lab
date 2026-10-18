# SPDX-License-Identifier: AGPL-3.0-or-later
"""Explicit read-only audit of a hash-preserved incomplete legacy journal."""
from collections import Counter
import hashlib
import json
from pathlib import Path

VERSION='ilvis0-interrupted-accounting-audit-v1'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):return json.loads(Path(path).read_text())


def inspect(directory):
    directory=Path(directory);failure=load(directory/'failure.json')
    for name,h in failure['artifacts'].items():
        if Path(name).name!=name or sha(directory/name)!=h:raise ValueError('interrupted source hash mismatch')
    manifest=load(directory/'manifest.json');plan=manifest['plan'];tasks=plan['tasks'];digest=sha(directory/'manifest.json')
    ids={t['identity'] for t in tasks};by_id={t['identity']:t for t in tasks};limit=plan['maximum_evaluations_per_identity']
    if len(ids)!=len(tasks) or len(tasks)!=plan['maximum_starts']:raise ValueError('original identity scope mismatch')
    starts=[json.loads(line) for line in (directory/'starts.jsonl').read_text().splitlines()]
    seen=set()
    for i,row in enumerate(starts,1):
        if row['number']!=i or row['manifest_sha256']!=digest or row['identity'] not in ids or row['identity'] in seen:
            raise ValueError('invalid start accounting')
        seen.add(row['identity'])
    lines=(directory/'sweeps.jsonl').read_bytes().splitlines(keepends=True);counts=Counter();valid=[];tail=None
    for i,line in enumerate(lines,1):
        try:row=json.loads(line)
        except (UnicodeError,json.JSONDecodeError):
            if i!=len(lines) or line.endswith(b'\n'):raise ValueError('corruption is not solely an incomplete final entry')
            tail=dict(line=i,bytes=len(line),sha256=hashlib.sha256(line).hexdigest());break
        if (not line.endswith(b'\n') or row['number']!=i or row['manifest_sha256']!=digest or row['identity'] not in seen
                or row['phase']!='diagnostic' or row['kind']!='tangent'):raise ValueError('invalid native charge prefix')
        counts[row['identity']]+=1
        if counts[row['identity']]>limit:raise ValueError('original allowance exceeded')
        valid.append(row)
    if tail is None:raise ValueError('expected preserved incomplete tail absent')
    saved={};artifacts={}
    for name,expected in failure['saved_results'].items():
        if Path(name).name!=name or sha(directory/name)!=expected['sha256']:raise ValueError('saved-result artifact mismatch')
        wrapper=load(directory/name);r=wrapper['result'];identity=r['identity']
        h=hashlib.sha256(json.dumps(r,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
        if (wrapper['manifest_sha256']!=digest or wrapper['result_sha256']!=h or identity not in seen
                or identity in saved or r['native_evaluations']!=counts[identity]):raise ValueError('saved result/accounting mismatch')
        artifact=r['linearization_file']
        if Path(artifact).name!=artifact or sha(directory/artifact)!=r['linearization_sha256']:raise ValueError('saved native artifact mismatch')
        saved[identity]=r;artifacts[name]=sha(directory/name);artifacts[artifact]=sha(directory/artifact)
    controls=[t for t in tasks if t['kind']=='control']
    controls_passed=bool(controls and all(t['identity'] in saved and saved[t['identity']]['passed'] for t in controls))
    unstarted=[t for t in tasks if t['identity'] not in seen]
    remaining=len(unstarted)*limit;reserved=len(seen)*limit
    if remaining+reserved!=plan['maximum_native_evaluations']:raise ValueError('combined finite allowance mismatch')
    return dict(version=VERSION,original_manifest_sha256=digest,charged_starts=len(starts),verified_saved_results=len(saved),
        valid_native_call_charges=len(valid),incomplete_charge_line=tail['line'],incomplete_tail=tail,
        charged_tasks=[by_id[r['identity']] for r in starts],unstarted_tasks=unstarted,
        interrupted_identities=sorted(seen-set(saved)),saved_results=saved,saved_artifacts=artifacts,
        controls_passed=controls_passed,maximum_remaining_native_evaluations=remaining,reserved_started_allowance=reserved,
        original_maximum_native_evaluations=plan['maximum_native_evaluations'],original_journals_unchanged=True,
        observed_starts=0,native_predictions=0)
