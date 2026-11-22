# SPDX-License-Identifier: AGPL-3.0-or-later
"""Same-field geometric separation after a flexible smooth path correction."""

import argparse
from contextlib import closing
import csv
import json
import math
from pathlib import Path

import numpy as np

from .esa_scored_path_shape import project_residual
from .ilvis0_matched_observed_inputs import _write_equal
from .ilvis0_precision_value import longitude_residual
from .ilvis0_solver_position import physical_metric
from .studies.artifacts import digest, encoded
from .studies.closed import ClosedStudy


BASE = 'docs/prediction-observed-development/'
PLAN = BASE + 'MATCHED_SHAPE_DRIFT_PLAN.md'
FREEZE = BASE + 'matched-shape-drift-freeze.json'
RESULT = BASE + 'matched-shape-drift-result.json'
NASA = 'docs/ilvis0-measurement-contribution/'
NASA_STUDY = 'data/ilvis0-matched-observed-preflight-v1-20261118'
NASA_REPORT = NASA + 'matched-observed-preflight-receipt.json'
ESA_REPORT = BASE + 'ESA_400_120_MODEL_MATRIX_RESULT.json'
REPORTS = {
    NASA_REPORT: '2a010e456688f320728c9fc8a2ad76b73478c2a0af012a6fd1af1b4776bd196c',
    ESA_REPORT: 'dd603cc6a72eb9b4b498bed0cecd996f66fa36f64c666b08a2bfb8d49d71a2d6',
}


def path_difference(globe, disc):
    times, reference, cut = globe
    other_times, comparison, other_cut = disc
    if (cut != other_cut or not 0 < cut <= len(times) - 4
            or not np.array_equal(times, other_times)):
        raise ValueError('matching forecast clocks and training cut required')
    reference, comparison = np.asarray(reference), np.asarray(comparison)
    if reference.shape != (len(times), 3) or comparison.shape != reference.shape:
        raise ValueError('matching three-axis forecast paths required')
    difference = comparison[cut:] - reference[cut:]
    difference[:, 1] = longitude_residual(difference[:, 1])
    difference *= physical_metric([reference[cut-1]])[0]
    counts = len(difference)
    result = project_residual(times[cut:], times[cut-1], difference, np.eye(3*counts))
    return dict(epochs=counts, total_rms_m=math.sqrt(result['total_energy']/counts),
                smooth_rms_m=math.sqrt(result['projected_energy']/counts),
                remainder_rms_m=math.sqrt(result['residual_energy']/counts))


def checked_reports(root):
    values = {}
    for path, expected in REPORTS.items():
        raw = (root/path).read_bytes()
        if digest(raw) != expected:
            raise ValueError('exact original development reports required')
        values[path] = json.loads(raw)
    nasa = (root/(NASA+'matched-observed-preflight-fits.csv')).read_bytes()
    if digest(nasa) != values[NASA_REPORT]['output_sha256']:
        raise ValueError('original NASA forecast inventory required')
    return values, list(csv.DictReader(nasa.decode().splitlines()))


def forecast(study, identity, *, nasa, expected_sha=None):
    envelope = study.envelope(identity)
    raw = study.artifact(identity, 'forecast.json', raw=True)
    if envelope['status'] != 'complete' or (expected_sha and digest(raw) != expected_sha):
        raise ValueError('saved forecast and report seals must agree')
    path = json.loads(raw)
    guard = 'later_positions_used' if nasa else 'prediction_receiver_positions_used'
    if path[guard] is not False:
        raise ValueError('later GPS positions must have been withheld')
    clock = 'query_times_s' if nasa else 'times_s'
    return (path[clock], path['coordinates'], path['training_epochs']), digest(raw)


def comparison(study, cases, available, *, nasa):
    absent = [model for model, item in cases.items() if item is None or item[0] not in available]
    if absent:
        return dict(state='missing_forecast', unavailable=absent)
    paths, hashes = {}, {}
    for model, (identity, expected) in cases.items():
        paths[model], hashes[model] = forecast(study, identity, nasa=nasa, expected_sha=expected)
    return dict(state='compared', forecast_sha256=hashes, **path_difference(*paths.values()))


def calculate(root, reports, nasa_rows):
    nasa, esa = reports[NASA_REPORT], reports[ESA_REPORT]
    output = []
    with closing(ClosedStudy(root, NASA_STUDY)) as study:
        expected = {key: nasa[key] for key in ('manifest_sha256', 'summary_sha256', 'state')}
        if study.completion != expected or len(nasa_rows) != 8:
            raise ValueError('the original eight NASA outcomes are required')
        available = {row['identity'] for row in nasa_rows if row['converged'] == 'True' and row['technical_pass'] == 'True'}
        for segment in sorted({row['segment_id'] for row in nasa_rows}):
            for field, models in (('specified', ('sphere_rotating', 'flat_geographic_field')),
                                  ('zero', ('sphere_still', 'flat_still'))):
                cases = {model: (f'{segment}-{model}', None) for model in models}
                output.append(dict(archive='NASA', segment=segment, field=field,
                                   **comparison(study, cases, available, nasa=True)))
    with closing(ClosedStudy(root, 'data/'+esa['study_id'])) as study:
        if (study.completion['manifest_sha256'] != esa['fit_manifest_sha256']
                or study.completion['summary_sha256'] != esa['fit_summary_sha256'] or len(esa['settings']) != 4):
            raise ValueError('the original four ESA settings are required')
        by_start = {(row['model'], row['profile'], row['law'], row['start']): row for row in esa['rows']}
        available = {row['identity'] for row in esa['rows'] if row['converged'] and row['forecast_complete']}
        for setting in esa['settings']:
            profile, law = setting['profile'], setting['law']
            cases = {}
            for model in ('sphere_still', 'flat_still'):
                start = setting['primary_start'][model]
                row = by_start.get((model, profile, law, start))
                cases[model] = None if row is None else (row['identity'], row['forecast_sha256'])
            output.append(dict(archive='ESA', recording=187, field='zero', profile=profile, law=law,
                               **comparison(study, cases, available, nasa=False)))
    if len(output) != 8:
        raise ValueError('every planned shape contrast must be retained')
    return output


def main():
    from .ilvis0_control_shards import runtime_environment
    from .studies.dependencies import source_closure

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze', 'calculate'))
    args = parser.parse_args()
    root = Path.cwd()
    reports, nasa_rows = checked_reports(root)
    names = (Path(__file__).relative_to(root).as_posix(), PLAN, 'analysis/tests/test_matched_shape_drift.py')
    record = dict(reports=REPORTS, environment=runtime_environment(), threads=1,
                  fit_starts=0, receiver_reads=0, maximum_forecast_reads=12, maximum_projections=8,
                  sources={name: digest((root/name).read_bytes()) for name in source_closure(root, names)})
    raw = encoded(record)
    if args.action == 'freeze':
        _write_equal(root/FREEZE, raw)
        print(digest(raw))
        return
    if (root/FREEZE).read_bytes() != raw:
        raise ValueError('unchanged bounded path-contrast freeze required')
    rows = calculate(root, reports, nasa_rows)
    result = encoded(dict(freeze_sha256=digest(raw), rows=rows, receiver_reads=0,
                          protected_reads=0, trajectory_fits=0, scientific_decision='abstain'))
    _write_equal(root/RESULT, result)
    print(json.dumps(dict(compared=sum(row['state']=='compared' for row in rows), total=len(rows),
                          sha256=digest(result)), sort_keys=True))


if __name__ == '__main__':
    main()
