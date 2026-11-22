# SPDX-License-Identifier: AGPL-3.0-or-later
"""Publish the sealed alignment-status ablation without model fitting."""

import hashlib
import json
from pathlib import Path

from .ilvis0_distance_inventory_report import (
    build_rows, _csv, FILE_FIELDS, STRETCH_FIELDS)
from .studies.artifacts import atomic, encoded
from .studies.closed import ClosedStudy


STUDY='data/ilvis0-alignment-ablation-20261116'
OUTPUT='docs/ilvis0-alignment-ablation'


def publish(root='.'):
    project=Path(root).resolve();study=ClosedStudy(project,STUDY)
    try:
        if len(study.tasks)!=29 or study.summary['completed']!=29:
            raise ValueError('complete 29-file alignment ablation required')
        results={identity:study.artifact(identity,'inventory.json')
                 for identity in study.tasks}
        files,stretches=build_rows(study.tasks,results,study.input('contexts'))
        passing=sum(result['passed'] for result in results.values())
        groups=len({row['date_group'] for row in stretches})
        minutes=sum(row['duration_s'] for row in stretches)/60
        page='\n'.join([
            '# Alignment-status screening ablation','',
            f'The fixed ablation scanned {len(files)} sources previously '
            'selected by receiver/raw support. '
            f'{passing} passed strict parsing and {len(files)-passing} '
            'were retained as invalid or unsupported.','',
            f'With the fused alignment-status veto removed, but the original '
            f'speed, climb, roll, course-rate, gap and raw-completeness '
            f'checks retained, it found **{len(stretches)} candidate '
            f'stretches** totaling **{minutes:.1f} minutes** on '
            f'**{groups} recorded-date groups**.','',
            'The [candidate table](candidates.csv) lists every recovered '
            'interval. The [file ledger](files.csv) also records sources '
            'with no candidate. No gyro model residual was inspected and '
            'no Earth-model fit was run.','',
            '**These are not newly eligible scientific flights.** Group 1 '
            'motion comes from a fused navigation solution; its roll, climb '
            'and course values may be less dependable when its own alignment '
            'flag is false. A separate receiver-motion check and full '
            'nuisance-information gate are required before fitting. The '
            'original 53-stretch study remains unchanged.',''])+'\n'
        blobs={'files.csv':_csv(FILE_FIELDS,files),
               'candidates.csv':_csv(STRETCH_FIELDS,stretches),
               'RESULT.md':page.encode('utf-8')}
        receipt=dict(version='ilvis0-alignment-ablation-publication-v1',
            study=STUDY,manifest_sha256=study.completion['manifest_sha256'],
            summary_sha256=study.completion['summary_sha256'],files=len(files),
            passing_files=passing,candidate_stretches=len(stretches),
            conservative_date_groups=groups,candidate_minutes=minutes,
            alignment_status_required=False,scientific_eligible=False,
            earth_model_fits=0,
            artifact_sha256={name:hashlib.sha256(raw).hexdigest()
                             for name,raw in blobs.items()})
        blobs['receipt.json']=encoded(receipt)
        output=project/OUTPUT;output.mkdir(parents=True,exist_ok=True)
        for name,raw in blobs.items():
            path=output/name
            if path.is_file():
                if path.read_bytes()!=raw:raise ValueError('ablation publication differs')
            else:atomic(path,raw)
        return receipt
    finally:study.close()


if __name__=='__main__':
    print(json.dumps(publish(),sort_keys=True))
