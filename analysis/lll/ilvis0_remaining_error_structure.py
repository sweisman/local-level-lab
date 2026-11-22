# SPDX-License-Identifier: AGPL-3.0-or-later
"""Describe sealed later-cut forecast errors without refitting or originals."""

import csv
import hashlib
import io
import math
import statistics
from pathlib import Path

from .ilvis0_remaining_prediction_report import MANIFEST_SHA256, STUDY

AXES=('north','east','up')


def _correlation(left,right):
    if len(left)<2:
        return None
    a=statistics.mean(left); b=statistics.mean(right)
    x=[value-a for value in left]; y=[value-b for value in right]
    denominator=math.sqrt(sum(value*value for value in x)*
                          sum(value*value for value in y))
    return sum(u*v for u,v in zip(x,y))/denominator if denominator else None


def describe_epochs(rows):
    """Describe signed errors on the forecast portion only."""
    if not isinstance(rows,list) or len(rows)<3:
        raise ValueError('training and at least two prediction epochs required')
    roles=[row.get('role') for row in rows]
    training=roles.count('training')
    if (training<1 or len(rows)-training<2 or
            roles!=['training']*training+['prediction']*(len(rows)-training)):
        raise ValueError('training must precede prediction')
    for index,row in enumerate(rows):
        if (row.get('epoch')!=index or
                not isinstance(row.get('time_s'),(int,float)) or
                not math.isfinite(row['time_s']) or
                (index and row['time_s']<=rows[index-1]['time_s']) or
                any(not isinstance(row.get(axis+'_direct_error_m'),(int,float)) or
                        not math.isfinite(row[axis+'_direct_error_m'])
                        for axis in AXES)):
            raise ValueError('ordered finite saved epochs required')
    later=rows[training:]
    times=[row['time_s'] for row in later]
    mean_time=statistics.mean(times)
    centered_time=[value-mean_time for value in times]
    time_sum=sum(value*value for value in centered_time)
    answer={}
    for axis in AXES:
        values=[row[axis+'_direct_error_m'] for row in later]
        mean=statistics.mean(values)
        answer[axis]=dict(mean_m=mean,
            rms_m=math.sqrt(statistics.mean(value*value for value in values)),
            final_m=values[-1],
            slope_m_per_min=60*sum(t*(v-mean) for t,v in
                                   zip(centered_time,values))/time_sum,
            lag1_correlation=_correlation(values[:-1],values[1:]))
    return dict(training_epochs=training,prediction_epochs=len(later),
                prediction_duration_s=times[-1]-times[0],axes=answer)


def describe_groups(rows,load_epochs):
    if not isinstance(rows,list) or len(rows)!=20:
        raise ValueError('exact twenty selected groups required')
    segments=set(); identities=set(); result=[]
    for row in rows:
        segment=row.get('segment_id')
        identity=row.get('outer_identity')
        if not isinstance(segment,str) or not segment or segment in segments:
            raise ValueError('unique selected group required')
        segments.add(segment)
        if identity is not None:
            if not isinstance(identity,str) or not identity or identity in identities:
                raise ValueError('unique sealed outer fit required')
            identities.add(identity)
        result.append(dict(segment_id=segment,outer_identity=identity,
                           error_structure=(describe_epochs(load_epochs(identity))
                                            if identity else None)))
    return dict(groups=20,scored_groups=len(identities),
                unscored_groups=20-len(identities),rows=result,
                scientific_decision='abstain',coverage_calibrated=False)


