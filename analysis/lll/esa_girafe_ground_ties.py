# SPDX-License-Identifier: AGPL-3.0-or-later
"""Compare saved ground force with the campaign's measured apron gravity values."""

from contextlib import closing
import json
import math
from pathlib import Path
from statistics import fmean
import sys

from .esa_girafe import (
    BASE, GPS_AT_UTC_MIDNIGHT, REPORT as INVENTORY, TARGETS, read_rows, verify_file,
)
from .studies.artifacts import atomic, digest, encoded
from .studies.closed import ClosedStudy

FOLDER = 'docs/prediction-observed-development/'
ID = 'esa-girafe-ground-ties-v1'
SCOPE = 'compare the two saved ESA 187 ground stops with the campaign apron gravity measurements'
PLAN = FOLDER + 'ESA_GIRAFE_GROUND_TIES_PLAN.md'
RESULT = FOLDER + 'esa-girafe-ground-ties-result.json'
FORCE = FOLDER + 'esa-ground-force-support-result.json'
FIRST = FOLDER + 'ground-receiver-control-result.json'
SECOND = FOLDER + 'second-ground-interval-result.json'
INPUT_HASHES = {
    FORCE: 'b8dbbe6bf7ac8565cf7379ffae39f8358850994f38e5b1d8dec005766b06e1be',
    FIRST: '558160e791f780ec3f4b56d0ce8b9ff53ba5baceece7ba951d0f104426c556b3',
    SECOND: '482637109319f04b373fb5d32fb4829f637015e5f38a24070099eccfc8d2c697',
    INVENTORY.as_posix(): 'f05496e18b04f34cbed3f09538d286ba8ed3191f60a44d41ec956c6aaeeeec91',
}
REFERENCE = 'https://doi.org/10.5194/essd-17-1667-2025'
TIES = {
    'GOH': dict(latitude_deg=64.1908984290, longitude_deg=-51.6756369418, height_m=109.422,
                gravity_mgal=982173.440),
    'RKV': dict(latitude_deg=64.1315813460, longitude_deg=-21.9466651338, height_m=76.642,
                gravity_mgal=982263.301),
}
MAX_DISTANCE_M = 100.
HEIGHT_GRADIENT = -3.086e-6
ANTENNA_ABOVE_SENSOR_M = {'imar': 1.60, 'girafe': 1.12}
ROW_LIMIT = 321325
TASKS = [dict(identity=name, input_key='sites', payload=dict(airport=name),
              limits=dict(native_calls=0, packet_visits=0, bound_calls=2, bound_steps=ROW_LIMIT))
         for name in TIES]


def height_adjusted_reference(gravity_mgal, antenna_height_m, reference_height_m, antenna_above_sensor_m):
    delta = antenna_height_m-antenna_above_sensor_m-reference_height_m
    return gravity_mgal*1e-5+HEIGHT_GRADIENT*delta


def force_summary(samples, *, stop_start):
    axes = [[], [], []]
    magnitudes, halves, temperatures = [], [], []
    minutes = {}
    first = last = None
    for sample in samples:
        if first is None:
            first = sample.utc_seconds
        last = sample.utc_seconds
        for axis, value in zip(axes, sample.xyz_mps2, strict=True):
            axis.append(value)
        magnitudes.append(math.hypot(*sample.xyz_mps2))
        halves.append(sample.half_interrogation_s)
        temperatures.append(sample.quartz_deg_c)
        minute = math.floor((sample.utc_seconds-stop_start)/60.)
        minutes.setdefault(minute, []).append(sample.xyz_mps2)
    if not magnitudes:
        raise ValueError('at least one force sample required')
    complete_minutes = []
    for minute, values in minutes.items():
        if len(values) >= 599:
            complete_minutes.append(dict(minute=minute, samples=len(values),
                magnitude_mps2=math.hypot(*(fmean(axis) for axis in zip(*values, strict=True)))))
    mean_vector = [fmean(axis) for axis in axes]
    return dict(samples=len(magnitudes), first_utc_s=first, last_utc_s=last,
                mean_vector_mps2=mean_vector, mean_vector_magnitude_mps2=math.hypot(*mean_vector),
                mean_sample_magnitude_mps2=fmean(magnitudes), mean_atom_axis_mps2=mean_vector[2],
                half_interrogation_s=[min(halves), max(halves)], mean_quartz_deg_c=fmean(temperatures),
                complete_minutes=complete_minutes)


