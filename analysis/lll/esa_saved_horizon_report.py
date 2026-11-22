# SPDX-License-Identifier: AGPL-3.0-or-later
"""Retrospective short-horizon scores from the sealed ESA development forecast."""

import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path

HORIZONS=(1,5,10,30,60,120,200,300,400)


def matching_full_score(verified,law,section):
    source={'raw':'raw','conditioned':'conditional'}[section]
    return verified['laws'][law]['score'][source]['horizontal_rms_m']


def prefix_errors(errors,horizons=HORIZONS):
    import numpy as np
    value=np.asarray(errors,dtype=float)
    if (value.ndim!=2 or value.shape[1]!=3 or not len(value) or
            not np.all(np.isfinite(value)) or not horizons or
            any(type(n) is not int or not 1<=n<=len(value) for n in horizons) or
            tuple(sorted(set(horizons)))!=tuple(horizons)):
        raise ValueError('finite north/east/up errors and ordered horizons required')
    return {str(n):dict(horizontal_rms_m=float(np.sqrt(np.mean(
                np.square(value[:n,:2]).sum(axis=1)))),
            vertical_rms_m=float(np.sqrt(np.mean(np.square(value[:n,2])))),
            final_vertical_error_m=float(value[n-1,2]))
            for n in horizons}


def build(root):
    import numpy as np
    from .esa_training_split_extension_report import build as extension_build
    from .esa_training_split_extension import ID
    from .esa_conditional_forecast_report import HISTORICAL,SCORING_SHA256
    from .esa_training_split_report import score_pair
    from .esa_training_split_study import LAWS
    from .studies.closed import ClosedStudy
    root=Path(root).resolve();verified=extension_build(root)
    extension=ClosedStudy(root,'data/'+ID)
    historical=ClosedStudy(root,HISTORICAL)
    try:
        if (extension.completion['manifest_sha256']!=verified[
                'extension_manifest_sha256'] or
                historical.manifest['inputs']['scoring']['sha256']!=SCORING_SHA256):
            raise ValueError('sealed 600/400 development evidence changed')
        rows=json.loads(gzip.decompress(historical.input('scoring',raw=True)))
        if len(rows)!=1200:
            raise ValueError('complete saved development receiver support required')
        future=rows[600:1000]
        receiver=np.asarray([[math.radians(row['latitude_deg']),
                              math.radians(row['longitude_deg']),row['height_m']]
                             for row in future],dtype=float)
        times=np.asarray([row['time_s'] for row in future],float)
        if (times.shape!=(400,) or np.any(np.diff(times)<=0) or
                np.max(np.diff(times))>1.1 or np.min(np.diff(times))<.9):
            raise ValueError('one-second saved receiver grid required')
        cases={}
        for law in LAWS:
            saved=extension.artifact(law,'extended-conditional.json')
            if (saved['law']!=law or saved['training_epochs']!=600 or
                    saved['prediction_epochs']!=400 or
                    saved['later_receiver_values_used'] is not False or
                    saved['protected_reads']!=0 or
                    saved['optimization_performed'] is not False):
                raise ValueError('unchanged earlier-only forecast required')
            score=score_pair(saved['raw_coordinates'],
                saved['conditional_receiver_mean'],
                saved['conditional_receiver_covariance'],receiver)
            cases[law]=dict(raw=prefix_errors(score['raw_neu_errors_m']),
                conditioned=prefix_errors(score['conditional_neu_errors_m']))
            for key,section in (('raw','raw'),('conditioned','conditioned')):
                full=cases[law][key]['400']['horizontal_rms_m']
                reported=matching_full_score(verified,law,section)
                if abs(full-reported)>1e-8:
                    raise ValueError('full-horizon saved score differs')
        return dict(version='esa-saved-horizon-diagnostic-v1',
            extension_study='data/'+ID,
            extension_manifest_sha256=extension.completion['manifest_sha256'],
            extension_summary_sha256=extension.completion['summary_sha256'],
            historical_scoring_sha256=SCORING_SHA256,
            report_source_sha256=hashlib.sha256((root/
                'analysis/lll/esa_saved_horizon_report.py').read_bytes()).hexdigest(),
            horizons_reports=list(HORIZONS),first_future_time_s=float(times[0]),
            last_future_time_s=float(times[-1]),cases=cases,
            retrospective_development_only=True,
            original_reads=0,protected_confirmation_groups_opened=0,
            new_fits=0,confidence_calibrated=False,scientific_decision='abstain')
    finally:
        historical.close();extension.close()


def publish(root):
    from .studies.artifacts import atomic,encoded
    root=Path(root).resolve();result=build(root)
    base=root/'docs/prediction-observed-development'
    atomic(base/'RECORDED_HORIZON_DIAGNOSTIC.json',encoded(result))
    rows=[]
    for n in HORIZONS:
        a=result['cases']['increment']['conditioned'][str(n)]
        b=result['cases']['point']['conditioned'][str(n)]
        rows.append('| {} | {:.2f} | {:.2f} | {:.2f} | {:.2f} |'.format(
            n,a['horizontal_rms_m'],a['vertical_rms_m'],
            b['horizontal_rms_m'],b['vertical_rms_m']))
    page=('# How the saved ESA development forecast changes with horizon\n\n'
        'This is a retrospective view of the **same** sealed 600-report fit '
        'and its next 400 one-second receiver reports. The fit and full '
        'forecast were saved before scoring; no parameter is refitted here. '
        'The short prefixes were examined after the long forecast result was '
        'known, so they cannot become fresh withheld validation.\n\n'
        '| First withheld reports | Increment horizontal RMS (m) | Increment height RMS (m) | Point-rate horizontal RMS (m) | Point-rate height RMS (m) |\n'
        '| ---: | ---: | ---: | ---: | ---: |\n'+'\n'.join(rows)+'\n\n'
        'A shorter interval may reduce drift, but this table neither changes '
        'the failed 400-report prediction gate nor qualifies a new gate. '
        'A future short-block study must choose its windows and limits from '
        'receiver-only metadata and generated controls before examining '
        'their model errors. The seven reserved ESA groups remain sealed.\n\n'
        '[Values and hashes](RECORDED_HORIZON_DIAGNOSTIC.json) · '
        '[Generated horizon scales](ORACLE_HORIZON_REPORT.md).\n')
    atomic(base/'RECORDED_HORIZON_DIAGNOSTIC.md',page.encode())
    return result


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',default='.')
    args=parser.parse_args(argv);result=publish(args.root)
    print(json.dumps({law:result['cases'][law]['conditioned']['400']
                      for law in ('increment','point')},sort_keys=True))


if __name__=='__main__':main()
