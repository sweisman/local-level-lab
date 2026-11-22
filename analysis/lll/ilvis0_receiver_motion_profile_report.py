# SPDX-License-Identifier: AGPL-3.0-or-later
"""Publish receiver-only motion summaries from sealed 29-task results."""

import csv
import hashlib
import io
import json
from pathlib import Path

from .studies.artifacts import atomic, encoded
from .studies.closed import ClosedStudy


STUDY='data/ilvis0-receiver-motion-profile-20261116'
OUTPUT='docs/ilvis0-receiver-motion-profile'
METRICS=('supported_velocity_epochs','supported_course_rate_epochs',
         'height_span_m','median_speed_kmh','minimum_speed_kmh','course_span_deg',
         'p95_abs_climb_mps','max_abs_climb_mps',
         'p95_abs_course_rate_deg_s','max_abs_course_rate_deg_s')


def _csv(fields,rows):
    stream=io.StringIO(newline='')
    writer=csv.DictWriter(stream,fieldnames=fields,lineterminator='\n')
    writer.writeheader();writer.writerows(rows)
    return stream.getvalue().encode('utf-8')


def publish(root='.'):
    project=Path(root).resolve();study=ClosedStudy(project,STUDY)
    try:
        if len(study.tasks)!=29 or study.summary['completed']!=29:
            raise ValueError('complete 29-candidate motion study required')
        original=list(csv.DictReader(io.StringIO(
            study.input('candidates',raw=True).decode('utf-8'))))
        if len(original)!=29 or {r['task'] for r in original}!=set(study.tasks):
            raise ValueError('candidate and sealed task identities differ')
        rows=[]
        for row in original:
            identity=row['task'];result=study.envelope(identity)['result']
            if result['identity']!=identity or result.get('earth_model_fits',0)!=0:
                raise ValueError('motion result identity or scientific scope changed')
            output=dict(row,passed=bool(result['passed']),reason='')
            if result['passed']:
                evidence=study.artifact(identity,'motion.json')
                if (evidence['segment_id']!=row['segment_id'] or
                        evidence['source_sha256']!=row['source_sha256'] or
                        evidence['profile']['receiver_fixes']!=int(row['receiver_fixes']) or
                        evidence['scientific_decision']!='abstain' or
                        evidence['earth_model_fits']!=0 or
                        evidence['gyro_residuals_inspected']):
                    raise ValueError('saved motion evidence differs from candidate')
                output.update({key:evidence['profile'][key] for key in METRICS})
            else:output['reason']=result.get('reason',result.get('error','task failed'))
            rows.append(output)
        rows.sort(key=lambda r:(r['date_group'],r['start_utc'],r['task']))
        fields=(*original[0].keys(),'passed','reason',*METRICS)
        passing=[r for r in rows if r['passed']]
        elevated_climb=sum(float(r['p95_abs_climb_mps'])>1.5 for r in passing)
        elevated_turn=sum(float(r['p95_abs_course_rate_deg_s'])>.05 for r in passing)
        page='\n'.join([
            '# Receiver motion in longer flight candidates','',
            f'The fixed profile closed {len(rows)} preselected candidate tasks; '
            f'{len(passing)} produced complete receiver-motion summaries and '
            f'{len(rows)-len(passing)} did not. No Earth-model fit was run.','',
            'The [per-candidate table](motion.csv) reports recorded course '
            'change, climb, speed and measurement support. Thirty-second '
            'receiver-coordinate regressions reduce single-fix jitter; '
            'unsupported endpoints and gaps are not filled. The WGS84 metric '
            'is used only to describe motion in the receiver coordinate chart.','',
            f'For context, {elevated_climb} of {len(passing)} profiles have '
            '95th-percentile absolute climb above 1.5 m/s, and '
            f'{elevated_turn} have 95th-percentile absolute course-change '
            'above 0.05 degree/s. These are reference values from the earlier '
            'fused-motion screen, **not acceptance decisions**. Receiver '
            'course is not aircraft heading; these summaries cannot establish '
            'roll or eliminate wind crab.','',
            'Next, freeze a receiver-motion selection and a full nuisance '
            'information check before using any new interval in Earth-model '
            'fitting. The original 53 selected stretches and reserved ESA '
            'groups remain unchanged.',''])+'\n'
        blobs=dict(motion_csv=_csv(fields,rows),result_md=page.encode('utf-8'))
        output={'motion.csv':blobs['motion_csv'],'RESULT.md':blobs['result_md']}
        receipt=dict(version='ilvis0-receiver-motion-profile-publication-v1',
                     study=STUDY,manifest_sha256=study.completion['manifest_sha256'],
                     summary_sha256=study.completion['summary_sha256'],
                     candidates=len(rows),passing=len(passing),
                     p95_climb_above_reference=elevated_climb,
                     p95_course_rate_above_reference=elevated_turn,
                     earth_model_fits=0,scientific_decisions=0,
                     artifact_sha256={name:hashlib.sha256(raw).hexdigest()
                                      for name,raw in output.items()})
        output['receipt.json']=encoded(receipt)
        destination=project/OUTPUT;destination.mkdir(parents=True,exist_ok=True)
        for name,blob in output.items():
            path=destination/name
            if path.exists():
                if path.read_bytes()!=blob:raise ValueError('published motion profile differs')
            else:atomic(path,blob)
        return receipt
    finally:study.close()


if __name__=='__main__':
    print(json.dumps(publish(),sort_keys=True))
