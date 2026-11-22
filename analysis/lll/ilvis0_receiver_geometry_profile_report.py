# SPDX-License-Identifier: AGPL-3.0-or-later
"""Publish sealed receiver-only contrast geometry without Earth-model fits."""

import csv
import hashlib
import io
import json
from pathlib import Path
import statistics

from .studies.artifacts import atomic,encoded
from .studies.closed import ClosedStudy


STUDY='data/ilvis0-receiver-geometry-profile-20261116'
OUTPUT='docs/ilvis0-receiver-geometry-profile'
FILE_FIELDS=('task','segment_id','filename','date_group','passed','reason',
             'supported_epochs')
GEOMETRY_FIELDS=('task','segment_id','filename','date_group','duration_s',
                 'treatment','pair','retained_fraction',
                 'retained_vector_rms_deg_hour','total_vector_rms_deg_hour',
                 'worst_crab_deg','worst_roll_deg','worst_pitch_deg',
                 'worst_model_anchor','nuisance_rank')


def _csv(fields,rows):
    stream=io.StringIO(newline='');writer=csv.DictWriter(
        stream,fieldnames=fields,lineterminator='\n')
    writer.writeheader();writer.writerows(rows)
    return stream.getvalue().encode('utf-8')


def publish(root='.'):
    project=Path(root).resolve();study=ClosedStudy(project,STUDY)
    try:
        if len(study.tasks)!=29 or study.summary['completed']!=29:
            raise ValueError('complete 29-candidate geometry study required')
        candidates=list(csv.DictReader(io.StringIO(
            study.input('candidates',raw=True).decode('utf-8'))))
        if len(candidates)!=29 or {r['task'] for r in candidates}!=set(study.tasks):
            raise ValueError('candidate and study task identities differ')
        files=[];scores=[]
        for candidate in candidates:
            identity=candidate['task'];result=study.envelope(identity)['result']
            if result['identity']!=identity or result.get('earth_model_fits',0)!=0:
                raise ValueError('saved task identity or scientific scope differs')
            file=dict(task=identity,segment_id=candidate['segment_id'],
                      filename=candidate['filename'],date_group=candidate['date_group'],
                      passed=bool(result['passed']),reason='',supported_epochs='')
            if result['passed']:
                saved=study.artifact(identity,'geometry.json')
                profile=saved['profile']
                if (saved['segment_id']!=candidate['segment_id'] or
                        saved['source_sha256']!=candidate['source_sha256'] or
                        saved['scientific_decision']!='abstain' or
                        saved['earth_model_fits']!=0 or
                        saved['gyro_residuals_inspected'] or
                        profile['gyro_observations_used'] or
                        profile['aircraft_motion_independently_known']):
                    raise ValueError('saved geometry evidence differs')
                file['supported_epochs']=profile['supported_epochs']
                for treatment,pairs in profile['conditional_geometry']['comparisons'].items():
                    for pair,score in pairs.items():
                        state=score['worst_state']
                        scores.append(dict(task=identity,
                            segment_id=candidate['segment_id'],
                            filename=candidate['filename'],
                            date_group=candidate['date_group'],
                            duration_s=candidate['duration_s'],
                            treatment=treatment,pair=pair,
                            retained_fraction=score['retained_fraction'],
                            retained_vector_rms_deg_hour=score['retained_vector_rms_deg_hour'],
                            total_vector_rms_deg_hour=score['total_vector_rms_deg_hour'],
                            worst_crab_deg=state['crab_deg'],
                            worst_roll_deg=state['roll_deg'],
                            worst_pitch_deg=state['pitch_deg'],
                            worst_model_anchor=state['model_anchor'],
                            nuisance_rank=score['nuisance_rank']))
            else:file['reason']=result.get('reason',result.get('error','task failed'))
            files.append(file)
        files.sort(key=lambda r:(r['date_group'],r['task']))
        scores.sort(key=lambda r:(r['date_group'],r['task'],r['treatment'],r['pair']))
        if len(scores)!=9*sum(file['passed'] for file in files):
            raise ValueError('three pairs and treatments required per passing task')
        strongest=[r for r in scores if r['treatment']=='linear_drift_gain_mount_tangents']
        medians={pair:statistics.median(float(r['retained_fraction'])
                 for r in strongest if r['pair']==pair)
                 for pair in sorted({r['pair'] for r in strongest})}
        page='\n'.join([
            '# Conditional contrast geometry in longer tracks','',
            f'The fixed study closed {len(files)} preselected candidate tasks. '
            f'{sum(file["passed"] for file in files)} produced complete '
            'conditional pairwise profiles; the other tasks remain in the '
            '[file ledger](files.csv). No recorded gyro residual or Earth-model '
            'fit was used.','',
            'The [pairwise table](geometry.csv) lists all three model pairs '
            'under constant bias, bias plus drift, and the wider local '
            'gain/mount tangent treatment. The reported retention is the '
            'worst over the declared crab, roll, pitch and model anchors. '
            'It is a fraction of a **predicted rate contrast**, not detection '
            'power or a test result.','',
            'Median retained fractions under the widest local nuisance '
            'treatment are: '+', '.join(f'`{pair}` {value:.4g}'
                                       for pair,value in medians.items())+'.','',
            '**Aircraft rotation is assumed independently removable in this '
            'geometry calculation.** The available receiver fixes do not '
            'supply body attitude or a calibrated error law. With unrestricted '
            'aircraft rotation, all these rate contrasts can be absorbed. '
            'A favorable table entry therefore cannot promote a track to '
            'scientific eligibility. The original 53-stretch study and '
            'reserved ESA groups remain unchanged.',''])+'\n'
        blobs={'files.csv':_csv(FILE_FIELDS,files),
               'geometry.csv':_csv(GEOMETRY_FIELDS,scores),
               'RESULT.md':page.encode('utf-8')}
        receipt=dict(version='ilvis0-receiver-geometry-profile-publication-v1',
                     study=STUDY,manifest_sha256=study.completion['manifest_sha256'],
                     summary_sha256=study.completion['summary_sha256'],
                     candidates=len(files),passing=sum(f['passed'] for f in files),
                     pairwise_rows=len(scores),median_retained_fraction=medians,
                     earth_model_fits=0,scientific_decisions=0,
                     artifact_sha256={name:hashlib.sha256(raw).hexdigest()
                                      for name,raw in blobs.items()})
        blobs['receipt.json']=encoded(receipt)
        output=project/OUTPUT;output.mkdir(parents=True,exist_ok=True)
        for name,raw in blobs.items():
            path=output/name
            if path.is_file():
                if path.read_bytes()!=raw:raise ValueError('geometry publication differs')
            else:atomic(path,raw)
        return receipt
    finally:study.close()


if __name__=='__main__':
    print(json.dumps(publish(),sort_keys=True))
