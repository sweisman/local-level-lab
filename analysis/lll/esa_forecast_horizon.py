# SPDX-License-Identifier: AGPL-3.0-or-later
"""Describe where a saved ESA forecast loses height coverage; never refit."""

import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path


def horizon_bins(raw_errors, conditioned_errors, half_widths, receiver_rows,
                 *, size=100):
    """Summarize fixed bins of prediction-minus-receiver errors in metres."""
    import numpy as np

    raw, conditioned, width = (np.asarray(value, dtype=float) for value in
                                (raw_errors, conditioned_errors, half_widths))
    n = len(raw)
    if (type(size) is not int or size < 2 or n < size or n % size or
            raw.shape != (n, 3) or conditioned.shape != raw.shape or
            width.shape != raw.shape or len(receiver_rows) != n or
            not all(np.all(np.isfinite(value)) for value in
                    (raw, conditioned, width)) or np.any(width <= 0)):
        raise ValueError('complete fixed bins of finite errors and intervals required')
    try:
        times = np.asarray([row['time_s'] for row in receiver_rows], float)
        north = np.asarray([row['north_mps'] for row in receiver_rows], float)
        east = np.asarray([row['east_mps'] for row in receiver_rows], float)
        up = np.asarray([row['up_mps'] for row in receiver_rows], float)
    except (KeyError, TypeError) as error:
        raise ValueError('complete fixed bins require receiver motion') from error
    if (not all(np.all(np.isfinite(value)) for value in
                (times, north, east, up)) or np.any(np.diff(times) <= 0)):
        raise ValueError('complete fixed bins require ordered receiver motion')
    speed = np.hypot(north, east)
    result = []
    for start in range(0, n, size):
        stop = start + size
        raw_up, cond_up = raw[start:stop, 2], conditioned[start:stop, 2]
        accepted = np.abs(cond_up) <= width[start:stop, 2]
        result.append(dict(start_offset=start, stop_offset=stop,
            first_time_s=float(times[start]), last_time_s=float(times[stop-1]),
            raw_up_mean_m=float(np.mean(raw_up)),
            raw_up_rms_m=float(np.sqrt(np.mean(raw_up*raw_up))),
            conditional_up_first_m=float(cond_up[0]),
            conditional_up_last_m=float(cond_up[-1]),
            conditional_up_mean_m=float(np.mean(cond_up)),
            conditional_up_rms_m=float(np.sqrt(np.mean(cond_up*cond_up))),
            conditional_adjustment_mean_m=float(np.mean(cond_up-raw_up)),
            nominal_95_up_count=int(np.count_nonzero(accepted)),
            nominal_95_up_total=size,
            nominal_95_up_fraction=float(np.mean(accepted)),
            receiver_mean_ground_speed_mps=float(np.mean(speed[start:stop])),
            receiver_mean_up_mps=float(np.mean(up[start:stop])),
            receiver_up_sd_mps=float(np.std(up[start:stop]))))
    return result


