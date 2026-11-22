# SPDX-License-Identifier: AGPL-3.0-or-later
"""Publish saved receiver/motion candidates without reopening IMU originals."""

import csv
from datetime import date, datetime, time, timedelta, timezone
import hashlib
import io
import json
import math
from pathlib import Path

from .studies.artifacts import atomic, encoded
from .studies.closed import ClosedStudy


STUDY = 'data/ilvis0-distance-inventory-20261116'
OUTPUT = 'docs/ilvis0-distance-inventory'
FILE_FIELDS = ('task','filename','source_sha256','canonical_task','state',
               'candidate_stretches','recorded_dates','reason')
STRETCH_FIELDS = ('segment_id','task','filename','source_sha256','date_group',
                  'start_utc','end_utc','duration_s','receiver_distance_km',
                  'minimum_ground_speed_kmh','median_ground_speed_kmh',
                  'receiver_fixes','first_latitude_deg','first_longitude_deg',
                  'last_latitude_deg','last_longitude_deg','imu_type',
                  'mounting_signature')


def _csv(fields, rows):
    stream=io.StringIO(newline='')
    writer=csv.DictWriter(stream,fieldnames=fields,lineterminator='\n')
    writer.writeheader();writer.writerows(rows)
    return stream.getvalue().encode('utf-8')


def _utc(week_s, recorded_dates):
    days=[date.fromisoformat(value) for value in recorded_dates]
    sundays={day-timedelta(days=(day.weekday()+1)%7) for day in days}
    if len(sundays)!=1:
        raise ValueError('candidate lacks one supported UTC week')
    sunday=datetime.combine(sundays.pop(),time(),timezone.utc)
    return (sunday+timedelta(seconds=week_s)).isoformat().replace('+00:00','Z')


def build_rows(tasks, results, contexts):
    """Deduplicate source aliases and group by connected recording dates."""
    by_task={row['task_id']:row for row in contexts['results']}
    if set(tasks)!=set(results) or not set(tasks)<=set(by_task):
        raise ValueError('task, result and UTC context identities differ')
    canonical={};canonical_result={};files=[];stretches=[];parent={}
    def root(day):
        parent.setdefault(day,day)
        while parent[day]!=day:
            day=parent[day]
        return day
    def join(a,b):
        a,b=root(a),root(b)
        if a!=b:parent[max(a,b)]=min(a,b)
    for task_id in sorted(tasks):
        task=tasks[task_id];result=results[task_id]
        if (result['identity']!=task_id or
                result['source_sha256']!=task['source_sha256'] or
                result['filename']!=task['filename'] or
                result['earth_model_fits']!=0 or
                result['gyro_residuals_inspected'] or
                result['scientific_decision']!='abstain'):
            raise ValueError('saved inventory identity or scientific scope changed')
        dates=sorted(set(by_task[task_id]['timing']['dates']))
        sha=task['source_sha256']
        alias=canonical.setdefault(sha,task_id)
        if alias!=task_id and (result['state'],result['segments'])!=canonical_result[sha]:
            raise ValueError('byte-identical source aliases have different selections')
        canonical_result.setdefault(sha,(result['state'],result['segments']))
        files.append(dict(task=task_id,filename=task['filename'],
            source_sha256=sha,canonical_task=alias,state=result['state'],
            candidate_stretches=len(result['segments']) if alias==task_id else 0,
            recorded_dates=';'.join(dates),reason=result.get('reason','')))
        if alias!=task_id:continue
        if result['segments'] and not dates:
            raise ValueError('candidate has no supported date')
        for day in dates[1:]:join(dates[0],day)
        for segment in result['segments']:
            first=segment['first_receiver_fix'];last=segment['last_receiver_fix']
            if (segment['duration_s']<600 or segment['receiver_distance_m']<50000 or
                    segment['minimum_receiver_ground_speed_kmh']<180 or
                    segment['receiver_fixes_count']<2 or not first or not last):
                raise ValueError('candidate fails frozen distance or receiver geometry rule')
            lat=lambda value:math.degrees(value['latitude_rad'])
            lon=lambda value:math.degrees(value['longitude_rad'])
            stretches.append(dict(segment_id=segment['segment_id'],task=task_id,
                filename=task['filename'],source_sha256=sha,date_group=dates[0],
                start_utc=_utc(segment['start_s'],dates),
                end_utc=_utc(segment['end_s'],dates),
                duration_s=segment['duration_s'],
                receiver_distance_km=segment['receiver_distance_m']/1000,
                minimum_ground_speed_kmh=segment['minimum_receiver_ground_speed_kmh'],
                median_ground_speed_kmh=segment['median_receiver_ground_speed_kmh'],
                receiver_fixes=segment['receiver_fixes_count'],
                first_latitude_deg=lat(first),first_longitude_deg=lon(first),
                last_latitude_deg=lat(last),last_longitude_deg=lon(last),
                imu_type=segment['imu_type'],
                mounting_signature=segment['signature']))
    for row in stretches:row['date_group']=root(row['date_group'])
    stretches.sort(key=lambda row:(row['date_group'],row['start_utc'],row['task']))
    if len({row['segment_id'] for row in stretches})!=len(stretches):
        raise ValueError('duplicate candidate identity')
    return files,stretches


