# SPDX-License-Identifier: AGPL-3.0-or-later
"""Score sealed IMU8 forecasts on an exactly aligned companion receiver."""

import argparse
from contextlib import closing
import csv
import gzip
import io
import json
from pathlib import Path

import numpy as np

from . import ilvis0_matched_forecast_receiver as scorer
from . import ilvis0_receiver_window_pairs_study as pairs
from .ilvis0_control_shards import runtime_environment
from .ilvis0_matched_observed_layout import OUTPUT as LAYOUT
from .ilvis0_receiver_overlap import _time_index
from .studies.artifacts import ArchiveStore, digest, encoded
from .studies.closed import ClosedStudy

FOLDER = scorer.parent.FOLDER
PAIR = '0f3ee9210f85e8b60bae'
SEGMENT = '3df34ea39a6cbdbe15bb0f36'
PRIMARY = '683ac516120685564714'
COMPANION = 'ad2d5717b2c1c2ed3589'
PLAN = FOLDER+'COMPANION_FORECAST_PLAN.md'
FREEZE = FOLDER+'companion-forecast-freeze.json'
RESULT = FOLDER+'companion-forecast-receipt.json'


def reference_choices(training_difference, later_difference):
    training, later = (np.asarray(a, float) for a in (training_difference, later_difference))
    if any(a.ndim != 2 or a.shape[1] != 3 or not len(a) or not np.isfinite(a).all()
           for a in (training, later)):
        raise ValueError('paired finite receiver differences required in both splits')
    offset = np.median(training, axis=0)
    return offset, dict(onboard=np.zeros_like(later), companion_raw=later,
                        companion_training_offset=later-offset)


def _receiver_coordinates(index, tags):
    values = np.array([[float(index[tag][key]) for key in
        ('latitude_deg', 'longitude_deg', 'ellipsoid_height_m')] for tag in tags])
    values[:, :2] = np.deg2rad(values[:, :2])
    return values


def load(root):
    layout_raw = (root/LAYOUT).read_bytes()
    record = next(x for x in json.loads(layout_raw)['layouts'] if x['segment_id']==SEGMENT)
    if record['source_task'] != PRIMARY:
        raise ValueError('the saved IMU8 selection changed its receiver')
    with closing(ArchiveStore(root)) as store:
        receivers = ClosedStudy(root, 'data/'+pairs.IDENTITY, store=store)
        forecasts = ClosedStudy(root, 'data/'+scorer.parent.ID, store=store)
        pair = receivers.tasks[PAIR]
        if (pair['left_task'] != PRIMARY or pair['right_task'] != COMPANION
                or not receivers.envelope(PAIR)['result']['passed'] or receivers.completion['state']!='complete'
                or forecasts.completion['state']!='terminal'):
            raise ValueError('the declared receiver pair and sealed forecast study are required')
        rows = receivers.input(pair['right_key'], raw=True)
        if digest(rows) != pair['right_sha256']:
            raise ValueError('the companion receiver bytes changed')
        by_time = _time_index(csv.DictReader(io.StringIO(gzip.decompress(rows).decode())))
        inputs = {'layout': digest(layout_raw), 'companion': digest(rows)}
        splits = []
        for side, count in (('training', 445), ('scoring', 223)):
            key = SEGMENT+'-'+side
            data = forecasts.input(key)
            inputs[side] = forecasts.manifest['inputs'][key]['sha256']
            tags = data['gps_tags_ms']
            if len(tags) != count or sorted(set(tags)) != tags or not set(tags) <= by_time.keys():
                raise ValueError('the exact companion receiver coverage changed')
            onboard = np.asarray(data['coordinates']['onboard'], float)
            difference = scorer._local(_receiver_coordinates(by_time, tags), onboard,
                                       scorer.physical_metric(onboard))
            splits.append((data['query_times_s'], onboard, difference))
        train_time, _, train_diff = splits[0]
        later_time, ref, later_diff = splits[1]
        seconds = np.asarray(later_time)-train_time[-1]
        if seconds[0] <= 0. or np.any(np.diff(seconds) <= 0.):
            raise ValueError('ordered unchanged forecast horizon required')
        metric = scorer.physical_metric(ref)
        models = {}
        for model in scorer.MODELS:
            identity = SEGMENT+'-'+model
            envelope = forecasts.envelope(identity)
            forecast = forecasts.artifact(identity, 'forecast.json')
            if (not envelope['result']['converged'] or not envelope['result']['passed']
                    or forecast['later_positions_used'] or forecast['training_epochs'] != len(train_time)
                    or forecast['query_times_s'] != train_time+later_time):
                raise ValueError('changed or unqualified saved forecast')
            inputs[model] = envelope['artifacts'][f'artifacts/{identity}/forecast.json']
            models[model] = scorer._local(forecast['coordinates'][len(train_time):], ref, metric)
        zero_disc = SEGMENT+'-flat_still'
        if zero_disc in forecasts.rows and forecasts.envelope(zero_disc)['result']['passed']:
            raise ValueError('unexpected zero-field disc result')
        lineage = dict(inputs=inputs, receiver_parent=receivers.completion,
                       forecast_parent=forecasts.completion, pair_id=PAIR, segment_id=SEGMENT)
    return seconds, models, train_diff, later_diff, lineage


