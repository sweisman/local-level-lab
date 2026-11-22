# SPDX-License-Identifier: AGPL-3.0-or-later
"""Measure shared-antenna receiver disagreement in an archived shape direction."""

from contextlib import closing
import gzip
import json
from pathlib import Path
import sys

from .esa_alternate_ppp_scoring import AIR1, BASE, FULL, INVENTORY, PARENT, TARGETS
from .esa_full_parallel_gnss_v2 import EXPECTED_ROLLOVERS
from .esa_parallel_gnss import MATCH_TOLERANCE_S, match_times
from .esa_parallel_gnss_120s import WIDTH_S
from .esa_ppp_acquisition import verify_complete
from .esa_rinex_code_comparison import FOLDER, PARENT_SHA, coordinates
from .esa_shape_receiver_margin import PRIOR_FREEZE, PRIOR_RESULT, PRIOR_SHA
from .esa_shape_receiver_replay import EARLIER, LATER, WITNESS, WITNESS_MANIFEST
from .studies.artifacts import ArchiveStore, atomic, digest, encoded
from .studies.closed import ClosedStudy


PLAN = FOLDER + 'ESA_PPP_SHAPE_ERROR_PLAN.md'
FREEZE = FOLDER + 'esa-ppp-shape-error-freeze.json'
RESULT = FOLDER + 'esa-ppp-shape-error-result.json'
WINDOWS = FOLDER + 'parallel-gnss-120s-result.json'
WINDOWS_SHA = '711846ee666d4fbe88d68697673902120e9f18bdae4eb8cb314724abd6ca556f'
FULL_SHA = 'f0cf2f2f1db5855c74c8c39962acc537c0867516cf61ae72b6145ca41ecfb74b'
FAST_WINDOWS, FULL_REPORTS = 195, 64080
TOTAL = EARLIER + LATER


def probe_windows(approved, differences, coefficients, *, comparison_bounds):
    """Apply fixed weights on full report grids and preserve exclusions."""
    import numpy as np

    rows = []
    for window in approved:
        start = window * WIDTH_S - EARLIER
        stop = start + TOTAL
        if start <= comparison_bounds[1] and stop - 1 >= comparison_bounds[0]:
            rows.append(dict(window_id=window, status='overlaps_comparison'))
            continue
        stamps = range(start, stop)
        missing = sum(t not in differences for t in stamps)
        if missing:
            rows.append(dict(window_id=window, status='incomplete', missing_reports=missing))
            continue
        measured = np.asarray([differences[t] for t in stamps])
        rows.append(dict(window_id=window, status='complete',
                         signed_difference=float(np.sum(measured * coefficients))))
    return rows


def _read_json(path, expected):
    raw = path.read_bytes()
    if digest(raw) != expected:
        raise ValueError('sealed report changed: ' + path.name)
    return json.loads(raw)


