# SPDX-License-Identifier: AGPL-3.0-or-later
"""Inventory saved primary-receiver metadata without reading IMU observations."""
import json
import re
from pathlib import Path


def policy():
    return dict(maximum_records=53,maximum_metadata_bytes=1000000,original_reads=0,
        native_calls=0,optimizer_starts=0,model_outcomes_used=False,receiver_covariance_established=False)


def inspect_record(metadata,expected):
    if metadata['source_file']!=expected['filename'] or metadata['source_sha256']!=expected['source_sha256']:
        raise ValueError('receiver metadata source differs from selected recording')
    gps=metadata['gps'];counts=gps['sentence_counts'];total=gps['bytes'];unparsed=gps['discarded_fragment_bytes']
    if (type(total) is not int or type(unparsed) is not int or not 0<=unparsed<=total
            or any(not isinstance(k,str) or type(v) is not int or v<0 for k,v in counts.items())
            or type(gps['invalid_checksums']) is not int or gps['invalid_checksums']<0):
        raise ValueError('valid bounded receiver counts required')
    codes=sorted({int(c) for version in metadata['versions']
        for c in re.findall(r'(?:^|,)PGPS(\d+)(?=,|$)',version)})
    return dict(expected,metadata_available=True,primary_receiver_type_codes=codes,
        receiver_stream_bytes=total,not_parsed_as_nmea_bytes=unparsed,
        invalid_nmea_checksums=gps['invalid_checksums'],sentence_counts=counts,
        nmea_talkers=sorted({k[:-3] for k in counts if len(k)>=5}),
        gga_count=sum(n for k,n in counts.items() if k.endswith('GGA')),
        nmea_precision_sentence_types=sorted(k for k in counts if k.endswith(('GST','GBS'))),
        nmea_dop_sentence_types=sorted(k for k in counts if k.endswith('GSA')),
        source_kind=metadata.get('gps_kind'),binary_contents_identified=False,
        receiver_covariance_established=False,scientific_decision='abstain')


def prepare(root,identity='ilvis0-receiver-metadata-20261022'):
    import csv
    from lll.studies.artifacts import ArchiveStore,atomic,encoded,safe_path,digest
    from lll.studies.dependencies import source_closure
    from lll.studies.runtime import Definition
    root=Path(root).resolve();csv_path=root/'docs/ilvis0-current-findings-20261015/stretch-analytics.csv'
    rows=list(csv.DictReader(csv_path.open()))
    if len(rows)!=53 or len({r['segment_id'] for r in rows})!=53:raise ValueError('original53-stretch cohort required')
    records={}
    for row in rows:
        value=dict(task=row['task'],filename=row['filename'],source_sha256=row['source_sha256'])
        if value['task'] in records and records[value['task']]!=value:raise ValueError('recording source changed')
        records[value['task']]=value
    base=safe_path(root,'data/ilvis0-source-point-development/receiver-metadata-inputs')
    if base.exists() or safe_path(root,'data/'+identity).exists():raise ValueError('fresh finite metadata study required')
    adapter='analysis/lll/ilvis0_receiver_metadata.py'
    sources=source_closure(root,[adapter,'analysis/tests/test_ilvis0_receiver_metadata.py',
        'docs/ilvis0-receiver-metadata/PLAN.md'])
    store=ArchiveStore(root);catalog=store.catalog();inputs={};tasks=[]
    def save(key,raw,extension='json'):
        path=base/(key+'.'+extension);atomic(path,raw);inputs[key]=path.relative_to(root).as_posix()
    try:
        base.mkdir(parents=True);save('policy',encoded(policy()));save('cohort',csv_path.read_bytes(),'csv')
        for identity_key,expected in sorted(records.items()):
            name='data/ilvis0-ready/'+identity_key+'/decoded/inspection.json'
            try:raw=store._read(name,catalog)
            except FileNotFoundError:raw=None
            if raw is not None and len(raw)>policy()['maximum_metadata_bytes']:
                raise ValueError('receiver metadata exceeds declared size limit')
            key='record-'+identity_key
            save(key,encoded(dict(expected=expected,source_metadata_path=name,
                source_metadata_sha256=digest(raw) if raw is not None else None,
                metadata=json.loads(raw) if raw is not None else None)))
            tasks.append(dict(identity=key,input_key=key,limits=dict(native_calls=0,packet_visits=0,bound_calls=0,bound_steps=0)))
        definition=dict(id=identity,adapter=adapter,sources=sources,inputs=inputs,tasks=tasks,
            workers=1,threads=1,maximum_wall_s=120.)
        atomic(base/'definition.json',encoded(definition));manifest=Definition.from_dict(definition,root).prepare(root)
        return dict(path='data/'+identity,recordings=len(tasks),stretches=53,sources=len(manifest['sources']),
            limits=manifest['limits'],allocation=manifest['allocation'])
    finally:store.close()


