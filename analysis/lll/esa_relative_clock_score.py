# SPDX-License-Identifier: AGPL-3.0-or-later
"""Rescore the fixed ESA forecasts from the sealed clock-only comparison."""

from contextlib import closing
import json
from pathlib import Path

from .airquantumgrav_geographic_report import error_metrics
from .esa_final_orbit_replay import _baseline_rows
from .esa_final_orbit_score import (
    LATER, ORIGINAL_COMPARISON, ORIGINAL_SHA, PPP_SHA, TRAIN, _coordinates, _load,
    score_forecast_paths,
)
from .esa_relative_clock_replay import BLOCK, COUNT, EXCLUDED_PRN, FOLDER, ID, REFERENCE_PRN, _task
from .studies.artifacts import ArchiveStore, atomic, digest, encoded
from .studies.closed import ClosedStudy


MANIFEST_SHA = '7003b74ea8af7a506baf5203a712d29126042462cd4e7d43fb034c0666f0d892'
RESULT = FOLDER + 'esa-relative-clock-score-result.json'
EFFECTS = ('excluded_minus_full_neu_m', 'adjusted_minus_restricted_neu_m')


def build(root):
    previous = _load(root, ORIGINAL_COMPARISON, ORIGINAL_SHA)['result']
    indices = previous['matched_code_indices']
    if len(indices) != TRAIN + LATER or indices != sorted(set(indices)):
        raise ValueError('original ordered GPS matches required')
    later = indices[TRAIN:]
    with closing(ArchiveStore(root)) as store:
        with closing(ClosedStudy(root, 'data/' + ID, store=store)) as study:
            if (study.completion['manifest_sha256'] != MANIFEST_SHA
                    or study.completion['state'] != 'complete' or not study.summary['passed']
                    or study.summary['charged']['bound_calls'] != 2 * COUNT):
                raise ValueError('completed paired clock study required')
            baseline = _baseline_rows(study.input('baseline', raw=True))
            epochs = [row for start in range(0, COUNT, BLOCK) for row in
                      json.loads(study.artifact(_task(start)['identity'], 'clock-epochs.json', raw=True))]
            if len(epochs) != COUNT or any(
                    not row['passed'] or row['gps_week_seconds'] != ref['gps_week_seconds']
                    or row['satellites'] != [prn for prn in ref['dual_frequency']['used_satellites']
                                            if prn != EXCLUDED_PRN]
                    for row, ref in zip(epochs, baseline, strict=True)):
                raise ValueError('complete original epochs and fixed matched satellite sets required')
            summary_sha = study.completion['summary_sha256']
            anchors = study.input('anchors')
        paths = dict(
            broadcast=_coordinates([baseline[i]['dual_frequency'] for i in later]),
            restricted=[epochs[i]['restricted_position'] for i in later],
            anchored_clock=[epochs[i]['clock_adjusted_position'] for i in later],
        )
        comparisons = score_forecast_paths(root, store, paths, previous, comparison_key='by_clock')
    effects = {name: [row[name] for row in epochs] for name in EFFECTS}
    return dict(
        observed_recording='187', epochs=len(epochs), later_epochs=LATER,
        reference_gps_satellite=REFERENCE_PRN, excluded_gps_satellite=EXCLUDED_PRN,
        clock_manifest_sha256=MANIFEST_SHA, clock_summary_sha256=summary_sha,
        broadcast_comparison_sha256=ORIGINAL_SHA, prior_forecast_binding_sha256=PPP_SHA,
        all_effects={name: error_metrics(values) for name, values in effects.items()},
        later_effects={name: error_metrics([values[i] for i in later]) for name, values in effects.items()},
        range_evaluations=sum(row['range_evaluations'] for row in epochs),
        maximum_clock_correction_range_m=max(row['maximum_clock_correction_range_m'] for row in epochs),
        clock_difference_anchors=anchors, signed_changes_neu_m=effects, forecast_comparisons=comparisons,
        new_inertial_fits=0, new_forecast_propagations=0, protected_reads=0,
        absolute_receiver_accuracy_established=False, scientific_decision='abstain',
    )


if __name__ == '__main__':
    root = Path.cwd()
    result = build(root)
    raw = encoded(result)
    path = root / RESULT
    if path.exists():
        if path.read_bytes() != raw:
            raise ValueError('existing result differs from matched clock replay')
    else:
        atomic(path, raw)
    print(encoded(dict(epochs=result['epochs'], later_effects=result['later_effects'],
                       result_sha256=digest(raw))).decode(), end='')