def _read_measurements(root, full, window_report, origin, operator, shape, baseline_score):
    import numpy as np

    from .airquantumgrav_receiver import records
    from .esa_changing_drift_transfer import _chart
    from .esa_full_parallel_gnss import _sha
    from .esa_parallel_gnss_time import corrected_neu
    from .esa_receiver_sequence_wrap import records_with_sequence_wrap
    from .ilvis0_solver_position import physical_metric
    from .state_space_directional_bound import adjoint_intervals

    reference_path = root / BASE / AIR1
    if _sha(reference_path) != full['reference_sha256']:
        raise ValueError('opened air1 export hash differs')
    with reference_path.open() as stream:
        reference = list(records(stream))
    index_by_time = {record['time_s']: i for i, record in enumerate(reference)}
    if len(reference) != FULL_REPORTS or len(index_by_time) != FULL_REPORTS:
        raise ValueError('the complete unique original export is required')
    indices = [index_by_time[row['time_s']] for row in origin]
    if any(any(reference[index][key] != row[key] for key in ('latitude_deg', 'longitude_deg', 'height_m'))
           for index, row in zip(indices, origin, strict=True)) or indices != sorted(set(indices)):
        raise ValueError('archived comparison epochs do not reproduce')
    needed = set(indices)
    observed = np.asarray(coordinates(origin))
    raw_chart = _chart(observed, observed[0])
    chart_per_local = np.asarray(shape['metric']) / physical_metric(observed)
    time_limits = (origin[0]['time_s'], origin[-1]['time_s'])
    if any(abs(row['time_s']-round(row['time_s'])) > MATCH_TOLERANCE_S for row in origin):
        raise ValueError('archive score does not have the planned one-second phase')

    q = np.r_[np.zeros(3 * EARLIER), shape['direction']]
    low, high = adjoint_intervals(operator, q)
    coeff = ((low + high) / 2).reshape(TOTAL, 3)
    results = []
    for name, size in TARGETS.items():
        previous = next(row for row in full['sources'] if row['filename'] == name)
        approved = [row['window_id'] for source in window_report['sources']
                    if source['filename'] == name for row in source['windows'] if row['fast_window']]
        if len(approved) != FAST_WINDOWS or approved != sorted(set(approved)):
            raise ValueError('exact 195 fast-window identities required')
        path = root / BASE / name
        receipt = json.loads((root / BASE / (name + '.receipt.json')).read_bytes())
        if verify_complete(path, size, receipt) != previous['source_sha256']:
            raise ValueError('opened alternate export hash differs')
        audit = {}
        with path.open() as stream:
            parsed = records_with_sequence_wrap(stream, expected_rollovers=EXPECTED_ROLLOVERS[name], audit=audit)
            matched = match_times(reference, parsed)
            for _ in parsed:
                pass
        if len(matched) != previous['matched_epochs'] or audit != previous['sequence_audit']:
            raise ValueError('opened alternate export match count differs')

        grid, target = {}, {}
        for index, other in matched:
            original = reference[index]
            exact = original['time_s']
            nominal = round(exact)
            on_grid = abs(exact - nominal) <= MATCH_TOLERANCE_S
            if not on_grid and index not in needed:
                continue
            raw, common = corrected_neu(original, other)
            if on_grid:
                if nominal in grid:
                    raise ValueError('ambiguous reference time at the nominal second')
                grid[nominal] = common
            if index in needed:
                target[index] = (other, np.asarray(common) - raw)
        comparison = dict(status='incomplete', matched_epochs=len(target))
        if set(target) == needed:
            alternatives = [target[index][0] for index in indices]
            raw_change = _chart(np.asarray(coordinates(alternatives)), observed[0]) - raw_chart
            time_change = np.asarray([target[index][1] for index in indices]) * chart_per_local
            raw_effect = float(q @ operator.whiten(raw_change.ravel()))
            corrected_effect = float(q @ operator.whiten((raw_change + time_change).ravel()))
            if not np.isclose(corrected_effect, float(np.sum(coeff * (raw_change + time_change))),
                              atol=1e-9, rtol=1e-8):
                raise ValueError('forward and adjoint receiver effects disagree')
            comparison.update(status='complete', raw_score_change=raw_effect,
                corrected_score_change=corrected_effect, corrected_midpoint=baseline_score + corrected_effect,
                corrected_earlier_component=float(np.sum(coeff[:EARLIER] *
                                                         (raw_change + time_change)[:EARLIER])),
                maximum_match_offset_s=max(abs(a['time_s'] - b['time_s'])
                                           for a, b in zip(alternatives, origin, strict=True)))
        windows = probe_windows(approved, grid, coeff, comparison_bounds=time_limits)
        complete = [abs(row['signed_difference']) for row in windows if row['status'] == 'complete']
        results.append(dict(filename=name, fixed_comparison=comparison, fast_windows=windows,
            max_absolute_probe_score=max(complete, default=None),
            p95_absolute_probe_score=float(np.quantile(complete, .95)) if complete else None))
    return results


