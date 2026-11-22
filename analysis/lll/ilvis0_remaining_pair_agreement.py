# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved-only two-start forecast comparison for twenty development groups."""

import csv
import hashlib
import io
from collections import defaultdict
from pathlib import Path

import numpy as np

from .ilvis0_solver_position import physical_metric

STUDY='data/ilvis0-remaining-prediction-transfer-20261118'
LIMIT_M=.1


def compare_pair(rows):
    if (not isinstance(rows,list) or len(rows)!=2 or
            {row['start'] for row in rows}!={0,1} or
            len({(row['segment_id'],row['origin']) for row in rows})!=1 or
            len({(row['training_epochs'],row['prediction_epochs'])
                 for row in rows})!=1):
        raise ValueError('two matched saved starts and one receiver cut required')
    rows=sorted(rows,key=lambda row:row['start'])
    cut=rows[0]['training_epochs'];horizon=rows[0]['prediction_epochs']
    paths=[np.asarray(row['forecast'],float) for row in rows]
    costs=np.asarray([row['training_cost'] for row in rows],float)
    if (cut<1 or horizon<1 or
            any(path.shape!=(cut+horizon,3) or
                not np.all(np.isfinite(path)) for path in paths) or
            not np.all(np.isfinite(costs))):
        raise ValueError('complete finite saved forecasts and costs required')
    metric=physical_metric(paths[0][cut:])
    delta=(paths[1][cut:]-paths[0][cut:])*metric
    length=np.linalg.norm(delta,axis=1)
    return dict(segment_id=rows[0]['segment_id'],origin=rows[0]['origin'],
        training_epochs=cut,prediction_epochs=horizon,
        both_converged=all(row['converged'] is True for row in rows),
        individual_converged=sum(row['converged'] is True for row in rows),
        training_cost_range=float(np.ptp(costs)),
        later_maximum_3d_separation_m=float(np.max(length)),
        later_horizontal_rms_separation_m=float(np.sqrt(np.mean(np.sum(delta[:,:2]**2,axis=1)))),
        later_height_rms_separation_m=float(np.sqrt(np.mean(delta[:,2]**2))),
        within_generated_point_agreement_limit=bool(np.max(length)<=LIMIT_M),
        reclassified_fits=0)


def build(root='.'):
    from .studies.closed import ClosedStudy
    root=Path(root).resolve()
    study=ClosedStudy(root,STUDY)
    try:
        if (len(study.tasks)!=80 or len(study.rows)!=80 or
                study.manifest['limits']['maximum_identities']!=80):
            raise ValueError('exact closed eighty-fit development study required')
        groups=defaultdict(list)
        for identity,task in study.tasks.items():
            outcome=study.envelope(identity)['result']
            fit=study.artifact(identity,'fit.json')
            forecast=study.artifact(identity,'forecast.json')
            payload=task['payload']
            if (fit['converged']!=outcome['converged'] or
                    fit['residual_sum_squares']!=outcome['training_cost'] or
                    forecast.get('prediction_receiver_positions_used') is not False or
                    forecast.get('continuous_propagation_without_gps_reset') is not True):
                raise ValueError('saved fit/forecast provenance differs')
            key=(payload['segment_id'],payload['origin'])
            groups[key].append(dict(segment_id=key[0],origin=key[1],
                start=payload['start'],converged=fit['converged'],
                training_cost=fit['residual_sum_squares'],
                training_epochs=forecast['training_epochs'],
                prediction_epochs=forecast['prediction_epochs'],
                forecast=forecast['coordinates']))
        if len(groups)!=40 or len({key[0] for key in groups})!=20:
            raise ValueError('exact twenty groups and two cuts required')
        pairs=[compare_pair(rows) for key,rows in sorted(groups.items())]
        return dict(version='ilvis0-remaining-pair-agreement-v1',
            study=STUDY,manifest_sha256=study.completion['manifest_sha256'],
            summary_sha256=study.completion['summary_sha256'],
            source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            pairs=40,groups=20,individual_fits=80,
            original_converged=sum(row['individual_converged'] for row in pairs),
            both_converged_pairs=sum(row['both_converged'] for row in pairs),
            within_point_agreement_limit=sum(
                row['within_generated_point_agreement_limit'] for row in pairs),
            maximum_later_3d_separation_m=max(
                row['later_maximum_3d_separation_m'] for row in pairs),
            rows=pairs,point_agreement_limit_m=LIMIT_M,
            native_calls=0,reclassified_fits=0,scientific_decision='abstain',
            coverage_calibrated=False)
    finally:study.close()


def render(result):
    lines=['# Saved two-start forecast agreement','',
        f"The original 80-fit development study contains {result['pairs']} "
        f"matched training-cut pairs across {result['groups']} recording groups. "
        f"{result['original_converged']}/80 individual fits passed their original "
        'stopping checks.','',
        f"{result['within_point_agreement_limit']}/40 saved pairs have a "
        f"maximum withheld-path difference within {LIMIT_M:g} m. "
        f"The largest pair difference is {result['maximum_later_3d_separation_m']:.3g} m. "
        'The threshold comes from generated solver development and is a '
        'diagnostic here, not a calibrated aircraft acceptance rule.','',
        'Both forecasts in each pair were saved before later receiver positions '
        'were scored. This compares predicted paths from two starting points '
        'on the same observations. Close agreement does not prove either fit '
        'is an optimum, accurate on withheld positions, or physically adequate. '
        'The original 50 nonpassing labels remain unchanged. No native calls '
        'or new aircraft fits were made.','',
        '[All forty pairs](remaining-pair-agreement.csv) · '
        '[Original forecast study](REMAINING_GROUPS_PREDICTION_RESULT.md)']
    return '\n'.join(lines)+'\n'


def csv_bytes(result):
    fields=('segment_id','origin','training_epochs','prediction_epochs',
            'individual_converged','both_converged','training_cost_range',
            'later_maximum_3d_separation_m',
            'later_horizontal_rms_separation_m',
            'later_height_rms_separation_m',
            'within_generated_point_agreement_limit','reclassified_fits')
    stream=io.StringIO(newline='')
    writer=csv.DictWriter(stream,fieldnames=fields,lineterminator='\n')
    writer.writeheader()
    for row in result['rows']:
        writer.writerow({key:row[key] for key in fields})
    return stream.getvalue().encode()


def publish(root='.'):
    from .studies.artifacts import atomic,encoded
    root=Path(root).resolve();result=build(root)
    output=root/'docs/prediction-group-transfer'
    atomic(output/'REMAINING_PAIR_AGREEMENT.md',render(result).encode())
    atomic(output/'remaining-pair-agreement.csv',csv_bytes(result))
    atomic(output/'remaining-pair-agreement.json',encoded(result))
    return result


if __name__=='__main__':
    result=publish()
    print('pairs within 0.1 m:',result['within_point_agreement_limit'],'/',result['pairs'])
