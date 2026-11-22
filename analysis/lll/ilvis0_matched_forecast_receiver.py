# SPDX-License-Identifier: AGPL-3.0-or-later
"""Sensitivity of existing forecasts to a common reference in the GPS hull."""

import argparse
from contextlib import closing
import json
from pathlib import Path
import platform

import numpy as np

from . import ilvis0_matched_observed_preflight as parent
from .ilvis0_matched_observed_inputs import _write_equal
from .ilvis0_precision_value import longitude_residual
from .ilvis0_solver_position import physical_metric
from .studies.artifacts import digest, encoded
from .studies.closed import ClosedStudy


SOURCE = 'analysis/lll/ilvis0_matched_forecast_receiver.py'
TEST = 'analysis/tests/test_ilvis0_matched_forecast_receiver.py'
PLAN = parent.FOLDER+'MATCHED_FORECAST_RECEIVER_PLAN.md'
FREEZE = parent.FOLDER+'matched-forecast-receiver-freeze.json'
RESULT = parent.FOLDER+'matched-forecast-receiver-receipt.json'
PARENT_RECEIPT = parent.FOLDER+'matched-observed-preflight-receipt.json'
HORIZONS = (30., 60., 120., None)
MODELS = ('sphere_rotating', 'sphere_still', 'flat_geographic_field')
PAIRS = (('same_field_shape', 'sphere_rotating', 'flat_geographic_field'),
         ('within_globe_field', 'sphere_rotating', 'sphere_still'))


def distances(points, vertices):
    """Return exact geometric min/max distance to three vertices' convex hull."""
    points, vertices = np.asarray(points, float), np.asarray(vertices, float)
    if (points.ndim != 2 or points.shape[1] not in (1, 2)
            or vertices.shape != (len(points), 3, points.shape[1])
            or not np.isfinite(points).all() or not np.isfinite(vertices).all()):
        raise ValueError('three finite receiver vertices per point required')
    delta = points[:, None, :]-vertices
    maximum = np.max(np.linalg.norm(delta, axis=2), axis=1)
    if points.shape[1] == 1:
        edges = delta[:, :, 0]
        return np.maximum(0., np.maximum(edges.min(axis=1), -edges.max(axis=1))), maximum
    edge = np.roll(vertices, -1, axis=1)-vertices
    squared = np.sum(edge*edge, axis=2)
    projection = np.divide(np.sum(delta*edge, axis=2), squared, where=squared>0., out=np.zeros_like(squared))
    away = delta-np.clip(projection, 0., 1.)[:, :, None]*edge
    minimum = np.min(np.linalg.norm(away, axis=2), axis=1)
    signs = edge[:, :, 0]*delta[:, :, 1]-edge[:, :, 1]*delta[:, :, 0]
    area = edge[:, 0, 0]*edge[:, 1, 1]-edge[:, 0, 1]*edge[:, 1, 0]
    inside = ((area > 0.) & np.all(signs >= 0., axis=1)) | ((area < 0.) & np.all(signs <= 0., axis=1))
    return np.where(inside, 0., minimum), maximum


def paired_range(first, second, vertices):
    """Bound mean square error of second minus first with a shared reference."""
    delta = second-first
    gaps = np.einsum('nd,nkd->nk', delta, (first+second)[:, None, :]-2.*vertices)
    low, high = float(np.mean(gaps.min(axis=1))), float(np.mean(gaps.max(axis=1)))
    leverage = float(2.*np.mean(np.linalg.norm(delta, axis=1)))
    margin = max(0., low, -high)
    return dict(lower_difference_m2=low, upper_difference_m2=high,
        ordering='first' if low>0. else 'second' if high<0. else 'can_tie_or_reverse',
        additional_radius_for_tie_m=margin/leverage if leverage else 0.)


def _local(coordinates, reference, metric):
    delta = np.asarray(coordinates, float)-reference
    if delta.shape != reference.shape or not np.isfinite(delta).all():
        raise ValueError('finite aligned forecast coordinates required')
    delta[:, 1] = longitude_residual(delta[:, 1])
    return delta*metric