def run(root, action):
    from .ilvis0_control_shards import runtime_environment
    from .innovations_snapshot import restore
    from .studies.dependencies import source_closure

    full = _read_json(root / FULL, FULL_SHA)
    windows = _read_json(root / WINDOWS, WINDOWS_SHA)
    prior = _read_json(root / PRIOR_RESULT, PRIOR_SHA)
    prior_freeze = _read_json(root / PRIOR_FREEZE, prior['freeze_sha256'])
    if (windows['full_result_sha256'] != FULL_SHA or full['reference_reports'] != FULL_REPORTS
            or windows['reference_sha256'] != full['reference_sha256']
            or full['inventory_sha256'] != digest((root / INVENTORY).read_bytes())):
        raise ValueError('exact opened receiver inventory required')
    with closing(ArchiveStore(root)) as store:
        with closing(ClosedStudy(root, 'data/' + WITNESS, store=store)) as witness:
            if witness.completion['manifest_sha256'] != WITNESS_MANIFEST or not witness.summary['passed']:
                raise ValueError('fixed matched-field score direction required')
            shape, times = witness.input('shape-direction'), witness.input('forecast_times')
            snapshot = witness.input('later-operator', raw=True)
        with closing(ClosedStudy(root, PARENT, store=store)) as parent:
            if parent.completion['manifest_sha256'] != PARENT_SHA:
                raise ValueError('the opened parent receiver source is required')
            origin = json.loads(gzip.decompress(parent.input('training', raw=True)))[:TOTAL]
    first = origin[0]['time_s'] - times[0]
    if (len(times) != TOTAL or prior_freeze['direction_sha256'] != digest(encoded(shape))
            or prior_freeze['operator_sha256'] != digest(snapshot) or prior['nominal_separation'] != shape['nominal']
            or any(abs(first + t - row['time_s']) > 1e-8 for t, row in zip(times, origin, strict=True))):
        raise ValueError('unchanged score and position timeline required')

    archived = {AIR1: full['reference_sha256']}
    archived.update({row['filename']: row['source_sha256'] for row in full['sources']})
    sources = source_closure(root, [Path(__file__).relative_to(root).as_posix(),
                                   PLAN, 'analysis/tests/test_esa_ppp_shape_error.py'])
    freeze = encoded(dict(
        input_sha256={FULL: FULL_SHA, WINDOWS: WINDOWS_SHA, PRIOR_RESULT: PRIOR_SHA},
        archive=dict(parent=PARENT_SHA, witness=WITNESS_MANIFEST),
        sources={p: digest((root / p).read_bytes()) for p in sources},
        environment=runtime_environment(), threads=1, receiver_export_sha256=archived,
        maximum_receiver_exports=3, fast_windows_per_export=FAST_WINDOWS, adjoint_passes=1,
        fit_starts=0, forecast_propagations=0, protected_reads=0,
    ))
    target = root / FREEZE
    if action == 'freeze':
        if not target.exists():
            atomic(target, freeze)
        if target.read_bytes() != freeze:
            raise ValueError('existing PPP score freeze differs')
        print(digest(freeze))
        return
    if target.read_bytes() != freeze:
        raise ValueError('unchanged finite PPP receiver audit required')
    operator = restore(snapshot, expected_sha256=shape['factors_sha256'],
                       expected_configuration=shape['configuration'], maximum_bytes=2**26)
    baseline_score = prior['scores']['original']['signed_midpoint']
    results = _read_measurements(root, full, windows, origin, operator, shape, baseline_score)
    raw = encoded(dict(freeze_sha256=digest(freeze), original_signed_midpoint=baseline_score,
        receiver_comparisons=results, same_aircraft_antenna=True, calibrated=False, scientific_decision='abstain'))
    result = root / RESULT
    if not result.exists():
        atomic(result, raw)
    if result.read_bytes() != raw:
        raise ValueError('saved PPP receiver audit differs')
    print(digest(raw))


if __name__ == '__main__':
    if len(sys.argv) != 2 or sys.argv[1] not in ('freeze', 'calculate'):
        raise SystemExit('usage: python -m lll.esa_ppp_shape_error {freeze,calculate}')
    run(Path.cwd(), sys.argv[1])
