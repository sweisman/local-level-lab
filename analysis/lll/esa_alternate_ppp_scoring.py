# SPDX-License-Identifier: AGPL-3.0-or-later
"""Score sealed ESA development forecasts against two other PPP exports."""

import gzip
import json
import math
from pathlib import Path

from .esa_full_parallel_gnss import AIR1, BASE, INVENTORY, _sha
from .esa_full_parallel_gnss_v2 import EXPECTED_ROLLOVERS
from .esa_parallel_gnss import MATCH_TOLERANCE_S, match_times
from .esa_parallel_gnss_time import corrected_neu
from .esa_ppp_acquisition import TARGETS, verify_complete
from .esa_receiver_sequence_wrap import records_with_sequence_wrap

VERSION = 'esa-alternate-ppp-forecast-scoring-v1'
FULL = 'docs/prediction-observed-development/full-parallel-gnss-v2-result.json'
PLAN = 'docs/prediction-observed-development/ESA_ALTERNATE_PPP_SCORING_PLAN.md'
PARENT = 'data/prediction-observed-development-continuation-v1-20261113'
MIN_COMMON = 100
MODELS = ('sphere_rotating','sphere_still','flat_still')


def score_errors(base_errors, adjusted_difference, common):
    import numpy as np
    from .airquantumgrav_geographic_report import error_metrics
    from .ilvis0_prediction_observed import accuracy_screen
    base = np.asarray(base_errors, float)
    delta = np.asarray(adjusted_difference, float)
    indices = list(common)
    if (base.ndim != 2 or base.shape[1:] != (3,)
            or delta.shape != base.shape or not indices
            or indices != sorted(set(indices)) or indices[0] < 0
            or indices[-1] >= len(base)
            or not np.all(np.isfinite(base)) or not np.all(np.isfinite(delta))):
        raise ValueError('aligned complete finite common-epoch errors required')
    errors = base[indices]-delta[indices]
    metrics = error_metrics(errors.tolist())
    metrics['maximum_horizontal_m'] = float(np.max(np.linalg.norm(errors[:,:2],axis=1)))
    metrics['maximum_absolute_up_m'] = float(np.max(abs(errors[:,2])))
    return dict(metrics, accuracy=accuracy_screen(metrics)['passed'],
                matched_epochs=len(indices))


def rank_setting(scores):
    if set(scores) != set(MODELS):
        raise ValueError('three complete model scores required')
    for row in scores.values():
        value = row.get('total_rms_m')
        if type(value) not in (int,float) or not math.isfinite(value) or value<0:
            raise ValueError('finite nonnegative matched total error required')
    globe = min(MODELS[:2], key=lambda name:scores[name]['total_rms_m'])
    flat = MODELS[2]
    g, f = scores[globe]['total_rms_m'], scores[flat]['total_rms_m']
    shape = 'globe' if g<f else 'flat' if f<g else 'tie'
    rotating = scores[MODELS[0]]['total_rms_m']
    still = scores[MODELS[1]]['total_rms_m']
    field = ('specified_field' if rotating<still else
             'zero_field' if still<rotating else 'tie') if shape=='globe' else None
    return dict(shape_lower_error_family=shape,
                lower_error_globe_model=globe,
                field_lower_error_model=field,
                preferred_accuracy=scores[globe if shape=='globe' else flat]['accuracy']
                if shape!='tie' else None,
                scientific_decision='abstain')


