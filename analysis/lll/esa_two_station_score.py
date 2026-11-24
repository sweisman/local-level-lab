# SPDX-License-Identifier: AGPL-3.0-or-later
"""Conditional shared range score from two matched ground receivers."""

import argparse
from contextlib import closing
import json
import math
from pathlib import Path

from .studies.artifacts import digest, encoded


ID = 'esa-two-station-score-v1'
SCOPE = 'Two ground receivers on the sealed ESA 187 airborne score rows'
BASE = 'docs/prediction-observed-development/'
PLAN = BASE+'ESA_TWO_STATION_SCORE_PLAN.md'
PARENT = BASE+'esa-nkar-phase-transfer-result.json'
PARENT_SHA = 'c43f33005a7844453ccd6c7c2d1ac094eb615f2799821b7b4564104b17c0740c'
RESULT = BASE+'esa-two-station-score-result.json'
INTERVALS = 120
TASK = dict(identity='common-ground-score', input_key='parent', payload={}, limits=dict(
    native_calls=0, packet_visits=0, bound_calls=3, bound_steps=3*INTERVALS))


def minimum_station_error(near, far, weights, *, target=None):
    """Nearest equal-radius ball intersection with the optional signed plane."""
    import numpy as np

    a, b, w = (np.asarray(x, dtype=float) for x in (near, far, weights))
    if (a.ndim != 1 or not len(a) or b.shape != a.shape or w.shape != a.shape
            or not all(np.isfinite(x).all() for x in (a, b, w))):
        raise ValueError('finite matched range vectors and weights required')
    norm = np.linalg.norm(w)
    if norm <= 0 or (target is not None and not math.isfinite(target)):
        raise ValueError('nonzero score direction and finite signed target required')
    if target is None:
        common = (a+b)/2.
    else:
        normal = w/norm
        heights = target/norm-np.array([a@normal, b@normal])
        first, second = a+heights[0]*normal, b+heights[1]*normal
        segment = second-first
        squared = segment@segment
        fraction = np.clip(.5+(heights[1]**2-heights[0]**2)/(2*squared), 0., 1.) if squared else .5
        common = first+fraction*segment
    errors = [float(np.linalg.norm(common-x)/math.sqrt(len(a))) for x in (a, b)]
    score = float(w@common)
    if target is not None and not math.isclose(score, target, rel_tol=1e-12, abs_tol=1e-12):
        raise ValueError('common range witness misses its required signed projection')
    return dict(common=common.tolist(), station_rms=errors, maximum_rms=max(errors), score=score)


def prepare(root):
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    if (root/'data'/ID/'manifest.json').exists():
        raise ValueError('preserve the existing finite comparison')
    if digest((root/PARENT).read_bytes()) != PARENT_SHA:
        raise ValueError('exact published matched two-station ranges required')
    adapter = Path(__file__).relative_to(root).as_posix()
    sources = source_closure(root, (adapter, PLAN, 'analysis/tests/test_esa_two_station_score.py'))
    definition = dict(id=ID, scope=SCOPE, adapter=adapter, inputs=dict(parent=PARENT, plan=PLAN),
                      sources=sources, tasks=[TASK], workers=1, threads=1, maximum_wall_s=30)
    return Definition.from_dict(definition, root).prepare(root)['limits']


def _observations(rows):
    count = len(rows)
    times = [row['start_gps_s'] for row in rows]
    fields = ('nkar_m', 'qaq_m', 'weights')
    if count != INTERVALS or any(b-a != 1 for a, b in zip(times, times[1:])):
        raise ValueError('all frozen consecutive shared intervals required')
    for row in rows:
        sats = row['satellites']
        if not 5 <= len(sats) <= 16 or sats != sorted(set(sats)):
            raise ValueError('ordered common GPS support required')
        if any(len(row[key]) != len(sats) or abs(math.fsum(row[key])) > 1e-12 for key in fields):
            raise ValueError('coincident receiver-clock-centred range and weight rows required')
    return [[x for row in rows for x in row[key]] for key in fields]


def evaluate(task, context):
    if (context.manifest['scope'] != SCOPE
            or {key: value for key, value in task.items() if key not in ('index', 'shard')} != TASK):
        raise ValueError('the frozen two-station task is required')
    raw = context.input_path('parent').read_bytes()
    if digest(raw) != PARENT_SHA:
        raise ValueError('frozen matched observations changed')
    parent = json.loads(raw)
    if not parent['passed'] or parent['protected_reads'] or parent['new_fits']:
        raise ValueError('only qualified development-only matched rows may enter')
    gap = parent['score_gap']
    if not math.isfinite(gap) or gap <= 0:
        raise ValueError('a positive saved model score gap is required')
    context.charge(bound_calls=1, bound_steps=INTERVALS)
    near, far, weights = _observations(parent['withheld_rows'])
    free = minimum_station_error(near, far, weights)
    possibilities = {'unrestricted': free}
    for name, target in (('negative_gap', -gap), ('positive_gap', gap)):
        context.charge(bound_calls=1, bound_steps=INTERVALS)
        possibilities[name] = minimum_station_error(near, far, weights, target=target)
    context.save('common-range-witnesses.json', possibilities)
    rows = parent['withheld_rows']
    return dict(passed=True, scientific_decision='abstain', independent_aircraft_error_cap_established=False,
                intervals=len(rows), ranges=len(weights), first_gps_s=rows[0]['start_gps_s'],
                last_gps_s=rows[-1]['start_gps_s']+1, score_gap=gap,
                station_score_shares=[math.fsum(w*x for w, x in zip(weights, values, strict=True))/gap
                                      for values in (near, far)],
                cases={key: {name: item for name, item in value.items() if name != 'common'}
                       for key, value in possibilities.items()},
                new_fits=0, original_downloads=0, protected_reads=0)


def report(root):
    from .ilvis0_matched_observed_inputs import _write_equal
    from .studies.closed import ClosedStudy

    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        envelope = study.envelope(TASK['identity'])
        if envelope['charged'] != TASK['limits'] or not envelope['result']['passed']:
            raise ValueError('the complete charged two-station result is required')
        summary = dict(envelope['result'], completion=study.completion, charged=envelope['charged'],
                       input_sha256=PARENT_SHA)
        witnesses = study.artifact(TASK['identity'], 'common-range-witnesses.json')
    _write_equal(root/RESULT, encoded(dict(summary, witnesses=witnesses)))
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'report'))
    print(json.dumps({'prepare': prepare, 'report': report}[parser.parse_args().action](Path.cwd()), sort_keys=True))