def build(root):
    """Read only sealed development forecasts and their already-opened GPS rows."""
    import numpy as np
    from .esa_conditional_forecast_report import (
        HISTORICAL, MANIFEST_SHA256, SCORING_SHA256, STUDY, TASK)
    from .esa_training_split_conditioning import ID as CONDITION_ID
    from .esa_training_split_report import PARENT, score_pair
    from .esa_training_split_study import ID as FIT_ID, LAWS
    from .studies.closed import ClosedStudy

    root = Path(root).resolve()
    score_path = root/'docs/prediction-observed-development/training-split-score.json'
    score_bytes = score_path.read_bytes()
    shorter = json.loads(score_bytes)
    names = ('data/'+FIT_ID, 'data/'+CONDITION_ID, PARENT,
             STUDY, HISTORICAL)
    studies = [ClosedStudy(root, name) for name in names]
    fit, condition, parent, old, historical = studies
    try:
        if (shorter['version'] != 'esa-600-200-retrospective-score-v1' or
                shorter['fit_manifest_sha256'] != fit.completion['manifest_sha256'] or
                shorter['conditioning_manifest_sha256'] !=
                    condition.completion['manifest_sha256'] or
                shorter['parent_manifest_sha256'] !=
                    parent.completion['manifest_sha256'] or
                shorter['report_source_sha256'] != hashlib.sha256((root/
                    'analysis/lll/esa_training_split_report.py').read_bytes()).hexdigest() or
                shorter['training_epochs'] != 600 or
                shorter['prediction_epochs'] != 200 or
                set(shorter['scored_laws']) != set(LAWS) or
                shorter['protected_confirmation_groups_opened'] != 0 or
                shorter['scientific_decision'] != 'abstain' or
                old.completion['manifest_sha256'] != MANIFEST_SHA256 or
                old.completion['state'] != 'complete' or
                historical.manifest['inputs']['scoring']['sha256'] !=
                    SCORING_SHA256):
            raise ValueError('sealed development forecast identities required')
        early_rows = json.loads(gzip.decompress(parent.input('training',raw=True)))
        full_rows = json.loads(gzip.decompress(historical.input('scoring',raw=True)))
        if len(early_rows) != 800 or len(full_rows) != 1200:
            raise ValueError('complete saved receiver support required')
        result = {}
        for law in LAWS:
            scored = shorter['scored_laws'][law]
            if (len(scored['scored_times_s']) != 200 or
                    not np.allclose(np.diff(scored['scored_times_s']),
                        np.diff([row['time_s'] for row in early_rows[600:800]]),
                        rtol=0, atol=1e-6)):
                raise ValueError('aligned shorter receiver times required')
            result[law] = horizon_bins(
                scored['raw_neu_errors_m'],
                scored['conditional_neu_errors_m'],
                scored['nominal_95_half_width_neu_m'],
                early_rows[600:800])
        saved = old.artifact(TASK, 'conditional-forecast.json')
        if (saved['training_epochs'] != 800 or
                saved['prediction_epochs'] != 400 or
                saved['later_receiver_values_used'] is not False or
                saved['scientific_decision'] != 'abstain' or
                len(saved['raw_coordinates']) != 1200 or
                len(saved['conditional_receiver_mean']) != 400 or
                not np.allclose(np.diff(saved['times_s'][800:]),
                    np.diff([row['time_s'] for row in full_rows[800:]]),
                    rtol=0, atol=1e-6)):
            raise ValueError('aligned sealed longer forecast required')
        receiver = np.asarray([[math.radians(row['latitude_deg']),
                                math.radians(row['longitude_deg']),
                                row['height_m']] for row in full_rows[800:]])
        older = score_pair(saved['raw_coordinates'][800:],
                           saved['conditional_receiver_mean'],
                           saved['conditional_receiver_covariance'], receiver)
        published = json.loads((root/'docs/prediction-observed-development/'
                                'conditional-coverage-diagnostic.json').read_bytes())
        if (abs(older['coverage']['axes']['up']['nominal_95_fraction'] -
                published['diagnostic']['axes']['up']['nominal_95_fraction'])
                > 1e-12 or
                abs(older['conditional']['vertical_rms_m'] -
                    published['vertical_correction'][
                        'conditional_receiver_minus_forecast_m']['rms']) > 1e-8):
            raise ValueError('longer forecast differs from published score')
        old_bins = horizon_bins(older['raw_neu_errors_m'],
            older['conditional_neu_errors_m'],
            older['nominal_95_half_width_neu_m'], full_rows[800:])
        return dict(version='esa-height-horizon-diagnostic-v1',
            shorter_score_sha256=hashlib.sha256(score_bytes).hexdigest(),
            shorter_fit_manifest_sha256=fit.completion['manifest_sha256'],
            shorter_conditioning_manifest_sha256=condition.completion[
                'manifest_sha256'],
            longer_manifest_sha256=MANIFEST_SHA256,
            longer_scoring_sha256=SCORING_SHA256,
            report_source_sha256=hashlib.sha256((root/
                'analysis/lll/esa_forecast_horizon.py').read_bytes()).hexdigest(),
            bin_size_reports=100, shorter_bins=result, longer_bins=old_bins,
            protected_confirmation_groups_opened=0,
            independent_validation=False, confidence_calibrated=False,
            scientific_decision='abstain')
    finally:
        for study in studies:
            study.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default='.')
    parser.add_argument('--output', required=True)
    args = parser.parse_args(argv)
    result = build(args.root)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, sort_keys=True, indent=2)+'\n')
    print(json.dumps(dict(shorter_up_coverage={law:[row[
        'nominal_95_up_count'] for row in bins] for law,bins in result[
        'shorter_bins'].items()}, longer_up_coverage=[row[
        'nominal_95_up_count'] for row in result['longer_bins']]),
        sort_keys=True))


if __name__ == '__main__':
    main()
