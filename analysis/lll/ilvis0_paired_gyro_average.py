# SPDX-License-Identifier: AGPL-3.0-or-later
"""Compare time-averaged force directions with the paired gyro travel."""

from collections import defaultdict
from contextlib import closing
import json
from pathlib import Path

from . import ilvis0_paired_gyro_intervals as parent
from .ilvis0_matched_observed_inputs import _write_equal
from .studies.artifacts import digest, encoded


ID = 'ilvis0-paired-gyro-average-v1'
SCOPE = 'Averaged conditional force directions and paired logged gyro travel on 24 October 2009'
PLAN = parent.prior.FOLDER+'PAIRED_GYRO_AVERAGED_FORCE_PLAN.md'
RESULT = parent.prior.FOLDER+'paired-gyro-intervals-result.json'
RESULT_HASH = 'af6ad8847b6ce60ab52453f44044693383bf72dd81d409bb93ec4470d9f0718d'
WIDTHS = (.25, 1.)
MAX_FORCE_POINTS = 77_824
CASES = 64
TASK = dict(identity=parent.LEG, input_key='layout', payload={},
    limits=dict(native_calls=0, packet_visits=0, bound_calls=4+CASES,
                bound_steps=2*parent.MAX_PACKETS+parent.MAX_FORCE+MAX_FORCE_POINTS+2*CASES*parent.MAX_INTERVALS))


def direction_cone(length, magnitude_mass, count_allowance, travel):
    """Allow each mean packet vector its count error and a rotation up to travel."""
    import numpy as np

    length, mass, counts, angle = (np.asarray(x, float) for x in (length, magnitude_mass, count_allowance, travel))
    delta = counts+2*np.sin(np.minimum(angle, np.pi)/2)*(mass+counts)
    ratio = delta/length
    return np.where(ratio < 1, np.arcsin(np.clip(ratio, 0., 1.)), np.pi)


def prepare(root):
    from .studies.closed import ClosedStudy
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    if (root/'data'/ID).exists():
        raise ValueError('preserve the existing average comparison')
    raw = (root/RESULT).read_bytes()
    if digest(raw) != RESULT_HASH:
        raise ValueError('exact sealed interval comparison required')
    with closing(ClosedStudy(root, 'data/'+parent.ID)) as prior:
        if prior.completion != json.loads(raw)['completion'] or not prior.summary['passed']:
            raise ValueError('completed matched intervals required')
        layout = prior.input('layout')
        inputs = {side['original']: prior.manifest['inputs'][side['original']]['source'] for side in layout['sides']}
    layout_path = f'data/{ID}-inputs/layout.json'
    _write_equal(root/layout_path, encoded(layout))
    inputs.update(layout=layout_path, previous=RESULT, **{'force-freeze': parent.prior.FREEZE,
                  'force-result': parent.prior.RESULT})
    adapter = Path(__file__).relative_to(root).as_posix()
    sources = source_closure(root, [adapter, PLAN, 'analysis/tests/test_ilvis0_paired_gyro_average.py'])
    definition = dict(id=ID, scope=SCOPE, adapter=adapter, inputs=inputs, sources=sources,
                      tasks=[TASK], workers=1, threads=1, maximum_wall_s=90.)
    return Definition.from_dict(definition, root).prepare(root)['limits']


