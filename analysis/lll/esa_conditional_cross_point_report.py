# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved-only same-law score of two ESA conditional forecasts."""

import gzip
import hashlib
import json
import math
from pathlib import Path

from .esa_conditional_cross_point_study import CONTROL, WEIGHTED
from .esa_conditional_cross_point_v3_study import ID
from .esa_conditional_forecast_report import (
    HISTORICAL, SCORING_SHA256, score_paths)


def build(root):
    import numpy as np
    from .ilvis0_prediction_observed import accuracy_screen
    from .studies.closed import ClosedStudy

    root = Path(root).resolve()
    names = ('data/'+ID, WEIGHTED, CONTROL, HISTORICAL)
    studies = [ClosedStudy(root, name) for name in names]
    try:
        current, weighted, control, historical = studies
        identity = 'receiver-only-point-under-weighted-law'
        if (current.completion['state'] != 'complete' or
                current.summary['completed'] != current.summary['total'] or
                current.summary['total'] != 1 or
                current.rows[identity]['passed'] is not True or
                weighted.completion['manifest_sha256'] !=
                    '17fd7ee56d1ed40fcef39061a4e7ba0706bd93e8d04b9f0998b0db94dc128ea7' or
                control.completion['manifest_sha256'] !=
                    '9f818e2e47b15444d51d0ad357f495ef7a1c12b57d4c489ef743a6c4918a37a8' or
                historical.manifest['inputs']['scoring']['sha256'] != SCORING_SHA256):
            raise ValueError('exact complete same-law forecast and scoring input required')
        old = current.artifact(identity, 'conditional-forecast.json')
        new = weighted.artifact(
            'single-pass-receiver-conditional', 'conditional-forecast.json')
        prefix = current.artifact(identity, 'prefix-replay.json')
        if (old['training_epochs'] != new['training_epochs'] or
                old['training_epochs'] != 800 or
                old['prediction_epochs'] != new['prediction_epochs'] or
                old['prediction_epochs'] != 400 or
                old['times_s'] != new['times_s'] or
                old['full_operator_configuration'] !=
                    new['full_operator_configuration'] or
                any(row['later_receiver_values_used'] is not False or
                    row['optimization_performed'] is not False or
                    row['fixed_calibration_only'] is not True
                    for row in (old, new)) or
                prefix['replay_passed'] is not True):
            raise ValueError('same saved earlier-only law and forecast grid required')
        raw_scoring = historical.input('scoring', raw=True)
        if hashlib.sha256(raw_scoring).hexdigest() != SCORING_SHA256:
            raise ValueError('exact sealed later scoring rows required')
        rows = json.loads(gzip.decompress(raw_scoring))
        if len(rows) != 1200:
            raise ValueError('complete fixed receiver scoring grid required')
        receiver = np.asarray([[math.radians(row['latitude_deg']),
            math.radians(row['longitude_deg']), row['height_m']] for row in rows])
        scores = {name: score_paths(
            row['raw_coordinates'], row['conditional_receiver_mean'], receiver,
            training_epochs=800)
            for name, row in (('receiver_only_point', old),
                              ('weighted_point', new))}
        return dict(version='esa-conditional-cross-point-report-v1',
            study=names[0],
            manifest_sha256=current.completion['manifest_sha256'],
            summary_sha256=current.completion['summary_sha256'],
            scoring_sha256=SCORING_SHA256,
            report_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            same_complete_error_law=True,
            weighted_training_cost_at_receiver_only_point=
                prefix['residual_sum_squares'],
            scores=scores,
            accuracy_screens={name: accuracy_screen(score['conditional'])
                              for name, score in scores.items()},
            training_epochs=800, prediction_epochs=400,
            later_receiver_values_used_for_forecast=False,
            observation_error_law_calibrated=False,
            protected_confirmation_groups_opened=0,
            scientific_decision='abstain')
    finally:
        for study in reversed(studies):
            study.close()


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default='.')
    parser.add_argument('--output', required=True)
    args = parser.parse_args(argv)
    result = build(args.root)
    target = Path(args.output)
    if target.exists():
        raise ValueError('fresh report path required')
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, sort_keys=True, indent=2)+'\n')
    print(json.dumps({name: dict(
        horizontal_rms_m=row['conditional']['horizontal_rms_m'],
        vertical_rms_m=row['conditional']['vertical_rms_m'],
        physical_screen=result['accuracy_screens'][name]['passed'])
        for name, row in result['scores'].items()}, sort_keys=True))


if __name__ == '__main__':
    main()