def evaluate(task,context):
    from lll.studies.artifacts import digest,encoded
    settings=json.loads(context.input_path('policy').read_bytes())
    if settings!=policy():raise ValueError('unchanged receiver metadata policy required')
    value=json.loads(context.input_path().read_bytes());expected=value['expected'];metadata=value['metadata']
    if metadata is None:record=dict(expected,metadata_available=False,receiver_covariance_established=False)
    else:record=inspect_record(metadata,expected)
    # Preserve the original-byte hash alongside its parsed deterministic representation.
    context.save('receiver-metadata.json',dict(record=record,source_metadata_path=value['source_metadata_path'],
        source_metadata_sha256=value['source_metadata_sha256'],parsed_metadata_sha256=digest(encoded(metadata))))
    return dict(identity=task['identity'],passed=True,record=record,original_reads=0,native_evaluations=0,
        optimizer_starts=0,receiver_covariance_established=False,scientific_decision='abstain')


def inspect(root,prefix):
    from lll.studies.closed import ClosedStudy
    from lll.studies.artifacts import digest
    study=ClosedStudy(root,prefix);records=[];missing=[]
    try:
        if digest(Path(__file__).read_bytes())!=study.manifest['sources']['analysis/lll/ilvis0_receiver_metadata.py']:
            raise ValueError('receiver metadata auditor differs from freeze')
        if study.input('policy')!=policy():raise ValueError('metadata policy changed')
        for identity in study.tasks:
            if identity not in study.rows or not study.rows[identity]['passed']:missing.append(identity);continue
            value=study.input(study.tasks[identity]['input_key']);result=study.envelope(identity)['result']
            actual=(inspect_record(value['metadata'],value['expected']) if value['metadata'] is not None else
                dict(value['expected'],metadata_available=False,receiver_covariance_established=False))
            if actual!=result['record']:raise ValueError('saved receiver inventory differs from inputs')
            study.artifact(identity,'receiver-metadata.json');records.append(actual)
        if not 1<=len(study.tasks)<=53:raise ValueError('bounded original cohort required')
        return dict(records=records,missing=missing,complete=not missing,stretches=53,numerical_work=0,
            manifest_sha256=study.completion['manifest_sha256'],summary_sha256=study.completion['summary_sha256'],
            receiver_covariance_established=False,model_outcomes_used=False)
    finally:study.close()


def render(report):
    available=[r for r in report['records'] if r['metadata_available']]
    total=sum(r['receiver_stream_bytes'] for r in available);unparsed=sum(r['not_parsed_as_nmea_bytes'] for r in available)
    precision=sum(bool(r['nmea_precision_sentence_types']) for r in available)
    text=['# What receiver-error information is already recorded?','',
        f"The 53 selected stretches come from {len(report['records'])+len(report['missing'])} recording files. "
        f"Saved primary-receiver metadata is available for **{len(available)} files**. This is an availability "
        'audit, not a count of independent flights.',
        '',f"**{precision} files** list GST or GBS error-statistics sentences. "
        'Presence alone does not establish their interpretation or a usable covariance.',
        '',f"Of {total:,} receiver-stream bytes, {unparsed:,} were not parsed as NMEA text. "
        'Their contents are not identified by this audit; the count does not mean those bytes are raw '
        'GNSS measurements or independent accuracy estimates.',
        '', '| Recording task | Primary-receiver type code | GGA sentences | Listed error-statistics sentences |',
        '|---|---|---:|---|']
    for row in report['records']:
        if not row['metadata_available']:values=[row['task'],'Unavailable','—','Unavailable']
        else:values=[row['task'],', '.join(map(str,row['primary_receiver_type_codes'])) or 'Not recorded',
            str(row['gga_count']),', '.join(row['nmea_precision_sentence_types']) or 'None listed']
        text.append('| '+' | '.join(values)+' |')
    text+=['', 'NMEA is a receiver text-message format. GGA provides positions and quality fields; '
        'its presence does not supply an independently measured noise covariance. The type codes above '
        'are recorded identifiers, not manufacturer or physical-unit identifications.',
        '', 'The audit reads saved inspection records only. It reads no original IMU file, uses no '
        'model residuals or fused-navigation covariance, and performs no predictions or fits. Missing '
        'or unparsed information remains unknown. **The aircraft prediction error law remains unqualified.**',
        '', '[Frozen scope](PLAN.md) · [Error assumptions](../PREDICTION_ERROR_ASSUMPTIONS.md) · '
        '[Roadmap](../ANALYSIS_ROADMAP.md)']
    return '\n'.join(text)+'\n'


def publish(root,prefix,output='docs/ilvis0-receiver-metadata'):
    from lll.ilvis0_control_publication import publish as package
    from lll.studies.artifacts import safe_path,atomic,encoded,digest
    from lll.studies.publication import archive_publication
    root=Path(root).resolve();data=safe_path(root,prefix);public=safe_path(root,output)
    if (public/'evidence-receipt.json').exists():raise ValueError('publication already sealed')
    report=inspect(root,prefix);package(data,public,render(report),plan='docs/ilvis0-receiver-metadata/PLAN.md')
    receipt=json.loads((public/'evidence-receipt.json').read_text());name='artifacts/publication/inventory.json'
    raw=encoded(report);atomic(public/name,raw);receipt['artifacts'][name]=digest(raw)
    atomic(public/'evidence-receipt.json',encoded(receipt))
    return dict(archive_publication(root,data,public),published=output,numerical_work=0)
