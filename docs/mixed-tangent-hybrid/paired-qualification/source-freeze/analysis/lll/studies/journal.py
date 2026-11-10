# SPDX-License-Identifier: AGPL-3.0-or-later
"""Versioned transactional charges for new studies; legacy receipts stay intact."""
import json
from pathlib import Path
import sqlite3
from contextlib import contextmanager
from .artifacts import digest,encoded

VERSION='lll-indexed-charge-journal-v1'


class Journal:
    def __init__(self,path,*,freeze,limits):
        if not isinstance(freeze,str) or not freeze or not limits:
            raise ValueError('explicit freeze and finite identity limits required')
        if any(not isinstance(k,str) or not k or not v or any(not isinstance(r,str) or not r or type(n) is not int or n<0 for r,n in v.items()) for k,v in limits.items()):
            raise ValueError('finite nonnegative resource limits required')
        self.path=Path(path);self.path.parent.mkdir(parents=True,exist_ok=True)
        self.freeze=freeze;self.limits=limits;spec=encoded(dict(version=VERSION,freeze=freeze,limits=limits)).decode()
        with self._db() as db:
            db.executescript('CREATE TABLE IF NOT EXISTS metadata(id INTEGER PRIMARY KEY CHECK(id=1),spec TEXT NOT NULL);'
                'CREATE TABLE IF NOT EXISTS events(number INTEGER PRIMARY KEY,payload TEXT NOT NULL,sha256 TEXT NOT NULL);'
                'CREATE TABLE IF NOT EXISTS starts(identity TEXT PRIMARY KEY);'
                'CREATE TABLE IF NOT EXISTS kinds(kind TEXT PRIMARY KEY,total INTEGER NOT NULL);'
                'CREATE TABLE IF NOT EXISTS counts(identity TEXT,resource TEXT,total INTEGER NOT NULL,PRIMARY KEY(identity,resource));')
            prior=db.execute('SELECT spec FROM metadata').fetchall()
            if not prior:db.execute('INSERT INTO metadata VALUES (1,?)',(spec,))
            elif prior!=[(spec,)]:raise ValueError('journal freeze or allowance changed')
        self.verify()

    @contextmanager
    def _db(self):
        db=sqlite3.connect(self.path,timeout=30);db.execute('PRAGMA synchronous=FULL')
        try:
            with db:yield db
        finally:db.close()

    def _append(self,identity,resource=None,amount=1,record=None):
        if identity not in self.limits:raise ValueError('unknown identity')
        if resource is not None and (resource not in self.limits[identity] or type(amount) is not int or amount<1):
            raise ValueError('unknown resource or invalid charge')
        with self._db() as db:
            db.execute('BEGIN IMMEDIATE')
            prior=db.execute('SELECT number,sha256 FROM events ORDER BY number DESC LIMIT 1').fetchone()
            number=1 if prior is None else prior[0]+1;previous=None if prior is None else prior[1]
            started=db.execute('SELECT 1 FROM starts WHERE identity=?',(identity,)).fetchone()
            if resource is None:
                if started:raise ValueError('identity already charged; no retry')
                db.execute('INSERT INTO starts VALUES (?)',(identity,))
            else:
                if not started:raise ValueError('charge requires a reserved start')
                row=db.execute('SELECT total FROM counts WHERE identity=? AND resource=?',(identity,resource)).fetchone()
                total=(0 if row is None else row[0])+amount
                if total>self.limits[identity][resource]:raise ValueError('frozen resource allowance exceeded')
                db.execute('INSERT INTO counts VALUES (?,?,?) ON CONFLICT(identity,resource) DO UPDATE SET total=excluded.total',
                    (identity,resource,total))
            payload=dict(number=number,previous_sha256=previous,freeze=self.freeze,identity=identity,resource=resource,amount=amount)
            if record is not None:
                kind='starts' if resource is None else 'sweeps'
                old=db.execute('SELECT total FROM kinds WHERE kind=?',(kind,)).fetchone()
                ordinal=1 if old is None else old[0]+1
                db.execute('INSERT INTO kinds VALUES (?,?) ON CONFLICT(kind) DO UPDATE SET total=excluded.total',(kind,ordinal))
                payload['record']=dict(record,number=ordinal,manifest_sha256=self.freeze)
            raw=encoded(payload);db.execute('INSERT INTO events VALUES (?,?,?)',(number,raw.decode(),digest(raw)))
        return payload

    def start(self,identity):return self._append(identity)
    def reserve(self,identity,resource,amount=1):return self._append(identity,resource,amount)
    def count(self,identity,resource):
        with self._db() as db:row=db.execute('SELECT total FROM counts WHERE identity=? AND resource=?',(identity,resource)).fetchone()
        return 0 if row is None else row[0]

    def call(self,identity,resource,function,*args,**kwargs):
        self.reserve(identity,resource);return function(*args,**kwargs)

    def verify(self):
        previous=None;starts=set();counts={};number=0;kinds={}
        with self._db() as db:
            for expected,(number,raw,sha) in enumerate(db.execute('SELECT number,payload,sha256 FROM events ORDER BY number'),1):
                row=json.loads(raw)
                if (number!=expected or digest(raw.encode())!=sha or row.get('number')!=number
                        or row.get('previous_sha256')!=previous or row.get('freeze')!=self.freeze):
                    raise ValueError('journal hash chain changed')
                identity=row['identity'];resource=row['resource'];amount=row['amount']
                if 'record' in row:
                    kind='starts' if resource is None else 'sweeps';kinds[kind]=kinds.get(kind,0)+1
                    record=row['record']
                    if (record.get('number')!=kinds[kind] or record.get('manifest_sha256')!=self.freeze
                            or record.get('identity')!=identity):raise ValueError('journal compatibility row changed')
                    operations=record.get('operations',1)
                    if (type(operations) is not int or operations<1 or operations!=amount
                            or (resource is not None and record.get('phase')!=resource)
                            or (operations!=1 and resource!='fit')):
                        raise ValueError('journal compatibility operation count changed')
                if identity not in self.limits:raise ValueError('unknown charged identity')
                if resource is None:
                    if identity in starts or amount!=1:raise ValueError('duplicate or invalid start')
                    starts.add(identity)
                else:
                    if identity not in starts or resource not in self.limits[identity] or type(amount) is not int or amount<1:
                        raise ValueError('invalid resource charge')
                    key=(identity,resource);counts[key]=counts.get(key,0)+amount
                    if counts[key]>self.limits[identity][resource]:raise ValueError('resource allowance exceeded')
                previous=sha
            saved_starts={r[0] for r in db.execute('SELECT identity FROM starts')}
            saved_counts={(r[0],r[1]):r[2] for r in db.execute('SELECT identity,resource,total FROM counts')}
            saved_kinds=dict(db.execute('SELECT kind,total FROM kinds'))
            if saved_starts!=starts or saved_counts!=counts or saved_kinds!=kinds:raise ValueError('journal index disagrees with receipts')
        return dict(events=number,starts=len(starts),head_sha256=previous)

    def export(self,path):
        self.verify()
        with self._db() as db:rows=[dict(payload=json.loads(raw),sha256=sha) for raw,sha in db.execute('SELECT payload,sha256 FROM events ORDER BY number')]
        from .artifacts import atomic
        atomic(path,b''.join(encoded(row) for row in rows))


