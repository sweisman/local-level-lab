# SPDX-License-Identifier: AGPL-3.0-or-later
"""Immutable per-charge receipts; an incomplete transaction blocks execution."""
from collections import Counter
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import uuid

VERSION='ilvis0-immutable-charge-receipts-v1'


def encoded(value):return (json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()


def digest(value):return hashlib.sha256(encoded(value)).hexdigest()


def durable_write(path,data,*,replace=False):
    temporary=path.parent/('.pending-'+uuid.uuid4().hex)
    fd=os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    try:
        view=memoryview(data)
        while view:
            n=os.write(fd,view)
            if not 0<n<=len(view):raise OSError('incomplete receipt write')
            view=view[n:]
        os.fsync(fd)
    finally:os.close(fd)
    # Publish only the complete, flushed record. Never overwrite an event.
    if replace:os.replace(temporary,path)
    else:os.link(temporary,path)
    directory=os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY)
    try:
        os.fsync(directory)
        if not replace:temporary.unlink()
        os.fsync(directory)
    finally:os.close(directory)


class Ledger:
    def __init__(self,directory,digest,identities,*,fit_limit=1,diagnostic_limit=26):
        self.directory=Path(directory);self.directory.mkdir(parents=True,exist_ok=True)
        self.events=self.directory/'charges';self.events.mkdir(exist_ok=True)
        self.digest=digest;self.identities=tuple(identities)
        self.limits={'fit':fit_limit,'diagnostic':diagnostic_limit}
        if (not self.identities or len(set(self.identities))!=len(self.identities)
                or any(type(n) is not int or n<1 for n in self.limits.values())):raise ValueError('unique identities and finite allowances required')

    def _load(self):
        names=[p.name for p in self.events.iterdir()]
        if any(n.startswith('.pending-') for n in names):raise ValueError('incomplete charge transaction; preserve, no repair')
        if any(n not in ('ledger.lock','HEAD.json') and not re.fullmatch(r'\d{8}\.json',n) for n in names):
            raise ValueError('unknown charge artifact')
        paths=sorted(self.events/n for n in names if re.fullmatch(r'\d{8}\.json',n))
        rows={'starts':[],'sweeps':[]};previous=None;seen=set();counts=Counter()
        try:
            for i,path in enumerate(paths,1):
                if path.name!=f'{i:08d}.json':raise ValueError('charge sequence gap')
                value=json.loads(path.read_text());payload=value['payload']
                if value['sha256']!=digest(payload) or payload['previous_sha256']!=previous or payload['event_number']!=i:
                    raise ValueError('charge hash chain mismatch')
                kind=payload['record_type'];row=payload['record'];identity=row['identity']
                if kind not in rows or row['number']!=len(rows[kind])+1 or row['manifest_sha256']!=self.digest or identity not in self.identities:
                    raise ValueError('charge scope or freeze mismatch')
                if kind=='starts':
                    if identity in seen:raise ValueError('duplicate charged start')
                    seen.add(identity)
                else:
                    phase=row['phase']
                    if identity not in seen or phase not in self.limits or row['kind'] not in ('tangent','value'):raise ValueError('invalid native charge')
                    counts[identity,phase]+=1
                    if counts[identity,phase]>self.limits[phase]:raise ValueError('charge allowance exceeded')
                rows[kind].append(row);previous=value['sha256']
            head=json.loads((self.events/'HEAD.json').read_text()) if (self.events/'HEAD.json').exists() else dict(events=0,sha256=None)
            if head!=dict(events=len(paths),sha256=previous):raise ValueError('incomplete charge head transaction')
        except (OSError,KeyError,TypeError,json.JSONDecodeError,UnicodeError) as error:
            raise ValueError('invalid immutable charge receipt; no repair') from error
        return rows,len(paths),previous

    def read(self,kind):
        if kind not in ('starts','sweeps'):raise ValueError('unknown journal')
        with (self.events/'ledger.lock').open('a+') as lock:
            fcntl.flock(lock,fcntl.LOCK_SH);return self._load()[0][kind]

    def append(self,kind,fields):
        with (self.events/'ledger.lock').open('a+') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX);rows,n,previous=self._load();identity=fields['identity']
            if identity not in self.identities:raise ValueError('identity outside finite scope')
            if kind=='starts':
                if any(r['identity']==identity for r in rows['starts']):raise ValueError('start charged; no retry')
            elif kind=='sweeps':
                if not any(r['identity']==identity for r in rows['starts']):raise ValueError('native work requires charged start')
                phase=fields['phase']
                if phase not in self.limits or fields['kind'] not in ('tangent','value'):raise ValueError('invalid native charge')
                if sum(r['identity']==identity and r['phase']==phase for r in rows[kind])>=self.limits[phase]:
                    from .ilvis0_estimator import EvaluationLimit
                    raise EvaluationLimit('native charge allowance exhausted')
            else:raise ValueError('unknown journal')
            row=dict(fields,number=len(rows[kind])+1,manifest_sha256=self.digest)
            payload=dict(event_number=n+1,previous_sha256=previous,record_type=kind,record=row)
            h=digest(payload)
            durable_write(self.events/f'{n+1:08d}.json',encoded(dict(payload=payload,sha256=h)))
            durable_write(self.events/'HEAD.json',encoded(dict(events=n+1,sha256=h)),replace=True)
            return row

    def start(self,identity):return self.append('starts',dict(identity=identity))

    def count(self,identity,phase):return sum(r['identity']==identity and r['phase']==phase for r in self.read('sweeps'))

    def call(self,identity,phase,kind,function,*args):
        self.append('sweeps',dict(identity=identity,phase=phase,kind=kind))
        return function(*args)

    def export(self):
        with (self.events/'ledger.lock').open('a+') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX);rows,_,_=self._load()
            for name,values in rows.items():durable_write(self.directory/(name+'.jsonl'),b''.join(encoded(r) for r in values),replace=True)
