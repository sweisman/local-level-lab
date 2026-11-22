# SPDX-License-Identifier: AGPL-3.0-or-later
"""Cross prediction conditioning with the distance metric on one sealed pair."""

import argparse
from contextlib import closing
import json
import math
from pathlib import Path

import numpy as np

from . import esa_changing_drift_transfer as full
from .esa_joint_path_score import _ranges
from .esa_scored_path_shape import project_residual
from .forecast_smooth_error import decompose
from .ilvis0_control_shards import runtime_environment
from .ilvis0_matched_observed_inputs import _write_equal
from .matched_shape_drift import ESA_REPORT, REPORTS, forecast
from .studies.artifacts import digest, encoded
from .studies.closed import ClosedStudy
from .studies.dependencies import source_closure


PLAN = full.FOLDER + 'MATCHED_SHAPE_METRIC_PLAN.md'
FREEZE = full.FOLDER + 'matched-shape-metric-freeze.json'
RESULT = full.FOLDER + 'matched-shape-metric-result.json'
REFERENCE = full.FOLDER + 'forecast-pair-information-result.json'
REFERENCE_SHA = '5e44f2662084cc635c857e8d6e742f814652e73219ae65d777304289ed0ad88f'
PAIR = ('sphere_still', 'flat_still')
WEIGHT = 'fixed_3cm'


def compare(root, report, reference, saved):
    setting = next(row for row in reference['settings'] if row['complete'] and row['imu_law'] == 'increment')
    selected = {name: setting['selected'][name] for name in PAIR}
    bound = {row['identity']: row for row in report['rows']}
    checked = next(row for row in report['settings'] if row['profile'] and row['law'] == 'increment')
    if any(selected[name] != f"{name}-1-increment-{checked['primary_start'][name]}" for name in PAIR):
        raise ValueError('the original training-selected shape pair is required')
    with closing(ClosedStudy(root, 'data/'+report['study_id'])) as study:
        if (study.completion['manifest_sha256'] != report['fit_manifest_sha256']
                or study.completion['summary_sha256'] != report['fit_summary_sha256']):
            raise ValueError('closed original ESA matrix required')
        times = study.input('forecast_times')
        paths = []
        for identity in selected.values():
            (clock, raw, cut), _ = forecast(study, identity, nasa=False, expected_sha=bound[identity]['forecast_sha256'])
            if clock != times or cut != full.CUT or len(raw) != len(times) or len(times) != full.CUT+full.LATER:
                raise ValueError('matching 400/120 paths required')
            paths.append(full._chart(raw[cut:], np.asarray(saved['anchor'])))
    raw_difference = paths[1]-paths[0]
    centers = {row['identity']: row['ranges'][WEIGHT]['center_m'] for row in saved['rows']
               if row['identity'] in selected.values()}
    conditioned = np.asarray(centers[selected[PAIR[1]]])-np.asarray(centers[selected[PAIR[0]]])
    weights = np.broadcast_to(np.eye(3)*full.POLICY['receiver_white_std_m'], (len(times), 3, 3))
    operator = full.operator(times, weights)
    if operator.configuration != saved['operator_configurations'][WEIGHT]:
        raise ValueError('exact original working covariance required')
    results = {}
    for name, difference in (('raw', raw_difference), ('conditioned', conditioned)):
        flat = project_residual(times[full.CUT:], times[full.CUT-1], difference, np.eye(difference.size))
        scaled = decompose(operator, times, difference, training_epochs=full.CUT)
        results[name] = dict(metres=dict(total=flat['total_energy'], remaining=flat['residual_energy']),
                             covariance=dict(total=scaled['total_squared_error'],
                                 remaining=scaled['through_degree'][2]['remaining_squared_error']))
    baseline = setting['arms']['full/'+WEIGHT]['/'.join(PAIR)]
    expected = baseline['after_degrees'][2]['squared_distance']
    if not math.isclose(results['conditioned']['covariance']['remaining'], expected, rel_tol=1e-9):
        raise ValueError('conditioned covariance calculation differs from the original')
    return dict(paths=results, selected=selected, recording=187, scientific_decision='abstain',
                receiver_reads=0, protected_reads=0, trajectory_fits=0)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze', 'calculate'))
    args = parser.parse_args()
    root = Path.cwd()
    contents = {name: (root/name).read_bytes() for name in (ESA_REPORT, REFERENCE, full.FREEZE, full.RANGES, full.SEAL)}
    if digest(contents[REFERENCE]) != REFERENCE_SHA or digest(contents[ESA_REPORT]) != REPORTS[ESA_REPORT]:
        raise ValueError('original sealed pair comparisons required')
    saved = _ranges(contents, full)
    names = (Path(__file__).relative_to(root).as_posix(), PLAN)
    config = encoded(dict(inputs={name: digest(raw) for name, raw in contents.items()},
                          sources={name: digest((root/name).read_bytes()) for name in source_closure(root, names)},
                          environment=runtime_environment(), threads=1, operators=1, archived_forecasts=2,
                          projections=4, receiver_reads=0, fit_starts=0))
    if args.action == 'freeze':
        _write_equal(root/FREEZE, config)
        print(digest(config))
        return
    if (root/FREEZE).read_bytes() != config:
        raise ValueError('unchanged bounded metric comparison required')
    result = compare(root, json.loads(contents[ESA_REPORT]), json.loads(contents[REFERENCE]), saved)
    raw = encoded(dict(result, freeze_sha256=digest(config)))
    _write_equal(root/RESULT, raw)
    print(digest(raw))


if __name__ == '__main__':
    main()
