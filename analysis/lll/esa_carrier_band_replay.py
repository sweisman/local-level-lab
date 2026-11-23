# SPDX-License-Identifier: AGPL-3.0-or-later
"""Project the recorded two-band GPS carrier correction onto a saved score."""

import argparse
from contextlib import closing
import gzip
import json
import math
from pathlib import Path
from statistics import correlation

from . import esa_qaq_ground_score as qaq
from .esa_carrier_phase_support import (
    GAMMA, L1_WAVELENGTH, L2_WAVELENGTH, pair_observation, phase_epochs,
)
from .esa_rinex_code_study import _INPUTS, _OBS
from .ilvis0_control_shards import runtime_environment
from .ilvis0_matched_observed_inputs import _write_equal
from .studies.artifacts import digest, encoded
from .studies.closed import ClosedStudy
from .studies.dependencies import source_closure


FOLDER = 'docs/prediction-observed-development/'
PLAN = FOLDER+'ESA_CARRIER_BAND_PLAN.md'
FREEZE = FOLDER+'esa-carrier-band-freeze.json'
RESULT = FOLDER+'esa-carrier-band-result.json'
PARENT_SHA = '98251d43fbaed81aeb24cb3fd8555b74636fab0c1c982a296fb315772e68a185'
INTERVALS = 120
SECOND_BAND = '2W'


def correction(first, last):
    """Return the additive L1-to-ionosphere-free range change, in metres."""
    try:
        l1a, l1b = first['l1'], last['l1']
        l2a, l2b = first['l2'][SECOND_BAND], last['l2'][SECOND_BAND]
    except KeyError:
        return None
    bands = (l1a, l1b, l2a, l2b)
    if any(item is None or item[1] or not math.isfinite(item[0]) for item in bands):
        return None
    d1 = L1_WAVELENGTH*(l1b[0]-l1a[0])
    d2 = L2_WAVELENGTH*(l2b[0]-l2a[0])
    return (d1-d2)/(GAMMA-1.)


def interval(air, station, continuity, row):
    first, last = row['start_gps_s'], row['stop_gps_s']
    satellites = row['satellites']
    weights = row['aggregate_weights']
    if (last-first != 1. or not 5 <= len(satellites) <= 32
            or len(set(satellites)) != len(satellites) or len(weights) != len(satellites)
            or not all(math.isfinite(w) for w in weights) or abs(math.fsum(weights)) > 1e-12):
        raise ValueError('fixed one-second clock-free weights required')
    aircraft, ground = [], []
    for prn in satellites:
        if prn not in continuity.get(last, set()):
            return None
        try:
            a, middle, b = [air[s]['satellites'][prn] for s in (first, first+.5, last)]
            g0, g1 = [station[s]['satellites'][prn] for s in (first, last)]
        except KeyError:
            return None
        for left, right in ((a, middle), (middle, b)):
            accepted, _ = pair_observation(left, right, .5)
            if accepted is None or accepted['l2_code'] != SECOND_BAND:
                return None
        air_delta, ground_delta = correction(a, b), correction(g0, g1)
        if air_delta is None or ground_delta is None:
            return None
        aircraft.append(air_delta)
        ground.append(ground_delta)
    return aircraft, ground


def compare(air, station, continuity, rows, gap):
    matched = []
    all_air, all_ground = [], []
    for row in rows:
        entry = dict(first_gps_s=row['start_gps_s'], last_gps_s=row['stop_gps_s'])
        observations = interval(air, station, continuity, row)
        if observations is None:
            matched.append(dict(entry, supported=False))
            continue
        a, g = observations
        weights = row['aggregate_weights']
        matched.append(dict(entry, supported=True, satellites=len(a),
                            aircraft_score=math.fsum(w*v for w,v in zip(weights, a, strict=True)),
                            ground_score=math.fsum(w*v for w,v in zip(weights, g, strict=True))))
        all_air.extend(a)
        all_ground.extend(g)
    score = {key:math.fsum(r[key] for r in matched if r['supported'])
             for key in ('aircraft_score', 'ground_score')}
    score['air_minus_ground_score'] = score['aircraft_score']-score['ground_score']
    if not all_air:
        return dict(intervals=matched, matched_values=0, supported_intervals=0)
    def rms(values):
        return math.sqrt(math.fsum(x*x for x in values)/len(all_air))
    spread = (max(all_air) > min(all_air)) and (max(all_ground) > min(all_ground))
    return dict(intervals=matched, matched_values=len(all_air),
                supported_intervals=sum(row['supported'] for row in matched),
                aircraft_rms_m=rms(all_air), ground_rms_m=rms(all_ground),
                difference_rms_m=rms(a-g for a,g in zip(all_air, all_ground, strict=True)),
                correlation=correlation(all_air, all_ground) if spread else None,
                signed_correction=score, score_gap=gap,
                fraction_of_gap={key:value/gap for key,value in score.items()})


def run(root, action):
    root = Path(root).resolve()
    raw = (root/qaq.RESULT).read_bytes()
    if digest(raw) != PARENT_SHA:
        raise ValueError('original Qaqortoq matched score required')
    parent = json.loads(raw)
    if len(parent['intervals']) != INTERVALS or parent['score_gap'] <= 0:
        raise ValueError('fixed Qaqortoq score support and positive gap required')
    own = Path(__file__).relative_to(root).as_posix()
    with closing(ClosedStudy(root, 'data/'+qaq.ID)) as study:
        if study.completion != parent['completion']:
            raise ValueError('closed Qaqortoq source must match the published score')
        freeze = encoded(dict(
            parent=study.completion, parent_sha256=PARENT_SHA,
            aircraft_excerpt_input_sha256=_INPUTS[_OBS],
            ground_excerpt_sha256=study.manifest['inputs']['ground']['sha256'],
            sources={p:digest((root/p).read_bytes()) for p in source_closure(root, (
                own, PLAN, 'analysis/tests/test_esa_carrier_band_replay.py'))},
            environment=runtime_environment(), threads=1, maximum_intervals=INTERVALS,
            maximum_satellites_per_interval=32, new_fits=0, protected_reads=0))
        path = root/FREEZE
        if action == 'freeze':
            _write_equal(path, freeze)
            return dict(freeze_sha256=digest(freeze))
        if path.read_bytes() != freeze:
            raise ValueError('unchanged saved score and replay scope required')
        airplane = gzip.decompress((root/_OBS).read_bytes())
        if digest(airplane) != _INPUTS[_OBS]:
            raise ValueError('original aircraft excerpt required')
        air = {row['seconds']:row for row in phase_epochs(airplane)}
        station, _ = qaq.decode_ground(gzip.decompress(study.input('ground', raw=True)))
        intake = study.input('intake', raw=True)
        if digest(intake) != qaq.INTAKE_SHA:
            raise ValueError('original station continuity report required')
        continuity = {row['time_s']:{int(sv[1:]) for sv in row['continued']}
                      for row in json.loads(intake)['rows']}
        result = compare(air, station, continuity, parent['intervals'], parent['score_gap'])
    result.update(freeze_sha256=digest(freeze), planned_intervals=INTERVALS,
                  new_fits=0, protected_reads=0, aircraft_error_bound_established=False,
                  scientific_decision='abstain')
    _write_equal(root/RESULT, encoded(result))
    return {key:value for key,value in result.items() if key != 'intervals'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze', 'check'))
    print(json.dumps(run(Path.cwd(), parser.parse_args().action), sort_keys=True))


if __name__ == '__main__':
    main()