def build(root):
    import numpy as np
    from .airquantumgrav_receiver import records
    from .airquantumgrav_scoring import receiver_errors
    from .esa_rolling_origin_400_model_matrix import ID
    from .esa_rolling_origin_400_model_matrix_report import build as saved_report
    from .studies.artifacts import digest
    from .studies.closed import ClosedStudy

    root = Path(root).resolve()
    report = saved_report(root)
    if report['complete_settings'] != 2 or report['total'] != 24:
        raise ValueError('exact completed development matrix required')
    parent = ClosedStudy(root, PARENT)
    study = ClosedStudy(root, 'data/'+ID)
    try:
        original = json.loads(gzip.decompress(parent.input('training',raw=True)))
        if (len(original)!=800 or study.completion['manifest_sha256']!=report['fit_manifest_sha256']
                or parent.completion['manifest_sha256']!=report['parent_manifest_sha256']):
            raise ValueError('unchanged parent cut and candidate fits required')
        later = original[400:520]
        if len(later)!=120:
            raise ValueError('exact 120 withheld parent reports required')
        inventory=json.loads((root/INVENTORY).read_bytes())
        full=json.loads((root/FULL).read_bytes())
        if (inventory.get('source_file')!=AIR1 or inventory.get('epochs')!=64080
                or full.get('reference_sha256')!=inventory.get('sha256')
                or full.get('protected_group_reads')!=0):
            raise ValueError('unchanged opened PPP sources required')
        air1_path=root/BASE/AIR1
        if _sha(air1_path)!=inventory['sha256']:
            raise ValueError('air1 source hash differs')
        with air1_path.open() as stream:
            reference=list(records(stream))
        time_to_index={row['time_s']:i for i,row in enumerate(reference)}
        if len(time_to_index)!=len(reference):
            raise ValueError('duplicate air1 receiver times')
        ref_indices=[]
        for row in later:
            index=time_to_index.get(row['time_s'])
            if (index is None or any(reference[index][key]!=row[key]
                    for key in ('latitude_deg','longitude_deg','height_m'))):
                raise ValueError('sealed later air1 path differs from raw PPP')
            ref_indices.append(index)
        if ref_indices!=sorted(set(ref_indices)):
            raise ValueError('withheld parent times are not unique and ordered')
        paired={}
        selected_indices=set(ref_indices)
        sources=[]
        for name,size in TARGETS.items():
            path=root/BASE/name
            receipt=json.loads((root/BASE/(name+'.receipt.json')).read_bytes())
            sha=verify_complete(path,size,receipt)
            expected=next(row for row in full['sources'] if row['filename']==name)
            if sha!=expected['source_sha256']:
                raise ValueError('parallel PPP source hash differs')
            sequence_audit={}
            with path.open() as stream:
                parsed=records_with_sequence_wrap(stream,
                    expected_rollovers=EXPECTED_ROLLOVERS[name],audit=sequence_audit)
                matches=match_times(reference,parsed)
                for _ in parsed:
                    pass
            if (sequence_audit!=expected['sequence_audit']
                    or len(matches)!=expected['matched_epochs']):
                raise ValueError('PPP parser or match audit differs')
            selected={index:corrected_neu(reference[index],other)[1]
                      for index,other in matches if index in selected_indices}
            paired[name]=selected
            sources.append(dict(filename=name,sha256=sha,
                                selected_matches=len(selected)))
        common=[i for i,index in enumerate(ref_indices)
                if all(index in paired[name] for name in TARGETS)]
        if len(common)<MIN_COMMON:
            raise ValueError('insufficient same-epoch triple-PPP withheld comparison')
        receiver=np.asarray([[math.radians(row['latitude_deg']),
                              math.radians(row['longitude_deg']),row['height_m']]
                             for row in later],float)
        differences={'air1':np.zeros((120,3))}
        for name in TARGETS:
            array=np.zeros((120,3))
            for position in common:
                array[position]=paired[name][ref_indices[position]]
            differences[name]=array
        settings=[]
        for setting in report['settings']:
            if not setting['complete']:
                continue
            profile,law=setting['profile'],setting['law']
            errors={}
            forecast_hashes={}
            for model in MODELS:
                start=setting['primary_start'][model]
                identity=f'{model}-{int(profile)}-{law}-{start}'
                raw=study.artifact(identity,'forecast.json',raw=True)
                forecast=json.loads(raw)
                if (forecast['training_epochs']!=400 or forecast['prediction_epochs']!=120
                        or forecast['prediction_receiver_positions_used'] is not False
                        or len(forecast['coordinates'])!=520):
                    raise ValueError('complete sealed earlier-only forecast required')
                prediction=np.asarray(forecast['coordinates'][400:520],float)
                errors[model]=receiver_errors(prediction,receiver)
                forecast_hashes[model]=digest(raw)
            by_source={}
            for name,difference in differences.items():
                scores={model:score_errors(errors[model],difference,common)
                        for model in MODELS}
                by_source[name]=dict(scores=scores,ranking=rank_setting(scores))
            settings.append(dict(profile=profile,law=law,
                                 primary_start=setting['primary_start'],
                                 forecast_sha256=forecast_hashes,
                                 by_receiver=by_source))
        return dict(version=VERSION,plan_sha256=_sha(root/PLAN),
            code_sha256=_sha(Path(__file__)),
            matrix_manifest_sha256=study.completion['manifest_sha256'],
            matrix_summary_sha256=study.completion['summary_sha256'],
            parent_manifest_sha256=parent.completion['manifest_sha256'],
            raw_air1_sha256=inventory['sha256'],
            full_ppp_result_sha256=_sha(root/FULL),sources=sources,
            common_withheld_epochs=len(common),
            common_parent_indices=common,settings=settings,
            receiver_original_reads=3,imu_original_reads=0,
            protected_reads=0,new_fits=0,
            horizon_independently_selected=False,
            absolute_receiver_accuracy_established=False,
            scientific_decision='abstain')
    finally:
        study.close();parent.close()


def main(argv=None):
    import argparse
    from .studies.artifacts import atomic,encoded
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',default='.')
    parser.add_argument('--output',required=True)
    args=parser.parse_args(argv)
    path=Path(args.output)
    if path.exists():
        raise ValueError('fresh alternate PPP score required')
    result=build(args.root)
    atomic(path,encoded(result))
    print([(r['profile'],r['law'],
            {name:value['ranking']['shape_lower_error_family']
             for name,value in r['by_receiver'].items()}) for r in result['settings']])


if __name__=='__main__':main()
