# SPDX-License-Identifier: AGPL-3.0-or-later
"""Exact retrospective split metadata, without raw reads or model results."""
import math


def prediction_layout(chosen,source,context):
    segment=source['segment']
    if (source['filename']!=chosen['filename'] or segment['segment_id']!=chosen['segment_id']
            or str(segment['imu_type'])!=chosen['imu_type'] or source['task']!=context['task_id']
            or context['inspection']['source_sha256']!=chosen['source_sha256']
            or context['timing']['accepted'] is not True or not chosen['group_id']):
        raise ValueError('unchanged eligible recording, source and supported timing required')
    times=[float(r['time_s']) for r in segment['receiver_fixes']]
    if (len(times)<9 or any(not math.isfinite(t) for t in times)
            or any(not 0<b-a<=2. for a,b in zip(times,times[1:]))):
        raise ValueError('complete supported increasing receiver epochs required')
    cut=2*len(times)//3
    return dict(segment_id=chosen['segment_id'],filename=chosen['filename'],
        source_sha256=chosen['source_sha256'],group_id=chosen['group_id'],
        imu_type=int(chosen['imu_type']),receiver_epochs=len(times),
        training_epochs=cut,prediction_epochs=len(times)-cut,
        first_training_utc_week_s=times[0],last_training_utc_week_s=times[cut-1],
        first_prediction_utc_week_s=times[cut],last_prediction_utc_week_s=times[-1],
        training_span_s=times[cut-1]-times[0],prediction_span_s=times[-1]-times[cut],
        receiver_positions_used_for_selection=False,gyro_values_used_for_selection=False,
        original_reads=0,observed_starts=0)


def publish_layout(root,output='docs/ilvis0-prediction-pilot-preparation/split-receipt.json'):
    import csv
    import gzip
    import io
    import json
    from pathlib import Path
    from lll.studies.artifacts import ArchiveStore,atomic,digest,encoded,safe_path
    root=Path(root).resolve();target=safe_path(root,output)
    if target.exists():raise ValueError('fresh split receipt required')
    names=dict(selection='docs/ilvis0-prediction-pilot-preparation/selection.csv',
        receipt='docs/ilvis0-prediction-pilot-preparation/selection-receipt.json',
        population='data/ilvis0-highspeed-segments-v2-20261008/selection.json.gz',
        context='data/ilvis0-followup-20261007/summary.json')
    store=ArchiveStore(root)
    try:raw={key:store.read(path) for key,path in names.items()}
    finally:store.close()
    receipt=json.loads(raw['receipt'])
    if digest(raw['selection'])!=receipt['selection_sha256']:raise ValueError('selected inventory hash differs')
    population=json.loads(gzip.decompress(raw['population']))
    source={r['segment']['segment_id']:r for r in population['selected']}
    contexts={r['task_id']:r for r in json.loads(raw['context'])['results']}
    selected=list(csv.DictReader(io.StringIO(raw['selection'].decode())))
    if len(selected)!=3 or len({r['group_id'] for r in selected})!=3:
        raise ValueError('the three distinct preselected retrospective groups are required')
    layouts=[prediction_layout(row,source[row['segment_id']],contexts[source[row['segment_id']]['task']]) for row in selected]
    value=dict(version='ilvis0-prediction-layout-v1',layouts=layouts,
        input_sha256={names[k]:digest(v) for k,v in raw.items()},
        source_sha256=digest(Path(__file__).read_bytes()),
        selection='saved metadata-only selection; first floor(2*N/3) epochs train',
        original_reads=0,observed_starts=0,scientific_decision='abstain')
    atomic(target,encoded(value));return value