class IndexedLedger:
    """Compatibility interface for the bounded runner's new journal format."""
    def __init__(self,directory,freeze,identities,*,fit_limit,diagnostic_limit):
        self.directory=Path(directory);self.freeze=freeze
        self.journal=Journal(self.directory/'charges/journal.sqlite',freeze=freeze,
            limits={identity:dict(fit=fit_limit,diagnostic=diagnostic_limit) for identity in identities})

    def read(self,kind):
        if kind not in ('starts','sweeps'):raise ValueError('unknown journal')
        with self.journal._db() as db:
            rows=[json.loads(raw) for (raw,) in db.execute('SELECT payload FROM events ORDER BY number')]
        return [row['record'] for row in rows if (row['resource'] is None)==(kind=='starts')]

    def append(self,kind,fields):
        if kind not in ('starts','sweeps'):raise ValueError('unknown journal')
        if kind=='sweeps' and (fields.get('phase') not in ('fit','diagnostic') or fields.get('kind') not in ('value','tangent')):
            raise ValueError('invalid operation charge')
        operations=fields.get('operations',1)
        if (type(operations) is not int or operations<1
                or (operations!=1 and (kind!='sweeps' or fields['phase']!='fit'))):
            raise ValueError('positive native operation count required')
        return self.journal._append(fields['identity'],None if kind=='starts' else fields['phase'],
            amount=operations,record=fields)['record']

    def start(self,identity):return self.append('starts',dict(identity=identity))
    def count(self,identity,phase):return self.journal.count(identity,phase)

    def call(self,identity,phase,kind,function,*args):
        self.append('sweeps',dict(identity=identity,phase=phase,kind=kind));return function(*args)

    def export(self):
        from .artifacts import atomic
        for kind in ('starts','sweeps'):atomic(self.directory/(kind+'.jsonl'),b''.join(encoded(r) for r in self.read(kind)))


def inspect_snapshot(data,freeze):
    """Read-only sealed database inspection for metadata/status readers."""
    from contextlib import contextmanager
    db=sqlite3.connect(':memory:')
    try:
        db.deserialize(data);db.execute('PRAGMA query_only=ON')
        specs=db.execute('SELECT spec FROM metadata').fetchall()
        if len(specs)!=1:raise ValueError('one journal specification required')
        spec=json.loads(specs[0][0])
        if spec.get('version')!=VERSION or spec.get('freeze')!=freeze:raise ValueError('journal freeze mismatch')
        j=Journal.__new__(Journal);j.freeze=freeze;j.limits=spec['limits']
        @contextmanager
        def snapshot():yield db
        j._db=snapshot;checked=j.verify()
        phases=dict(db.execute('SELECT resource,SUM(total) FROM counts GROUP BY resource'))
        return dict(starts=checked['starts'],sweeps=sum(phases.values()),
            native_sweeps=phases.get('fit',0),incomplete_transaction=False)
    except sqlite3.Error as error:raise ValueError('invalid journal snapshot') from error
    finally:db.close()
