# SPDX-License-Identifier: AGPL-3.0-or-later
"""Score closed ESA alternate-training fits on the same held-out air1 path."""

import gzip
import json
import math
from pathlib import Path

from .esa_alternate_ppp_scoring import MODELS, PARENT
from .esa_alternate_training_refit import ID, INPUTS, MATERIAL, SOURCE_NAMES, SOURCES, tasks
from .esa_full_parallel_gnss import _sha

VERSION='esa-alternate-training-refit-report-v1'
SAVED='docs/prediction-observed-development/esa-alternate-ppp-scoring-result.json'


def rank_complete(scores):
    if set(scores)!=set(MODELS):
        return dict(shape='unresolved',field=None,reason='required_fit_not_passed')
    values={name:float(row['total_rms_m']) for name,row in scores.items()}
    if any(not math.isfinite(value) or value<0 for value in values.values()):
        raise ValueError('finite nonnegative model scores required')
    globe=min(MODELS[:2],key=values.get)
    shape='globe' if values[globe]<values[MODELS[2]] else 'flat' if values[MODELS[2]]<values[globe] else 'tie'
    field=('specified_field' if values[MODELS[0]]<values[MODELS[1]] else
           'zero_field' if values[MODELS[1]]<values[MODELS[0]] else 'tie') if shape=='globe' else None
    return dict(shape=shape,field=field,reason=None)


def build(root):
    import numpy as np
    from .airquantumgrav_geographic_report import error_metrics
    from .airquantumgrav_scoring import receiver_errors
    from .esa_rolling_origin_400_model_matrix import ID as MATRIX_ID
    from .ilvis0_prediction_observed import accuracy_screen
    from .studies.artifacts import digest
    from .studies.closed import ClosedStudy

    root=Path(root).resolve()
    saved=json.loads((root/SAVED).read_bytes())
    material=(root/MATERIAL).read_bytes()
    if (saved.get('version')!='esa-alternate-ppp-forecast-scoring-v1'
            or saved.get('common_withheld_epochs')!=120):
        raise ValueError('unchanged original held-out scores required')
    current=ClosedStudy(root,'data/'+ID)
    original=ClosedStudy(root,'data/'+MATRIX_ID)
    parent=ClosedStudy(root,PARENT)
    try:
        expected={row['identity'] for row in tasks()}
        if (current.summary['total']!=6 or current.summary['completed']!=6
                or set(current.rows)!=expected
                or set(current.manifest['inputs'])!=INPUTS
                or original.completion['manifest_sha256']!=saved['matrix_manifest_sha256']
                or parent.completion['manifest_sha256']!=saved['parent_manifest_sha256']):
            raise ValueError('all six closed bound refits and source manifests required')
        binding=current.input('alternate-material-binding')
        if binding['material_sha256']!=digest(material):
            raise ValueError('staged alternate training material differs')
        parent_rows=json.loads(gzip.decompress(parent.input('training',raw=True)))
        if len(parent_rows)!=800:
            raise ValueError('same sealed 800-report parent cut required')
        later=parent_rows[400:520]
        receiver=np.asarray([[math.radians(row['latitude_deg']),
                              math.radians(row['longitude_deg']),row['height_m']]
                             for row in later],float)
        baseline=next(row for row in saved['settings']
                      if row['profile'] is True and row['law']=='increment')
        if any(baseline['primary_start'][model]!=0 for model in MODELS):
            raise ValueError('same original primary starts required')
        by_source=[]
        for source in SOURCES:
            scores={}
            outcomes=[]
            for model in MODELS:
                identity=f'{source}-{model}'
                envelope=current.envelope(identity)
                if envelope['status']!='complete':
                    outcomes.append(dict(model=model,passed=False,
                                         technical_status=envelope['status'],
                                         result_sha256=envelope['result_sha256']))
                    continue
                outcome=envelope['result']
                if (outcome.get('source')!=source or outcome.get('model')!=model
                        or outcome.get('training_epochs')!=400
                        or outcome.get('prediction_epochs')!=120
                        or outcome.get('later_receiver_positions_used') is not False):
                    raise ValueError('refit task outcome differs')
                outcomes.append(dict(model=model,passed=outcome['passed'],
                                     numerical_converged=outcome['numerical_converged'],
                                     result_sha256=envelope['result_sha256']))
                if not outcome['passed']:
                    continue
                forecast=current.artifact(identity,'forecast.json')
                if (forecast.get('training_epochs')!=400
                        or forecast.get('prediction_epochs')!=120
                        or forecast.get('prediction_receiver_positions_used') is not False):
                    raise ValueError('earlier-only alternate forecast required')
                alternative=np.asarray(forecast['coordinates'][400:520],float)
                errors=receiver_errors(alternative,receiver)
                metrics=error_metrics(errors.tolist())
                metrics['maximum_horizontal_m']=float(np.max(np.linalg.norm(errors[:,:2],axis=1)))
                metrics['maximum_absolute_up_m']=float(np.max(abs(errors[:,2])))
                original_forecast=original.artifact(f'{model}-1-increment-0','forecast.json')
                original_coordinates=np.asarray(original_forecast['coordinates'][400:520],float)
                difference=receiver_errors(alternative,original_coordinates)
                original_score=baseline['by_receiver']['air1']['scores'][model]['total_rms_m']
                check=receiver_errors(original_coordinates,receiver)
                actual_original=float(np.sqrt(np.mean(np.sum(check**2,axis=1))))
                if not math.isclose(actual_original,original_score,rel_tol=1e-9,abs_tol=1e-6):
                    raise ValueError('original fixed score differs')
                scores[model]=dict(total_rms_m=metrics['total_rms_m'],
                    horizontal_rms_m=metrics['horizontal_rms_m'],
                    height_rms_m=metrics['vertical_rms_m'],
                    original_total_rms_m=original_score,
                    forecast_shift_rms_m=float(np.sqrt(np.mean(np.sum(difference**2,axis=1)))),
                    physical_screen_passed=accuracy_screen(metrics)['passed'])
            by_source.append(dict(source=source,filename=SOURCE_NAMES[source],
                                  outcomes=outcomes,scores=scores,
                                  ranking=rank_complete(scores)))
        return dict(version=VERSION,code_sha256=_sha(Path(__file__)),
            source_scores_sha256=_sha(root/SAVED),material_sha256=digest(material),
            refit_manifest_sha256=current.completion['manifest_sha256'],
            refit_summary_sha256=current.completion['summary_sha256'],
            original_manifest_sha256=original.completion['manifest_sha256'],
            parent_manifest_sha256=parent.completion['manifest_sha256'],
            later_receiver_reports=120,by_source=by_source,
            input_source='opened ESA development recording 187',
            original_reads=0,new_fits=0,protected_group_reads=0,
            calibrated_error_law=False,independent_replication=False,
            scientific_decision='abstain')
    finally:
        current.close();original.close();parent.close()


def main(argv=None):
    import argparse
    from .studies.artifacts import atomic,encoded
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',default='.')
    parser.add_argument('--output',required=True)
    args=parser.parse_args(argv)
    output=Path(args.output)
    if output.exists():
        raise ValueError('fresh closed-refit report required')
    result=build(args.root)
    atomic(output,encoded(result))
    print([(row['source'],row['ranking']) for row in result['by_source']])


if __name__=='__main__':main()
