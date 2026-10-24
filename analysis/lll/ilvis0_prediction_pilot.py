# SPDX-License-Identifier: AGPL-3.0-or-later
"""Metadata-only pilot selection; no gyro summaries, model costs or raw reads."""
import csv
import io
import math
from pathlib import Path

FIELDS=('segment_id','filename','source_sha256','start_utc','end_utc','duration_s',
    'imu_type','mean_latitude_deg','mean_course_deg','minimum_ground_speed_kmh',
    'median_ground_speed_kmh')


def policy():
    return dict(version='ilvis0-prediction-pilot-selection-v1',maximum_stretches=3,
        population='unchanged 53 saved eligible stretches',
        cells='IMU type and latitude hemisphere; rare cells first, then IMU type/hemisphere',
        order_within_cell='longest duration, then segment ID',
        groups='at most one stretch per conservative provenance group',
        minimum_duration_s=240.,minimum_speed_kmh=700.,model_outcomes_used=False,
        raw_gyro_values_used=False,original_reads=0,observed_starts=0,
        independent_flights_established=False,protected_esa_data_used=False)


def select(cohort,provenance):
    lookup={}
    for row in provenance:
        if row['archive']!='ilvis0':continue
        if row['record_id'] in lookup:raise ValueError('duplicate recording provenance')
        lookup[row['record_id']]=row
    cells={};seen=set()
    for row in cohort:
        value={key:row[key] for key in FIELDS};identity=value['segment_id']
        if identity in seen:raise ValueError('duplicate saved stretch')
        seen.add(identity);record=lookup.get('ilvis0:'+identity)
        if (record is None or not record['group_id'] or record['role']!='retrospective_development'
                or any(record[k]!=value[k] for k in ('filename','source_sha256'))):
            raise ValueError('verified retrospective recording membership required')
        numbers=[float(value[k]) for k in ('duration_s','mean_latitude_deg','mean_course_deg',
            'minimum_ground_speed_kmh','median_ground_speed_kmh')]
        duration,latitude,course,minimum,median=numbers
        if (not all(math.isfinite(v) for v in numbers) or duration<policy()['minimum_duration_s']
                or minimum<policy()['minimum_speed_kmh'] or median<minimum
                or not -90<latitude<90 or not 0<=course<360 or value['imu_type'] not in ('8','21')
                or not all(value[k] for k in ('segment_id','filename','source_sha256','start_utc','end_utc'))):
            raise ValueError('unchanged eligible stretch and complete route metadata required')
        cell=(int(value['imu_type']),'north' if latitude>=0 else 'south')
        value.update(group_id=record['group_id'],hemisphere=cell[1])
        cells.setdefault(cell,[]).append(value)
    selected=[];groups=set()
    for cell in sorted(cells,key=lambda c:(len(cells[c]),c)):
        ordered=sorted(cells[cell],key=lambda v:(-float(v['duration_s']),v['segment_id']))
        chosen=next((v for v in ordered if v['group_id'] not in groups),None)
        if chosen is not None:selected.append(chosen);groups.add(chosen['group_id'])
        if len(selected)==policy()['maximum_stretches']:break
    return selected


def publish_selection(root,output='docs/ilvis0-prediction-pilot-preparation'):
    from lll.studies.artifacts import atomic,digest,encoded,safe_path
    root=Path(root).resolve();target=safe_path(root,output)
    names=('docs/ilvis0-current-findings-20261015/stretch-analytics.csv',
           'docs/analysis-provenance/recording-groups.csv')
    raw={n:(root/n).read_bytes() for n in names}
    cohort=list(csv.DictReader(io.StringIO(raw[names[0]].decode())))
    records=list(csv.DictReader(io.StringIO(raw[names[1]].decode())))
    if len(cohort)!=53:raise ValueError('the original 53-stretch cohort is required')
    chosen=select(cohort,records)
    if len(chosen)!=3:raise ValueError('three distinct available cells and conservative groups required')
    columns=(*FIELDS,'group_id','hemisphere');stream=io.StringIO(newline='')
    writer=csv.DictWriter(stream,fieldnames=columns,lineterminator='\n');writer.writeheader();writer.writerows(chosen)
    selection=stream.getvalue().encode();receipt=dict(policy=policy(),rows=len(chosen),
        input_sha256={n:digest(v) for n,v in raw.items()},selection_sha256=digest(selection),
        selector_sha256=digest(Path(__file__).read_bytes()),numerical_work=0,observed_starts=0)
    target.mkdir(parents=True,exist_ok=True)
    atomic(target/'selection.csv',selection);atomic(target/'selection-receipt.json',encoded(receipt))
    return receipt
