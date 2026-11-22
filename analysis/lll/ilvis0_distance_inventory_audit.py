# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved-only audit of the completed longer-flight screening tallies."""

from collections import Counter
import csv
import hashlib
import io
import json
from pathlib import Path

from .studies.artifacts import atomic, encoded
from .studies.closed import ClosedStudy


STUDY = 'data/ilvis0-distance-inventory-20261116'
OUTPUT = 'docs/ilvis0-distance-inventory'
SAMPLE_FLAGS = frozenset((
    'missing_motion_context','missing_receiver_support','below_ground_speed',
    'excessive_vertical_speed','excessive_roll','excessive_course_rate',
    'incomplete_alignment'))
SPAN_FLAGS = frozenset((
    'short_after_buffers_or_raw_intersection','below_sampled_receiver_distance'))


def summarize(results):
    """Count flags separately; overlapping flags are never treated as files."""
    counts=Counter();files=Counter();states=Counter()
    for result in results:
        states[result['state']]+=1
        reasons=result.get('rejections',{})
        if any(type(value) is not int or value<0 for value in reasons.values()):
            raise ValueError('nonnegative integer screening tallies required')
        counts.update(reasons)
        files.update(key for key,value in reasons.items() if value)
    rows=[]
    for name in sorted(counts):
        phase=('sample flags' if name in SAMPLE_FLAGS else
               'candidate spans' if name in SPAN_FLAGS else
               'packet or receiver context')
        rows.append(dict(reason=name,phase=phase,tally=counts[name],
                         files_with_flag=files[name]))
    return dict(files=len(results),states=dict(states),rows=rows,
                counts_overlap=True,unique_causes_identified=False)


def publish(root='.'):
    project=Path(root).resolve();study=ClosedStudy(project,STUDY)
    try:
        if study.completion['state']!='complete' or len(study.tasks)!=232:
            raise ValueError('complete 232-file inventory required')
        results=[study.artifact(identity,'inventory.json')
                 for identity in sorted(study.tasks)]
        audit=summarize(results)
        table=io.StringIO(newline='')
        writer=csv.DictWriter(table,fieldnames=('reason','phase','tally','files_with_flag'),
                              lineterminator='\n')
        writer.writeheader();writer.writerows(audit['rows'])
        rows={row['reason']:row for row in audit['rows']}
        name=('incomplete_alignment','excessive_course_rate',
              'below_ground_speed','short_after_buffers_or_raw_intersection',
              'below_sampled_receiver_distance')
        lines=['# Why the longer-flight rule found few candidates','',
               'All 232 strict file scans completed. Five files yielded a candidate; '
               '227 did not. The following are saved screening tallies, not '
               'independent flight counts or unique explanations. A sample can '
               'trigger several flags.','',
               '| Flag | Tally | Files with flag |',
               '|---|---:|---:|']
        for key in name:
            row=rows.get(key,dict(tally=0,files_with_flag=0))
            lines.append(f'| `{key}` | {row["tally"]:,} | {row["files_with_flag"]} |')
        lines.extend(('',
            'Alignment, speed and course-rate flags count screened motion '
            'samples. Short-after-buffer and distance flags count candidate '
            'spans. Their tallies have different units and cannot be added. '
            'The [complete rejection table](rejection-counts.csv) preserves '
            'every recorded flag.','',
            'The large alignment tally is a warning about depending on the '
            'instrument’s fused navigation status for screening. It does not '
            'prove that otherwise excluded raw IMU and receiver data can '
            'distinguish Earth models. A separately fixed receiver-only '
            'candidate inventory would be required to test that question. '
            'The original 53-stretch study remains unchanged.',''))
        blobs={'rejection-counts.csv':table.getvalue().encode('utf-8'),
               'REJECTION_AUDIT.md':'\n'.join(lines).encode('utf-8')}
        receipt=dict(version='ilvis0-distance-inventory-rejection-audit-v1',
            study=STUDY,manifest_sha256=study.completion['manifest_sha256'],
            summary_sha256=study.completion['summary_sha256'],
            files=audit['files'],states=audit['states'],
            counts_overlap=True,unique_causes_identified=False,
            artifact_sha256={name:hashlib.sha256(blob).hexdigest()
                             for name,blob in blobs.items()})
        blobs['rejection-audit-receipt.json']=encoded(receipt)
        destination=project/OUTPUT
        for name,blob in blobs.items():
            target=destination/name
            if target.is_file():
                if target.read_bytes()!=blob:
                    raise ValueError('existing rejection audit differs: '+name)
            else:atomic(target,blob)
        return receipt
    finally:study.close()


if __name__=='__main__':
    print(json.dumps(publish(),sort_keys=True))
