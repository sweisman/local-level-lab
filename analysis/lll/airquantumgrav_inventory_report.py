# SPDX-License-Identifier: AGPL-3.0-or-later
"""Verify and publish saved receiver inventory; never decode original data."""
import csv
import gzip
import io
import json
import math
from collections import Counter


def reconcile(selected,result,epochs,eligible,rejected):
    n=selected['total_receiver_epochs'];reasons=selected['epoch_reasons']
    if (len(reasons)!=n or len(epochs)!=n or result['receiver_epochs']!=n
            or selected['gyro_used_for_selection'] or selected['fused_navigation_used_for_selection']
            or not selected['source_integrity_verified'] or selected['instantaneous_motion_certified']
            or result['policy_version']!=selected['version']):
        raise ValueError('complete receiver-only selection binding required')
    for i,(epoch,reason) in enumerate(zip(epochs,reasons,strict=True)):
        if int(epoch['index'])!=i or epoch['rejection_reasons']!='|'.join(reason):
            raise ValueError('per-epoch exclusion evidence differs')
    coverage=bytearray(n)
    for label,table in [('eligible',eligible),('rejected_runs',rejected)]:
        if len(table)!=len(selected[label]):raise ValueError('published interval count differs')
        for number,(row,formatted) in enumerate(zip(selected[label],table,strict=True)):
            first,last=row['first_index'],row['last_index']
            if not 0<=first<=last<n or row['epochs']!=last-first+1:raise ValueError('interval indices differ')
            if any(coverage[i] or reasons[i] for i in range(first,last+1)):
                raise ValueError('overlap or excluded epoch inside interval')
            coverage[first:last+1]=bytes([1])*(last-first+1)
            for key,value in row.items():
                expected='|'.join(value) if key=='rejection_reasons' else str(value)
                if formatted[key]!=expected:raise ValueError('interval CSV differs from saved selection')
            if (formatted['group_id']!=result['group_id'] or formatted['policy_version']!=result['policy_version']
                    or formatted['source_sha256']!=result['receiver_source_sha256']
                    or formatted['interval_id']!=f'187-v2-{label}-{number:04d}'):
                raise ValueError('interval provenance differs')
            if label=='eligible' and (row['rejection_reasons'] or row['duration_s']<1200 or row['distance_m']<60000):
                raise ValueError('eligible interval does not meet frozen duration and distance')
    excluded=sum(bool(v) for v in reasons)
    if (any(bool(coverage[i])==bool(reasons[i]) for i in range(n))
            or excluded!=selected['excluded_epochs'] or excluded!=result['excluded_epochs']
            or dict(Counter(x for v in reasons for x in v))!=result['rejection_counts']
            or len(eligible)!=result['eligible_count'] or len(rejected)!=result['rejected_runs']
            or not math.isclose(sum(v['duration_s'] for v in selected['eligible'])/60,result['eligible_minutes'],abs_tol=1e-9)
            or result['decoder_calls']!=n+1 or result['charged_work']['receiver_file_passes']!=1
            or result['charged_work']['selection_passes']!=1
            or result['charged_work']['decoder_calls']!=((n+1+1023)//1024)*1024
            or any(result[k]!=0 for k in ('native_calls','raw_imu_reads','observed_optimizer_starts','protected_reads'))):
        raise ValueError('inventory coverage, summary or work differs')
    return dict(verified=True,receiver_epochs=n,eligible=selected['eligible'],eligible_minutes=result['eligible_minutes'],
        excluded_epochs=excluded,rejection_counts=result['rejection_counts'],charged_work=result['charged_work'],
        original_reads=0,numerical_work=0,scientific_decision='abstain')


def inspect(root,prefix='data/esa-development-selection-v2-20261023'):
    import sqlite3
    from lll.studies.closed import ClosedStudy
    from lll.studies.journal import inspect_snapshot
    study=ClosedStudy(root,prefix)
    try:
        if not study.summary['passed'] or len(study.tasks)!=1:raise ValueError('complete passing inventory required')
        identity=next(iter(study.tasks));result=study.envelope(identity)['result']
        selected=json.loads(gzip.decompress(study.artifact(identity,'selection.json.gz',raw=True)))
        table=lambda name:list(csv.DictReader(io.StringIO(study.artifact(identity,name,raw=True).decode())))
        epochs=list(csv.DictReader(io.StringIO(gzip.decompress(study.artifact(identity,'epoch-reasons.csv.gz',raw=True)).decode())))
        report=reconcile(selected,result,epochs,table('eligible.csv'),table('rejected_runs.csv'))
        raw=study.artifact(identity,'inventory-work.sqlite',raw=True)
        snapshot=inspect_snapshot(raw,study.completion['manifest_sha256'])
        connection=sqlite3.connect(':memory:')
        try:
            connection.deserialize(raw);connection.execute('PRAGMA query_only=ON')
            counts=dict(connection.execute('SELECT resource,SUM(total) FROM counts GROUP BY resource'))
            if counts!=result['charged_work'] or snapshot['starts']!=1:raise ValueError('saved work journal differs')
        finally:connection.close()
        for name in study.envelope(identity)['artifacts']:
            study.read(name,study.envelope(identity)['artifacts'][name],raw=True)
        report.update(group_id=result['group_id'],source_sha256=result['receiver_source_sha256'],
            manifest_sha256=study.completion['manifest_sha256'],summary_sha256=study.completion['summary_sha256'],
            elapsed_s=study.summary['elapsed_s'])
        return report
    finally:study.close()


def render(report):
    lines=['# Longer ESA development intervals','',
        f"**{len(report['eligible'])} eligible runs, totaling {report['eligible_minutes']:.1f} minutes.**",
        'They come from one development recording of the ESA/DTU airborne survey.',
        'Selection uses receiver timing, speed, distance, quality and valid covariance,',
        'before examining gyro values or fitting any physical candidate.','',
        '| Run | Duration | Distance | Mean ground speed | Mean latitude | Mean course | Height range |',
        '|---|---:|---:|---:|---:|---:|---:|']
    for i,row in enumerate(report['eligible']):
        lines.append(f"| {i+1} | {row['duration_s']/60:.1f} min | {row['distance_m']/1000:.1f} km | "
            f"{row['mean_speed_kmh']:.1f} km/h | {row['mean_latitude_deg']:.2f}° N | {row['mean_course_deg']:.1f}° | "
            f"{row['minimum_height_m']:.0f}–{row['maximum_height_m']:.0f} m |")
    lines+=['','Mean course summarizes a changing path; these are not straight, level legs.',
        'The runs contain turns and climbs. Version 2 removes the quiet-motion veto',
        'because the intended method explicitly propagates aircraft motion from IMU',
        'samples. It does not certify unseen motion between receiver samples.',
        'The zero-eligible version-1 inventory remains unchanged.','',
        'Every admitted run lasts at least 20 minutes, travels at least 60 km and',
        'stays at or above 180 km/h at the receiver epochs. Reported quality, timing,',
        'complete IMU support and positive-definite full covariance are required.',
        'Receiver accuracy and the instrument sampling interpretation remain assumptions.','',
        f"The one-pass inventory checks all {report['receiver_epochs']:,} receiver epochs; "
        f"{report['excluded_epochs']:,} fail one or more epoch rules.",
        'Saved-only verification reconciles every epoch and interval, all CSV outputs',
        'and the original-source hash, plus the charged work journal. It reads no',
        'original recording and performs no model fit.','',
        'No ESA shape or background-field result follows from this inventory.',
        'The next study needs its own preselected interval, training/prediction split,',
        'working errors, physical accuracy checks and finite fit allowance.',
        'Seven separate confirmation groups remain protected.','',
        '[Full interval CSV](artifacts/receiver-inventory-187-v2/eligible.csv) · '
        '[Excluded-epoch reasons](artifacts/receiver-inventory-187-v2/epoch-reasons.csv.gz) · '
        '[Frozen plan](PLAN.md) · [Selection rules](../external-imu-data/ESA_SELECTION_V2.md) · '
        '[Roadmap](../ANALYSIS_ROADMAP.md)']
    return '\n'.join(lines)+'\n'


def publish(root,prefix='data/esa-development-selection-v2-20261023',output='docs/esa-development-selection-v2'):
    from pathlib import Path
    from lll.ilvis0_control_publication import publish as package
    from lll.studies.artifacts import atomic,digest,encoded,safe_path
    from lll.studies.publication import archive_publication
    root=Path(root).resolve();data=safe_path(root,prefix);public=safe_path(root,output)
    if (public/'evidence-receipt.json').exists():raise ValueError('inventory publication already sealed')
    report=inspect(root,prefix);package(data,public,render(report),plan='docs/esa-development-selection-v2/PLAN.md')
    receipt=json.loads((public/'evidence-receipt.json').read_bytes())
    for name,raw in [('verified-report.json',encoded(report)),('reporter.py',Path(__file__).read_bytes())]:
        name='artifacts/publication/'+name;atomic(public/name,raw);receipt['artifacts'][name]=digest(raw)
    atomic(public/'evidence-receipt.json',encoded(receipt))
    return dict(archive_publication(root,data,public),published=output,numerical_work=0)