def _bound_sites(root):
    from .esa_parallel_gnss import relative_neu

    parsed = {}
    for path, expected in INPUT_HASHES.items():
        raw = (root / path).read_bytes()
        if digest(raw) != expected:
            raise ValueError('original ground or inventory report changed')
        parsed[path] = json.loads(raw)
    sites = {}
    receiver = (parsed[FIRST]['stability'], parsed[SECOND]['result'])
    imar = parsed[FORCE]['ground']['stops']
    for position, force, expected_name in zip(receiver, imar, TIES, strict=True):
        observed = {axis: position[key] for axis, key in zip(
            ('latitude_deg', 'longitude_deg', 'height_m'),
            ('latitude_center_deg', 'longitude_center_deg', 'height_center_m'), strict=True)}
        offsets = {airport: relative_neu(tie, observed) for airport, tie in TIES.items()}
        chosen = min(offsets, key=lambda airport: math.hypot(*offsets[airport][:2]))
        displacement = offsets[chosen]
        if chosen != expected_name or math.hypot(*displacement[:2]) > MAX_DISTANCE_M:
            raise ValueError('saved ground site cannot be associated with its apron reference')
        span = force['time_range_s']
        if not position['first_time_s'] <= span[0] < span[1] <= position['last_time_s']:
            raise ValueError('saved iMAR interval leaves the receiver-selected ground stop')
        sites[chosen] = dict(antenna=observed, distance_neu_m=displacement, tie=TIES[chosen],
                            imar=force, times_utc_s=[t-GPS_AT_UTC_MIDNIGHT for t in span])
    return dict(sites=sites, files=parsed[INVENTORY.as_posix()]['files'], input_hashes=INPUT_HASHES)


def prepare(root):
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    directory = root / 'data' / (ID+'-inputs')
    if directory.exists() or (root / 'data' / ID).exists():
        raise ValueError('existing ground ties freeze must stay intact')
    inputs = {}
    for name in TARGETS:
        original = BASE / name
        verify_file(root / original, name)
        inputs[name] = original.as_posix()
    target = directory / 'sites.json'
    atomic(target, encoded(_bound_sites(root)))
    inputs['sites'] = target.relative_to(root).as_posix()
    adapter = Path(__file__).relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE, adapter=adapter, inputs=inputs, tasks=TASKS,
        sources=source_closure(root, [adapter, PLAN, 'analysis/tests/test_esa_girafe_ground_ties.py']),
        workers=1, threads=1, maximum_wall_s=90.)
    print(encoded(Definition.from_dict(definition, root).prepare(root)['limits']).decode(), end='')


def _samples(path, first, last):
    with path.open('rb') as stream:
        for row in read_rows(stream):
            if row.utc_seconds > last:
                break
            if row.utc_seconds >= first:
                yield row


def evaluate(task, context):
    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or declared not in TASKS:
        raise ValueError('exact airport gravity task required')
    data = json.loads(context.input_path('sites').read_bytes())
    airport = task['payload']['airport']
    site = data['sites'][airport]
    start, end = site['times_utc_s']
    tie = site['tie']
    ref = tie['gravity_mgal']*1e-5
    refs = {name: height_adjusted_reference(tie['gravity_mgal'], site['antenna']['height_m'],
            tie['height_m'], offset) for name, offset in ANTENNA_ABOVE_SENSOR_M.items()}
    girafe = {}
    for name, acquisition in data['files'].items():
        if acquisition['first_utc_s'] > end or acquisition['last_utc_s'] < start:
            continue
        context.charge(bound_calls=1, bound_steps=acquisition['samples'])
        summary = force_summary(_samples(context.input_path(name), start, end), stop_start=start)
        magnitude = summary['mean_vector_magnitude_mps2']
        girafe[name] = summary | dict(mean_minus_apron_mps2=magnitude-ref,
            mean_minus_height_adjusted_apron_mps2=magnitude-refs['girafe'],
            atom_minus_height_adjusted_apron_mps2=summary['mean_atom_axis_mps2']-refs['girafe'])
    imar = site['imar']
    magnitude = imar['mean_vector_magnitude_m_s2']
    row = dict(airport=airport, airport_reference=tie, antenna_neu_from_reference_m=site['distance_neu_m'],
               times_utc_s=site['times_utc_s'], height_adjusted_references_mps2=refs, girafe=girafe,
               imar=dict(samples=imar['samples'], mean_vector_magnitude_mps2=magnitude,
                         mean_minus_apron_mps2=magnitude-ref,
                         mean_minus_height_adjusted_apron_mps2=magnitude-refs['imar']),
               scientific_decision='abstain')
    context.save_bytes('ground-tie.json', encoded(row))
    return dict(passed=bool(girafe), scientific_decision='abstain')


def report(root):
    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        if not study.summary['passed'] or len(study.rows) != len(TASKS):
            raise ValueError('complete two-stop gravity comparison required')
        rows = [study.artifact(task['identity'], 'ground-tie.json') for task in TASKS]
        if study.summary['charged']['bound_calls'] != sum(len(row['girafe']) for row in rows):
            raise ValueError('ground comparison ledger differs from the source reads')
        result = dict(ground_stops=rows, charged=study.summary['charged'], source_reports=INPUT_HASHES,
                      manifest_sha256=study.completion['manifest_sha256'], campaign_reference=REFERENCE,
                      protected_reads=0, imar_rereads=0, earth_model_fits=0, scientific_decision='abstain')
    raw = encoded(result)
    path = root / RESULT
    if not path.exists():
        atomic(path, raw)
    if path.read_bytes() != raw:
        raise ValueError('saved GIRAFE ground tie result differs')
    print(digest(raw))


if __name__ == '__main__':
    if sys.argv[1:] == ['prepare']:
        prepare(Path.cwd())
    elif sys.argv[1:] == ['report']:
        report(Path.cwd())
    else:
        raise SystemExit('usage: python -m lll.esa_girafe_ground_ties {prepare,report}')