def _summarize(time, trajectories, vertices):
    rows = []
    for horizon in HORIZONS:
        n = len(time) if horizon is None else int(np.searchsorted(time, horizon, side='right'))
        if n < 2 or (horizon is not None and time[-1] < horizon):
            raise ValueError('full declared forecast support required')
        record = dict(horizon_s=horizon, epochs=n, last_time_s=float(time[n-1]), forecasts={}, pairs={})
        for axis, use in (('horizontal', slice(0, 2)), ('height', slice(2, 3))):
            gps = vertices[:n, :, use]
            model = {name: values[:n, use] for name, values in trajectories.items()}
            for name, values in model.items():
                lower, upper = distances(values, gps)
                record['forecasts'].setdefault(name, {})[axis] = dict(
                    lower_rms_m=float(np.sqrt(np.mean(lower**2))), upper_rms_m=float(np.sqrt(np.mean(upper**2))))
            for label, first, second in PAIRS:
                record['pairs'].setdefault(label, {})[axis] = paired_range(model[first], model[second], gps)
        rows.append(record)
    return rows


def build(study):
    receipt = study.input('input_receipt')
    by_record = []
    if (study.summary['total']!=8 or study.summary['completed']!=7
            or study.summary['state']!='terminal' or len(receipt['recordings'])!=2
            or sum(item['scoring_epochs'] for item in receipt['recordings'])!=371):
        raise ValueError('exact closed preflight and original prediction support required')
    for item in receipt['recordings']:
        identity = item['segment_id']
        query = study.input(identity+'-queries')
        scoring = study.input(identity+'-scoring')
        cut, count = item['training_epochs'], item['scoring_epochs']
        times = np.asarray(query['query_times_s'], float)
        if (len(times)!=cut+count or np.any(np.diff(times)<=0.)
                or scoring['query_times_s']!=query['query_times_s'][cut:]
                or set(scoring['coordinates'])!=set(parent.TRACKS)):
            raise ValueError('different later receiver support')
        reference = np.asarray(scoring['coordinates']['onboard'], float)
        metric = physical_metric(reference)
        vertices = np.stack([_local(scoring['coordinates'][track], reference, metric)
                             for track in parent.TRACKS], axis=1)
        forecasts = {}
        for model in MODELS:
            case = identity+'-'+model
            result = study.envelope(case)['result']
            forecast = study.artifact(case, 'forecast.json')
            if (not result['passed'] or not result['converged'] or forecast['later_positions_used']
                    or forecast['training_epochs']!=cut or forecast['query_times_s']!=query['query_times_s']):
                raise ValueError('changed sealed forecast identity or support')
            forecasts[model] = _local(forecast['coordinates'][cut:], reference, metric)
        missing = study.rows.get(identity+'-flat_still')
        if missing is not None and study.envelope(identity+'-flat_still')['result']['passed']:
            raise ValueError('unexpected zero-field disc forecast')
        by_record.append(dict(segment_id=identity, imu_type=item['imu_type'], missing_forecast='flat_still',
            horizons=_summarize(times[cut:]-times[cut-1], forecasts, vertices)))
    return by_record


def main():
    from .studies.dependencies import source_closure

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze', 'replay'))
    args = parser.parse_args()
    root = Path.cwd()
    with closing(ClosedStudy(root, 'data/'+parent.ID)) as study:
        prior = (root/PARENT_RECEIPT).read_bytes()
        checked = json.loads(prior)
        if (any(checked[k]!=v for k,v in study.completion.items())
                or checked['preflight_technical_passes']!=6):
            raise ValueError('unchanged verified forecast preflight required')
        config = encoded(dict(parent=study.completion, parent_receipt_sha256=digest(prior),
            sources={p:digest((root/p).read_bytes()) for p in source_closure(root,(SOURCE,TEST,PLAN))},
            python=platform.python_version(), numpy=np.__version__, threads=1,
            maxima=dict(recordings=2, forecasts=6, epochs=371), horizons_s=HORIZONS, fit_starts=0))
        if args.action=='freeze':
            _write_equal(root/FREEZE, config)
            print(digest(config))
            return
        if (root/FREEZE).read_bytes()!=config:
            raise ValueError('forecast comparison differs from its source and input freeze')
        result = dict(freeze_sha256=digest(config), trajectories=build(study),
                      receiver_error_calibrated=False, absolute_fit_qualified=False,
                      fit_starts=0, scientific_decision='abstain')
    _write_equal(root/RESULT, encoded(result))
    print(json.dumps(dict(recordings=len(result['trajectories']), receipt_sha256=digest(encoded(result)))))


if __name__=='__main__':
    main()
