# SPDX-License-Identifier: AGPL-3.0-or-later
"""Score closed 400/120 ESA forecasts without reopening a fit."""

import gzip
import hashlib
import json
import math
from pathlib import Path

from .esa_rolling_origin_400_study import ID,LAWS

PARENT='data/prediction-observed-development-continuation-v1-20261113'


def score_raw(predicted,receiver):
    import numpy as np
    from .airquantumgrav_geographic_report import error_metrics
    from .airquantumgrav_scoring import receiver_errors

    forecast=np.asarray(predicted,dtype=float)
    observed=np.asarray(receiver,dtype=float)
    if (forecast.shape!=(120,3) or observed.shape!=(120,3) or
            not np.all(np.isfinite(forecast)) or
            not np.all(np.isfinite(observed))):
        raise ValueError('120 complete finite forecast and receiver rows required')
    errors=receiver_errors(forecast,observed)
    return dict(epochs=120,metrics=error_metrics(errors.tolist()),
                neu_errors_m=errors.tolist(),
                confidence_calibrated=False,physical_adequacy_gate_frozen=False,
                scientific_decision='abstain')


def build(root):
    import numpy as np
    from .studies.closed import ClosedStudy

    root=Path(root).resolve()
    fit=ClosedStudy(root,'data/'+ID)
    try:
        if (fit.completion['state'] not in ('complete','terminal') or
                fit.summary['completed']!=2 or set(fit.tasks)!=set(LAWS)):
            raise ValueError('both sealed earlier-origin fit outcomes required')
        origin=fit.input('parent_identity')
        parent=ClosedStudy(root,PARENT)
        try:
            if (origin['source_id']!='esa-99f1530c3eda4318' or
                    origin['manifest_sha256']!=parent.completion[
                        'manifest_sha256'] or
                    origin['summary_sha256']!=parent.completion['summary_sha256']):
                raise ValueError('sealed development parent differs')
            all_rows=json.loads(gzip.decompress(parent.input('training',raw=True)))
            if len(all_rows)!=800:
                raise ValueError('complete development receiver history required')
            receiver=np.asarray([[math.radians(row['latitude_deg']),
                math.radians(row['longitude_deg']),row['height_m']]
                for row in all_rows[400:520]],dtype=float)
            scored={}
            for law in LAWS:
                result=fit.envelope(law)['result']
                if result['law']!=law or result['later_receiver_positions_used'] is not False:
                    raise ValueError('earlier-only fit outcome differs')
                if result['passed'] is not True:
                    scored[law]=dict(fit_passed=False,raw_score=None,
                                     reason='sealed fit did not pass')
                    continue
                record=fit.artifact(law,'fit.json')
                forecast=fit.artifact(law,'forecast.json')
                if (record['converged'] is not True or
                        forecast['training_epochs']!=400 or
                        forecast['prediction_epochs']!=120 or
                        forecast['prediction_receiver_positions_used'] is not False or
                        len(forecast['coordinates'])!=520 or
                        len(forecast['times_s'])!=520):
                    raise ValueError('complete sealed 400/120 forecast required')
                scored[law]=dict(fit_passed=True,
                    evaluations=record['evaluations'],
                    active_bounds=record['active_bounds'],
                    raw_score=score_raw(forecast['coordinates'][400:],receiver))
            return dict(version='esa-rolling-origin-400-raw-score-v1',
                fit_study='data/'+ID,
                fit_manifest_sha256=fit.completion['manifest_sha256'],
                fit_summary_sha256=fit.completion['summary_sha256'],
                parent_manifest_sha256=parent.completion['manifest_sha256'],
                source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                training_receiver_reports=400,withheld_receiver_reports=120,
                scored_laws=scored,original_reads=0,protected_reads=0,
                new_fits=0,independent_validation=False,
                error_law_qualified=False,physical_adequacy_qualified=False,
                scientific_decision='abstain')
        finally:parent.close()
    finally:fit.close()


def publish(root):
    from .studies.artifacts import atomic,encoded
    root=Path(root).resolve();result=build(root)
    base=root/'docs/prediction-observed-development'
    atomic(base/'ROLLING_ORIGIN_400_RAW_RESULT.json',encoded(result))
    rows=[]
    for law in LAWS:
        item=result['scored_laws'][law]
        if item['fit_passed']:
            metrics=item['raw_score']['metrics']
            rows.append('| {} | yes | {:.3f} | {:.3f} |'.format(
                law,metrics['horizontal_rms_m'],metrics['vertical_rms_m']))
        else:
            rows.append('| {} | no | — | — |'.format(law))
    page=('# Earlier-origin raw forecast check\n\n'
        'Both fit tasks closed before the separately held 120 receiver '
        'positions were scored. The table reports direct forecast errors '
        'without a receiver-conditioning correction.\n\n'
        '| IMU error law | Fit passed | Horizontal RMS (m) | Height RMS (m) |\n'
        '| --- | --- | ---: | ---: |\n'+'\n'.join(rows)+'\n\n'
        'This is exploratory development on one already studied flight. '
        'No physical-adequacy limit or observed error coverage was qualified '
        'for this new cut, and these raw errors alone do not make an '
        'Earth-model decision. The full signed errors, fit status and hashes '
        'are in the [machine-readable result](ROLLING_ORIGIN_400_RAW_RESULT.json).\n')
    atomic(base/'ROLLING_ORIGIN_400_RAW_RESULT.md',page.encode())
    return result


def main(argv=None):
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',default='.')
    args=parser.parse_args(argv)
    result=publish(args.root)
    print(json.dumps({law:{'fit_passed':row['fit_passed'],
        'horizontal_rms_m':None if row['raw_score'] is None else
            row['raw_score']['metrics']['horizontal_rms_m'],
        'height_rms_m':None if row['raw_score'] is None else
            row['raw_score']['metrics']['vertical_rms_m']}
        for law,row in result['scored_laws'].items()},sort_keys=True))


if __name__=='__main__':main()