def score(seconds, trajectory, training, later, lineage):
    offset, references = reference_choices(training, later)
    horizons = []
    for horizon in scorer.HORIZONS:
        count = len(seconds) if horizon is None else int(np.searchsorted(seconds, horizon, side='right'))
        if count < 2 or (horizon is not None and seconds[-1] < horizon):
            raise ValueError('saved forecast lacks its declared horizon')
        by_reference = {}
        for name, reference in references.items():
            values = {}
            for model, path in trajectory.items():
                delta = path[:count]-reference[:count]
                rms = np.sqrt(np.mean(delta**2, axis=0))
                values[model] = dict(neu_rms_m=rms.tolist(), horizontal_rms_m=float(np.hypot(*rms[:2])))
            by_reference[name] = values
        horizons.append(dict(horizon_s=horizon, epochs=count, by_reference=by_reference))
    vertices = np.stack(tuple(references.values()), axis=1)
    return dict(**lineage, training_epochs=len(training), later_epochs=len(later),
        training_companion_offset_neu_m=offset.tolist(),
        later_companion_relative_rms_neu_m=np.sqrt(np.mean((later-offset)**2, axis=0)).tolist(),
        horizons=horizons, joint_reference_sensitivity=scorer._summarize(seconds, trajectory, vertices),
        missing_forecast='flat_still', position_solves=0, navigation_fits=0,
        absolute_error_calibrated=False, scientific_decision='abstain')


if __name__ == '__main__':
    from .studies.dependencies import source_closure

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze', 'replay'))
    args = parser.parse_args()
    root = Path.cwd()
    material = load(root)
    own = Path(__file__).relative_to(root).as_posix()
    sources = source_closure(root, (own, PLAN, 'analysis/tests/test_ilvis0_companion_forecast.py'))
    config = encoded(dict(lineage=material[-1], environment=runtime_environment(),
        sources={p: digest((root/p).read_bytes()) for p in sources}, scoring_epochs=223, training_epochs=445,
        score_combinations=36, threads=1, navigation_fits=0))
    if args.action == 'freeze':
        scorer._write_equal(root/FREEZE, config)
        print(digest(config))
    else:
        if (root/FREEZE).read_bytes() != config:
            raise ValueError('changed companion forecast freeze')
        result = score(*material)
        scorer._write_equal(root/RESULT, encoded(dict(result, freeze_sha256=digest(config))))
        print(json.dumps(dict(training_epochs=result['training_epochs'], later_epochs=result['later_epochs'],
                              full_horizon=result['horizons'][-1])))