def publish(root='.'):
    project=Path(root).resolve();study=ClosedStudy(project,STUDY)
    try:
        if len(study.tasks)!=232 or study.summary['completed']!=232:
            raise ValueError('complete 232-file inventory required')
        results={task:study.artifact(task,'inventory.json') for task in study.tasks}
        files,stretches=build_rows(study.tasks,results,study.input('contexts'))
        blobs={'files.csv':_csv(FILE_FIELDS,files),
               'candidates.csv':_csv(STRETCH_FIELDS,stretches)}
        groups=len({row['date_group'] for row in stretches})
        passing=sum(result['passed'] for result in results.values())
        minutes=sum(row['duration_s'] for row in stretches)/60
        page='\n'.join([
            '# Longer-flight candidate inventory','',
            f'The separate receiver-and-motion scan checked {len(files)} retained '
            f'recordings. {passing} passed strict parsing; {len(files)-passing} '
            'were recorded as unsupported or invalid.','',
            f'The fixed rule found **{len(stretches)} candidate stretches** '
            f'totaling {minutes:.1f} minutes, on **{groups} conservative '
            'recorded-date groups**. Same-day and overlapping recorders count '
            'together. These groups are not established independent flights.','',
            'The selection uses receiver speed and position, fused-navigation '
            'motion screening and raw-stream completeness. It uses no gyro '
            'model residuals and makes no Earth-model fits. The original '
            '53-stretch study is unchanged.','',
            'The [candidate table](candidates.csv) gives each stretch’s time, '
            'distance, speed, endpoints, source and date group. The '
            '[file ledger](files.csv) includes sources with no candidate and '
            'sources that failed strict decoding.','',
            'The next step is to verify flight provenance and model information '
            'for these candidates before deciding whether any can contribute '
            'to an independent uncertainty study. This inventory alone '
            'establishes no prediction coverage or Earth-model detection.',''])+'\n'
        blobs['RESULT.md']=page.encode('utf-8')
        receipt=dict(version='ilvis0-distance-inventory-publication-v1',
            study=STUDY,manifest_sha256=study.completion['manifest_sha256'],
            summary_sha256=study.completion['summary_sha256'],
            files=len(files),passing_files=passing,
            canonical_files=len({row['canonical_task'] for row in files}),
            candidate_stretches=len(stretches),conservative_date_groups=groups,
            candidate_minutes=minutes,
            date_groups_are_independent_flights=False,earth_model_fits=0,
            artifact_sha256={name:hashlib.sha256(blob).hexdigest() for name,blob in blobs.items()})
        blobs['receipt.json']=encoded(receipt)
        destination=project/OUTPUT;destination.mkdir(parents=True,exist_ok=True)
        for name,blob in blobs.items():
            path=destination/name
            if path.is_file():
                if path.read_bytes()!=blob:
                    raise ValueError('existing public inventory differs: '+name)
            else:atomic(path,blob)
        return receipt
    finally:study.close()


if __name__=='__main__':
    print(json.dumps(publish(),sort_keys=True))
