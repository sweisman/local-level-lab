# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved-only receiver perturbation margins for fixed ESA forecasts."""

import gzip
import json
import math
from pathlib import Path

from .esa_alternate_ppp_scoring import MODELS, PARENT
from .esa_full_parallel_gnss import _sha

VERSION='esa-fixed-forecast-receiver-margin-v1'
SCORES='docs/prediction-observed-development/esa-alternate-ppp-scoring-result.json'
PLAN='docs/prediction-observed-development/ESA_FIXED_FORECAST_RECEIVER_MARGIN_PLAN.md'


def tie_margin(preferred,alternative):
    """Minimum norm of a receiver perturbation making fixed SSEs equal."""
    import numpy as np
    a=np.asarray(preferred,float)
    b=np.asarray(alternative,float)
    if (a.ndim!=2 or a.shape[1] not in (2,3) or b.shape!=a.shape or not len(a)
            or not np.all(np.isfinite(a)) or not np.all(np.isfinite(b))):
        raise ValueError('aligned finite two- or three-axis errors required')
    gap=float(np.sum(b*b)-np.sum(a*a))
    if gap<=0:
        raise ValueError('strictly lower preferred sum of squares required')
    direction=b-a
    norm=float(np.linalg.norm(direction))
    if norm==0:
        raise ValueError('distinct fixed forecasts required')
    # Error after moving receiver by delta is e-delta. The score difference
    # changes by -2 delta dot (b-a).
    delta=gap*direction/(2*norm*norm)
    tied=float(np.sum((b-delta)**2)-np.sum((a-delta)**2))
    if abs(tied)>1e-8*gap:
        raise ValueError('constructed arbitrary shift does not tie scores')
    summed=np.sum(direction,axis=0)
    constant_norm=float(np.linalg.norm(summed))
    constant=None
    if constant_norm:
        c=gap*summed/(2*constant_norm*constant_norm)
        tied_constant=float(np.sum((b-c)**2)-np.sum((a-c)**2))
        if abs(tied_constant)>1e-8*gap:
            raise ValueError('constructed constant shift does not tie scores')
        constant=float(np.linalg.norm(c))
    return dict(preferred_rms_m=float(np.sqrt(np.mean(np.sum(a*a,axis=1)))),
        alternative_rms_m=float(np.sqrt(np.mean(np.sum(b*b,axis=1)))),
        arbitrary_shift_epoch_rms_m=float(np.linalg.norm(delta)/math.sqrt(len(a))),
        constant_shift_m=constant,
        score_gap_sum_squares_m2=gap)


def build(root):
    import numpy as np
    from .airquantumgrav_scoring import receiver_errors
    from .esa_rolling_origin_400_model_matrix import ID
    from .studies.artifacts import digest
    from .studies.closed import ClosedStudy

    root=Path(root).resolve()
    saved=json.loads((root/SCORES).read_bytes())
    if (saved.get('version')!='esa-alternate-ppp-forecast-scoring-v1'
            or saved.get('new_fits')!=0 or saved.get('protected_reads')!=0
            or saved.get('common_withheld_epochs')!=120
            or len(saved.get('settings',[]))!=2):
        raise ValueError('two complete sealed forecast settings required')
    parent=ClosedStudy(root,PARENT)
    study=ClosedStudy(root,'data/'+ID)
    try:
        if (saved['parent_manifest_sha256']!=parent.completion['manifest_sha256']
                or saved['matrix_manifest_sha256']!=study.completion['manifest_sha256']):
            raise ValueError('sealed study manifests differ')
        original=json.loads(gzip.decompress(parent.input('training',raw=True)))
        if len(original)!=800:
            raise ValueError('same 800-report parent cut required')
        later=original[400:520]
        receiver=np.asarray([[math.radians(row['latitude_deg']),
                              math.radians(row['longitude_deg']),row['height_m']]
                             for row in later],float)
        result=[]
        for setting in saved['settings']:
            errors={}
            for model in MODELS:
                start=setting['primary_start'][model]
                identity=f"{model}-{int(setting['profile'])}-{setting['law']}-{start}"
                raw=study.artifact(identity,'forecast.json',raw=True)
                if digest(raw)!=setting['forecast_sha256'][model]:
                    raise ValueError('sealed forecast hash differs')
                forecast=json.loads(raw)
                if (forecast.get('training_epochs')!=400
                        or forecast.get('prediction_epochs')!=120
                        or forecast.get('prediction_receiver_positions_used') is not False):
                    raise ValueError('strict earlier-only forecast required')
                predicted=np.asarray(forecast['coordinates'][400:520],float)
                errors[model]=receiver_errors(predicted,receiver)
                stored=setting['by_receiver']['air1']['scores'][model]['total_rms_m']
                actual=float(np.sqrt(np.mean(np.sum(errors[model]**2,axis=1))))
                if not math.isclose(actual,stored,rel_tol=1e-9,abs_tol=1e-6):
                    raise ValueError('saved original score does not reproduce')
            if setting['by_receiver']['air1']['ranking']['lower_error_globe_model']!=MODELS[0]:
                raise ValueError('specified-field globe must be saved preferred globe')
            contrasts={}
            for model in MODELS[1:]:
                contrasts[model]=dict(full=tie_margin(errors[MODELS[0]],errors[model]),
                                      horizontal=tie_margin(errors[MODELS[0]][:,:2],
                                                            errors[model][:,:2]))
            result.append(dict(profile=setting['profile'],law=setting['law'],
                               contrasts=contrasts))
        return dict(version=VERSION,source_sha256=_sha(root/SCORES),
            plan_sha256=_sha(root/PLAN),code_sha256=_sha(Path(__file__)),
            matrix_manifest_sha256=study.completion['manifest_sha256'],
            parent_manifest_sha256=parent.completion['manifest_sha256'],
            later_epochs=120,settings=result,receiver_coordinate_metric='frozen air1 local NEU',
            same_forecasts_and_calibration=True,original_reads=0,
            new_fits=0,native_forecasts=0,protected_group_reads=0,
            calibrated_receiver_accuracy=False,scientific_decision='abstain')
    finally:
        study.close();parent.close()


def main(argv=None):
    import argparse
    from .studies.artifacts import atomic,encoded
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',default='.')
    parser.add_argument('--output',required=True)
    args=parser.parse_args(argv)
    output=Path(args.output)
    if output.exists():
        raise ValueError('fresh fixed-forecast sensitivity required')
    result=build(args.root)
    atomic(output,encoded(result))
    print([(x['profile'],x['law'],
            {k:round(v['full']['arbitrary_shift_epoch_rms_m'],3)
             for k,v in x['contrasts'].items()}) for x in result['settings']])


if __name__=='__main__':main()