def windows(root, frozen, receipt, segment, *, expected_windows=parent.MAX_INTERVALS):
    """Reproduce the prior selection and recover its exact fixed GPS windows."""
    import numpy as np

    path = parent.prior.paths
    raw, source, _, pairs = path.carrier._checked_inputs(root)
    earlier, prepared = path.SUPPORT._inputs(root)
    raw.update(prepared)
    if {name: digest(value) for name, value in raw.items()} != frozen['inputs']:
        raise ValueError('original force material required')
    records = {case['segment_id']: path.SUPPORT._record(case, raw) for case in earlier['recordings']}
    primary, = (case for case in earlier['recordings'] if case['segment_id'] == segment)
    provenance = json.loads(raw[primary['artifacts']['packet-provenance.json']['path']])
    centres = {key: tuple(np.cumsum(periods)-periods/2 for periods in rec['periods'])
               for key, rec in records.items()}
    matched, selected = [], []
    for window, offsets, coordinates, _ in path._paths(root, raw, source, pairs):
        key, side = window['segment_id'], window['side']
        clock = records[key]
        tag = int(window['gps_millisecond_tag'])
        j = np.searchsorted(clock['tags'], tag)
        if j == len(clock['tags']) or clock['tags'][j] != tag:
            raise ValueError('unchanged receiver time target required')
        target = clock['times'][j]
        start, stop = int(window['packet_first']), int(window['packet_stop'])
        packet = start+int(np.argmin(abs(centres[key][0][start:stop]-target)))
        selected.append((key, tag, side, packet))
        if key == segment:
            polynomials = [path.fit_path(offsets, values, degree=parent.prior.DEGREE) for values in coordinates]
            matched.append((side, packet, target, start, stop, polynomials, (offsets[0], offsets[-1])))
    if digest(encoded(selected)) != receipt['packet_selection_sha256'] or len(matched) != expected_windows:
        raise ValueError('exact older packet selection required')
    return provenance['first_interval_start_utc_s'], records[segment], matched


def _support(ends, ref, width, start, stop):
    import numpy as np

    starts = np.r_[0., ends[:-1]]
    first = max(start, np.searchsorted(starts, ref-width/2-1e-9, side='left'))
    last = min(stop, np.searchsorted(ends, ref+width/2+1e-9, side='right'))
    if first >= last:
        return None
    return first, last, starts[first], ends[last-1]


def _prediction(polynomial, quadrature, model):
    import numpy as np

    from .ilvis0_receiver_force import evaluate_batch

    points, weights = quadrature
    coordinates, velocities, accelerations = np.asarray([parent.prior.paths.point_jet(polynomial, point)
                                                          for point in points]).transpose(1, 0, 2)
    settings = parent.prior.paths._settings(model)
    settings['gravity_mps2'] = np.full(len(points), settings['gravity_mps2'])
    forces = evaluate_batch(coordinates, velocities, accelerations, **settings)['specific_force_ned_mps2']
    return weights@parent.prior.force_in_fixed_frame(forces, coordinates, model=model)


def histories(origin, record, matched, gyros, overlap):
    import numpy as np

    from .esa_doppler_force import _quadrature_rule
    from .models import OMEGA_E

    nodes, weights = _quadrature_rule()
    counts = record['counts']
    magnitudes = np.linalg.norm(counts, axis=1)
    paths = parent.prior.paths
    result = defaultdict(list)
    for clock, periods in zip(paths.SUPPORT.CLOCKS, record['periods'], strict=True):
        ends = np.cumsum(periods)
        for j, (side, packet, target, start, stop, polys, limits) in enumerate(matched):
            centre = ends[packet]-periods[packet]/2
            for width in WIDTHS:
                support = _support(ends, centre, width, start, stop)
                if support is None:
                    continue
                first, last, lo, hi = support
                if hi-lo < .95*width or not (limits[0] <= lo-target < hi-target <= limits[1]):
                    continue
                left, right = lo+origin, hi+origin
                if left < parent.OFFSET or right > overlap-parent.OFFSET:
                    continue
                travel = max(parent._travel(index, [left], [right])[0] for index in gyros[clock])
                if not np.isfinite(travel):
                    raise ValueError('gyro support must cover each retained full-force interval')
                observed = counts[first:last].sum(axis=0)
                quant = np.sqrt(3)*paths.SUPPORT.COUNT_ERROR*(last-first)
                length = np.linalg.norm(observed)
                if length == 0.:
                    raise ValueError('direction of zero acceleration is undefined')
                within = direction_cone(length, magnitudes[first:last].sum(), quant, travel+OMEGA_E*(hi-lo)).item()
                count_only = direction_cone(length, 0., quant, 0.).item()
                quadrature = ((lo+hi)/2-target+nodes*(hi-lo)/2, weights/2)
                for track, polynomial in zip(paths.TRACKS, polys, strict=True):
                    for model in paths.average.MATCHED_MODELS:
                        predicted = _prediction(polynomial, quadrature, model)
                        result[side, clock, width, track, model].append((j, centre+origin, observed, predicted,
                                                                         count_only, within))
    return result


