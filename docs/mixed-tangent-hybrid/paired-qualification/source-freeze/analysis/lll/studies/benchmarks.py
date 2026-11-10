# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite bookkeeping benchmarks on generated files; no instrument data or fits."""
import hashlib
import json
from pathlib import Path
import platform
import time
from .artifacts import ArchiveStore,atomic,encoded

LIMIT_SECONDS=120


def run(root,scratch):
    from ..ilvis0_receipt_journal import Ledger
    from .journal import IndexedLedger
    root=Path(root);scratch=Path(scratch)
    if scratch.exists():raise ValueError('benchmark requires a fresh generated workspace')
    scratch.mkdir(parents=True);freeze=hashlib.sha256(b'fixed-bookkeeping-benchmark-v1').hexdigest()
    scope=dict(version='lll-bookkeeping-benchmarks-v1',executions=12,maximum_seconds_each=LIMIT_SECONDS,
        generated_records=200,native_evaluations=0,observed_fits=0,numerical_threads=1)
    atomic(root/'repro/benchmark-scope.json',encoded(scope))
    results=[]
    def measure(name,variant,function):
        started=time.monotonic();out=function(started);elapsed=time.monotonic()-started
        row=dict(name=name,variant=variant,seconds=elapsed,within_allowance=elapsed<=LIMIT_SECONDS,
            logical_sha256=hashlib.sha256(encoded(out)).hexdigest());results.append(row);return out
    def check(started):
        if time.monotonic()-started>LIMIT_SECONDS:raise ValueError('benchmark cooperative allowance exhausted')
    ledgers={}
    for label,kind in (('expanded',Ledger),('indexed',IndexedLedger)):
        ledger=kind(scratch/label,freeze,['case'],fit_limit=200,diagnostic_limit=1);ledgers[label]=ledger
        def append(started,ledger=ledger):
            ledger.start('case')
            for i in range(200):
                check(started);ledger.append('sweeps',dict(identity='case',phase='fit',kind='tangent',packet_visits=1))
            return ledger.read('sweeps')
        measure('charge append',label,append)
    for label,ledger in ledgers.items():
        def counts(started,ledger=ledger):
            values=[]
            for i in range(100):check(started);values.append(ledger.count('case','fit'))
            return values
        measure('charge count lookup',label,counts)
    source=scratch/'generated';names=[]
    for i in range(200):
        name=f'docs/example/source-freeze/module-{i:04d}.py';path=source/name;path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes((f'# generated variant {i%5}\n'+('x=1\n'*50)).encode());names.append(name)
    store=ArchiveStore(source);store.pack(names)
    catalog=store.catalog()
    def hashes(started,packed):
        if packed:store.verify()
        out=[]
        for name in names:
            check(started)
            out.append(catalog['paths'][name]['sha256'] if packed else hashlib.sha256((source/name).read_bytes()).hexdigest())
        return out
    measure('duplicate source verification','expanded',lambda t:hashes(t,False))
    measure('duplicate source verification','indexed',lambda t:hashes(t,True))
    def listing(started,packed):
        check(started)
        return sorted(catalog['paths'] if packed else (str(p.relative_to(source)) for p in (source/'docs').rglob('*.py')))
    measure('source inventory','expanded',lambda t:listing(t,False))
    measure('source inventory','indexed',lambda t:listing(t,True))
    documents=[]
    for i in range(200):
        name=f'docs/example/artifacts/result-{i:04d}.json';path=source/name;path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(encoded(dict(identity=i,value=i%7)));documents.append(name)
    store.pack(documents);catalog=store.catalog()
    def documents_read(started,packed):
        out=[]
        for name in documents:
            check(started)
            data=store._object(catalog['paths'][name]['sha256'],catalog) if packed else (source/name).read_bytes()
            out.append(json.loads(data))
        return out
    measure('result reads','expanded',lambda t:documents_read(t,False))
    measure('result reads','indexed',lambda t:documents_read(t,True))
    for label,ledger in ledgers.items():
        def exported(started,ledger=ledger):
            check(started);ledger.export()
            return [(scratch/label/(kind+'.jsonl')).read_text() for kind in ('starts','sweeps')]
        measure('audit export',label,exported)
    for name in {r['name'] for r in results}:
        pair=[r for r in results if r['name']==name]
        if len(pair)!=2 or pair[0]['logical_sha256']!=pair[1]['logical_sha256']:
            raise ValueError('benchmark changed logical results: '+name)
    report=dict(scope=scope,python=platform.python_version(),platform=platform.machine(),results=results,
        equivalent=True,numerical_algorithm_changed=False)
    atomic(root/'repro/benchmarks.json',encoded(report));return report
