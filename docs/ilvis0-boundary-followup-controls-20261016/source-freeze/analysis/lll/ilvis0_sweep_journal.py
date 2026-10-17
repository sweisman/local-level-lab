# SPDX-License-Identifier: AGPL-3.0-or-later
"""Durable pre-call accounting. Interrupted and failed work remains charged."""
from collections import Counter
import fcntl
import json
import os
from pathlib import Path

from .ilvis0_estimator import EvaluationLimit


class Ledger:
    def __init__(self,directory,digest,identities,*,fit_limit=200,diagnostic_limit=55):
        self.directory=Path(directory);self.directory.mkdir(parents=True,exist_ok=True)
        self.digest=digest;self.identities=tuple(identities)
        if (not self.identities or len(set(self.identities))!=len(self.identities)
                or any(type(n) is not int or n<1 for n in (fit_limit,diagnostic_limit))):
            raise ValueError('unique identities and finite positive allowances required')
        self.limits={'fit':fit_limit,'diagnostic':diagnostic_limit}

    def read(self,kind):
        if kind not in ('starts','sweeps'):raise ValueError('unknown journal')
        path=self.directory/(kind+'.jsonl')
        try:rows=[json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []
        except (ValueError,UnicodeError) as e:raise ValueError('corrupt charge journal; no repair') from e
        seen=set();counts=Counter()
        starts={r['identity'] for r in self.read('starts')} if kind=='sweeps' else None
        for index,row in enumerate(rows):
            if (row.get('number')!=index+1 or row.get('manifest_sha256')!=self.digest
                    or row.get('identity') not in self.identities):
                raise ValueError('invalid charge journal scope or freeze')
            identity=row['identity']
            if kind=='starts':
                if identity in seen:raise ValueError('duplicate start charge')
                seen.add(identity)
            else:
                phase=row.get('phase');native=row.get('kind')
                if phase not in self.limits or native not in ('tangent','value') or identity not in starts:
                    raise ValueError('invalid native sweep charge')
                counts[identity,phase]+=1
                if counts[identity,phase]>self.limits[phase]:raise ValueError('charge allowance exceeded')
        return rows

    def append(self,kind,fields):
        path=self.directory/(kind+'.jsonl')
        with path.open('a+') as stream:
            fcntl.flock(stream,fcntl.LOCK_EX)
            rows=self.read(kind);identity=fields['identity']
            if identity not in self.identities:raise ValueError('identity outside finite scope')
            if kind=='starts':
                if any(r['identity']==identity for r in rows):raise ValueError('start charged; no retry')
                if len(rows)>=len(self.identities):raise EvaluationLimit('start allowance exhausted')
            else:
                phase=fields['phase']
                if phase not in self.limits or fields['kind'] not in ('tangent','value'):
                    raise ValueError('unsupported sweep phase or kind')
                if identity not in {r['identity'] for r in self.read('starts')}:
                    raise ValueError('native work requires charged start')
                if sum(r['identity']==identity and r['phase']==phase for r in rows)>=self.limits[phase]:
                    raise EvaluationLimit('native sweep allowance exhausted')
            row=dict(fields,number=len(rows)+1,manifest_sha256=self.digest)
            stream.write(json.dumps(row,sort_keys=True,allow_nan=False)+'\n')
            stream.flush();os.fsync(stream.fileno())
        fd=os.open(self.directory,os.O_RDONLY|os.O_DIRECTORY)
        try:os.fsync(fd)
        finally:os.close(fd)
        return row

    def start(self,identity):return self.append('starts',dict(identity=identity))

    def count(self,identity,phase):
        return sum(r['identity']==identity and r['phase']==phase for r in self.read('sweeps'))

    def call(self,identity,phase,kind,function,*args):
        self.append('sweeps',dict(identity=identity,phase=phase,kind=kind))
        return function(*args)