def build(root='.'):
    from .ilvis0_remaining_prediction_report import build as parent_build
    from .studies.closed import ClosedStudy
    root=Path(root).resolve()
    parent=parent_build(root)
    study=ClosedStudy(root,STUDY)
    try:
        if (study.completion['manifest_sha256']!=MANIFEST_SHA256 or
                study.completion['summary_sha256']!=parent['summary_sha256']):
            raise ValueError('saved parent study differs')
        report=describe_groups(parent['rows'],
                               lambda identity:study.artifact(identity,'epochs.json'))
        if report['scored_groups']!=9 or parent['assessment']['abstentions']!=11:
            raise ValueError('frozen nine-score accounting differs')
        report.update(version='ilvis0-twenty-group-error-structure-v1',
            parent_manifest_sha256=MANIFEST_SHA256,
            parent_summary_sha256=parent['summary_sha256'],
            source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            original_reads=0,protected_reads=0,native_calls=0)
        return report
    finally:
        study.close()


def csv_bytes(report):
    fields=['segment_id','outer_identity','prediction_epochs',
            'prediction_duration_s']
    for axis in AXES:
        fields += [axis+'_'+key for key in
                   ('mean_m','rms_m','final_m','slope_m_per_min','lag1_correlation')]
    stream=io.StringIO(newline='')
    writer=csv.DictWriter(stream,fieldnames=fields,lineterminator='\n')
    writer.writeheader()
    for row in report['rows']:
        item={key:row.get(key) for key in fields}
        structure=row['error_structure']
        if structure:
            item.update(prediction_epochs=structure['prediction_epochs'],
                        prediction_duration_s=structure['prediction_duration_s'])
            for axis,metrics in structure['axes'].items():
                item.update({axis+'_'+key:value for key,value in metrics.items()})
        writer.writerow(item)
    return stream.getvalue().encode()


def render(report):
    rows=[row['error_structure'] for row in report['rows']
          if row['error_structure']]
    def median(axis,key):
        return statistics.median(row['axes'][axis][key] for row in rows)
    def median_correlation(axis):
        values=[row['axes'][axis]['lag1_correlation'] for row in rows]
        available=[value for value in values if value is not None]
        return f'{statistics.median(available):.4f}' if available else '—'
    lines=['# Error patterns in saved aircraft forecasts','',
        'Nine of twenty selected recording groups have a usable later-cut '
        'forecast. The other eleven remain in the denominator as unscorable '
        'numerical outcomes. This audit uses the saved forecast errors only; '
        'it makes no new fit or model comparison.','',
        '| Later-position error | North | East | Height |',
        '|---|---:|---:|---:|',
        '| Median RMS across nine groups | '+ ' | '.join(
            f'{median(axis,"rms_m"):.2f} m' for axis in AXES)+' |',
        '| Median absolute trend | '+' | '.join(
            f'{statistics.median(abs(row["axes"][axis]["slope_m_per_min"])
              for row in rows):.2f} m/min' for axis in AXES)+' |',
        '| Median adjacent-epoch correlation | '+' | '.join(
            median_correlation(axis) for axis in AXES)+' |','',
        'A trend is a linear summary of each forecast error, not an independent '
        'estimate of sensor drift. The CSV also records signed means, final '
        'errors and adjacent-epoch correlations for each group. These '
        'correlations include slow trends, so they do not measure a stationary '
        'noise process.','',
        'All nine scored groups passed the fixed development reference and '
        'separate physical screen in the [parent report]'
        '(REMAINING_GROUPS_PREDICTION_RESULT.md). Eleven could not be scored. '
        'This selected, same-archive sample does not calibrate uncertainty, '
        'establish prediction coverage or support a scientific detection.','',
        '[Per-group saved error audit](remaining-error-structure.csv) · '
        '[Parent forecast method](REMAINING_GROUPS_PREDICTION_PLAN.md)']
    return '\n'.join(lines)+'\n'


def publish(root='.'):
    from .studies.artifacts import atomic,encoded
    root=Path(root).resolve()
    report=build(root)
    output=root/'docs/prediction-group-transfer'
    atomic(output/'REMAINING_ERROR_STRUCTURE.md',render(report).encode())
    atomic(output/'remaining-error-structure.csv',csv_bytes(report))
    atomic(output/'remaining-error-structure.json',encoded(report))
    return report


if __name__=='__main__':
    result=publish()
    print('saved groups:',result['scored_groups'],'/',result['groups'])