def compare(rows, gyros):
    import numpy as np

    from .models import OMEGA_E

    picks, times, observed, predicted, count_only, with_motion = (np.asarray(v) for v in zip(*rows, strict=True))
    adjacent = np.diff(picks) == 1
    elapsed = np.diff(times)[adjacent]
    budget = np.max([parent._travel(index, times[:-1][adjacent], times[1:][adjacent])
                     for index in gyros], axis=0)+OMEGA_E*elapsed
    if not len(budget) or not np.isfinite(budget).all():
        raise ValueError('complete common gyro support for adjacent targets required')
    summaries = {}
    for label, allowance in (('count_only', count_only), ('with_internal_motion', with_motion)):
        angles = parent.prior.screen(observed, predicted, times, maximum_rate_rad_s=0.,
            body_direction_error_rad=allowance, frame_direction_error_rad=np.zeros(len(times)))['necessary_turn_rad']
        gap = (np.asarray(angles)[adjacent]-budget)/elapsed
        summaries[label] = dict(above_both=int(np.sum(gap>0)), max_shortfall_rad_s=float(gap.max()))
    return dict(covered_pairs=len(budget), supported_centres=len(times), **summaries)


def evaluate(task, context):
    declared = {k: v for k, v in task.items() if k not in ('index','shard')}
    if context.manifest['scope'] != SCOPE or declared != TASK:
        raise ValueError('the fixed paired averaging task is required')
    layout = json.loads(context.input_path('layout').read_bytes())
    sources = list(parent.motion.streams(context, layout))
    if tuple(source['source_sha256'] for _, source, _, _ in sources) != parent.ORIGINAL_HASHES:
        raise ValueError('the original 24 October recorder pair is required')
    gyros = {clock: [parent._travel_index(*timing[clock], angles, source['angle_scale_rad_per_count'])
                    for _, source, angles, timing in sources] for clock in parent.motion.parent.CLOCKS}
    context.charge(bound_calls=1, bound_steps=parent.MAX_FORCE)
    evidence = {}
    for key in ('force-freeze', 'force-result'):
        raw = context.input_path(key).read_bytes()
        if digest(raw) != parent.HASHES[key]:
            raise ValueError('unchanged force history receipts required')
        evidence[key] = json.loads(raw)
    origin, record, matched = windows(context.root.parents[1], evidence['force-freeze'],
                                      evidence['force-result'], parent.SEGMENTS[0])
    context.charge(bound_calls=1, bound_steps=MAX_FORCE_POINTS)
    by_case = histories(origin-layout['begin'], record, matched, gyros, layout['end']-layout['begin'])
    if len(by_case) != CASES:
        raise ValueError('all 64 fixed average histories are required')
    results = []
    for (side, clock, width, track, model), rows in sorted(by_case.items()):
        context.charge(bound_calls=1, bound_steps=2*parent.MAX_INTERVALS)
        results.append(dict(side=side, clock=clock, width_s=width, track=track, model=model,
                            **compare(rows, gyros[clock])))
    context.save_bytes('paired-averages.json', encoded(dict(summaries=results, fit_starts=0,
        validated_aircraft_bound=False, scientific_decision='abstain')))
    return dict(passed=True, summaries=len(results), scientific_decision='abstain')
