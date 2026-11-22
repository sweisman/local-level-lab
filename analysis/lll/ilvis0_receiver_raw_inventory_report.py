# SPDX-License-Identifier: AGPL-3.0-or-later
"""Publish broad receiver/raw candidates from sealed scan results only."""

import hashlib
import json
from pathlib import Path

from .ilvis0_distance_inventory_report import (
    build_rows, _csv, FILE_FIELDS, STRETCH_FIELDS)
from .studies.artifacts import atomic, encoded
from .studies.closed import ClosedStudy


STUDY='data/ilvis0-receiver-raw-inventory-20261116'
OUTPUT='docs/ilvis0-receiver-raw-inventory'


def publish(root='.'):
    project=Path(root).resolve();study=ClosedStudy(project,STUDY)
    try:
        if len(study.tasks)!=232 or study.summary['completed']!=232:
            raise ValueError('complete 232-file receiver/raw inventory required')
        results={identity:study.artifact(identity,'inventory.json')
                 for identity in study.tasks}
        files,stretches=build_rows(study.tasks,results,study.input('contexts'))
        for row in stretches:row['level_motion_screened']=False
        fields=(*STRETCH_FIELDS,'level_motion_screened')
        groups=len({row['date_group'] for row in stretches})
        minutes=sum(row['duration_s'] for row in stretches)/60
        passing=sum(result['passed'] for result in results.values())
        page='\n'.join([
            '# Receiver-supported flight candidates','',
            f'The separately fixed scan checked {len(files)} retained recordings. '
            f'{passing} passed strict parsing; {len(files)-passing} were '
            'recorded as unsupported or invalid.','',
            f'It found **{len(stretches)} candidate trajectories** totaling '
            f'{minutes:.1f} minutes on **{groups} conservative recorded-date '
            'groups**. Same-day and overlapping recorders count together. '
            'These are not established independent flights.','',
            'Each candidate has at least 10 continuous minutes, 50 km of '
            'sampled receiver path, receiver speed at least 180 km/h, and '
            'complete supported raw IMU timing. Selection does not use '
            'fused-navigation alignment, roll, climb or course-rate flags. '
            '**Level flight has not been established**: turns and climbs may '
            'remain. No gyro model residual or Earth-model fit was used.','',
            'The [candidate table](candidates.csv) shows time, distance, '
            'speed, receiver endpoints, recorder and date group. The '
            '[file ledger](files.csv) includes empty and invalid sources.','',
            'The next gate is a separately fixed receiver-geometry and motion '
            'check, then an information test under the full nuisance space. '
            'These candidates cannot enter a coverage or Earth-model claim '
            'from this inventory alone. The original 53-stretch study and '
            'seven reserved ESA groups remain unchanged.',''])+'\n'
        blobs={'files.csv':_csv(FILE_FIELDS,files),
               'candidates.csv':_csv(fields,stretches),
               'RESULT.md':page.encode('utf-8')}
        receipt=dict(version='ilvis0-receiver-raw-inventory-publication-v1',
            study=STUDY,manifest_sha256=study.completion['manifest_sha256'],
            summary_sha256=study.completion['summary_sha256'],
            files=len(files),passing_files=passing,
            canonical_files=len({row['canonical_task'] for row in files}),
            candidate_trajectories=len(stretches),conservative_date_groups=groups,
            candidate_minutes=minutes,level_flight_established=False,
            independent_flights_established=False,earth_model_fits=0,
            artifact_sha256={name:hashlib.sha256(blob).hexdigest()
                             for name,blob in blobs.items()})
        blobs['receipt.json']=encoded(receipt)
        destination=project/OUTPUT;destination.mkdir(parents=True,exist_ok=True)
        for name,blob in blobs.items():
            path=destination/name
            if path.is_file():
                if path.read_bytes()!=blob:
                    raise ValueError('existing receiver/raw inventory differs: '+name)
            else:atomic(path,blob)
        return receipt
    finally:study.close()


if __name__=='__main__':
    print(json.dumps(publish(),sort_keys=True))
