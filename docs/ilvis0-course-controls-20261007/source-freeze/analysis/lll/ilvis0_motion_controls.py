# SPDX-License-Identifier: AGPL-3.0-or-later
"""Deterministic course-filter controls and recorded receiver-track maneuvers.

No Earth-model simulation, threshold calibration, or scientific eligibility change.
Recorded controls are ground-track changes, not independently measured body yaw.
"""
from collections import Counter
import argparse
import fcntl
import json
import os
from pathlib import Path
import platform
import numpy as np

from . import ilvis0_motion_diagnosis as motion
from . import applanix as ap, ilvis0 as il, ilvis0_followup as follow

VERSION = 'ilvis0-course-controls-v1'


def pulse_controls():
    """Known, noiseless finite-duration course corrections; test possible hidden motion."""
    times = np.arange(0, 120.001, .02)
    limit = .05
    rows = []
    for duration in (.2, .5, 1, 2, 4, 8, 12, 20, 40):
        for rate in (.06, .1, .2, .5):
            # Exact integral of a rate pulse, rather than numerical differentiation.
            course = rate * np.clip(times - 40, 0, duration)
            measures = {}
            for span in motion.SPANS:
                measured = motion.local_slope(times, course, span)
                peak = float(np.nanmax(np.abs(measured)))
                measures[str(span)] = dict(peak_rate_deg_s=peak, exceeds_original_limit=peak > limit,
                                           retained_peak_fraction=peak / rate)
            rows.append(dict(duration_s=duration, true_rate_deg_s=rate,
                             net_course_change_deg=duration * rate, measurements=measures))
    return dict(version=VERSION, controls=rows, threshold_deg_s=limit,
                missed_controls={str(span): sum(not r['measurements'][str(span)]['exceeds_original_limit'] for r in rows)
                                 for span in motion.SPANS},
                missed_sustained_controls_12s_or_longer={str(span): sum(
                    r['duration_s'] >= 12 and not r['measurements'][str(span)]['exceeds_original_limit'] for r in rows)
                    for span in motion.SPANS},
                scientific_eligibility_changes=0,
                interpretation='Long-interval regression can hide real short corrections. No adopted interval or calibrated acceptance rule follows from these controls.')


def receiver_maneuvers(nav, receiver, minimum_span_s=30, minimum_change_deg=3):
    """Select non-overlapping substantial ground-track changes without any gyro values.

    Endpoints are actual receiver epochs, with <=2-second gaps. The interval is supported
    by a net receiver change; it does not assert the gyro/body-rate mechanism of that change.
    """
    t = np.asarray([r['utc_week_s'] for r in receiver], float)
    course = np.rad2deg(np.unwrap(np.deg2rad([r['course_deg'] for r in receiver])))
    nt = np.asarray([r['utc_week_s'] for r in nav], float)
    nc = np.rad2deg(np.unwrap(np.arctan2([r['velocity_east_mps'] for r in nav],
                                       [r['velocity_north_mps'] for r in nav])))
    receiver_rates = {str(s): motion.local_slope(t, course, s) for s in motion.SPANS}
    nav_rates = {str(s): motion.local_slope(nt, nc, s) for s in motion.SPANS}
    events, reasons = [], Counter()
    if len(t) < 3 or np.any(np.diff(t) <= 0):
        return dict(events=[], reason='insufficient or unordered receiver support')
    busy_until = -np.inf
    for left, start in enumerate(t):
        if start <= busy_until:
            continue
        right = np.searchsorted(t, start + minimum_span_s)
        if right >= len(t):
            break
        if t[right] - start > minimum_span_s + 2 or np.any(np.diff(t[left:right+1]) > 2):
            reasons['missing_receiver_support'] += 1
            continue
        change = course[right] - course[left]
        if abs(change) < minimum_change_deg:
            continue
        stop = t[right]
        receiver_selected = (t >= start) & (t <= stop)
        nav_selected = (nt >= start) & (nt <= stop)
        nav_times = nt[nav_selected]
        nav_complete = (len(nav_times) >= 3 and nav_times[0] - start <= 2
                        and stop - nav_times[-1] <= 2 and np.all(np.diff(nav_times) <= 2))
        checks = {}
        for span in motion.SPANS:
            key = str(span)
            checks[key] = {}
            for kind, rates, selected in (('receiver', receiver_rates, receiver_selected),
                                           ('navigation', nav_rates, nav_selected)):
                valid = rates[key][selected]
                valid = valid[np.isfinite(valid)]
                supported = bool(len(valid) and (kind == 'receiver' or nav_complete))
                checks[key][kind] = dict(supported=supported,
                    exceeds_original_limit=bool(supported and np.any(np.abs(valid) > .05)),
                    peak_rate_deg_s=float(np.max(np.abs(valid))) if supported else None)
        events.append(dict(start_s=float(start), end_s=float(stop), net_receiver_course_change_deg=float(change),
                           endpoint_average_rate_deg_s=float(change / (stop - start)), measurements=checks))
        busy_until = stop
    return dict(events=events, rejected_intervals=dict(reasons),
                selection='actual receiver ground-track endpoint change >=3 degrees in >=30 seconds; no gyro values',
                interpretation='Recorded route maneuvers, not independent body-yaw truth or a calibrated scientific gate.')


def run(corpus, units, retention, output):
    corpus, units, retention, output = map(Path, (corpus, units, retention, output))
    if json.loads((units / 'status.json').read_text())['state'] != 'complete':
        raise ValueError('finish the units audit first; at most two total CPU threads')
    with (units / 'run.lock').open('r') as unit_lock:
        fcntl.flock(unit_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    unit_manifest = json.loads((units / 'manifest.json').read_text())
    tasks = [t for c in unit_manifest['configurations'] for t in c['representatives']]
    retained = {r['task_id']: r for r in json.loads((retention / 'summary.json').read_text())['results']}
    records = {r['task_id']: r for r in map(json.loads, (corpus / 'records.jsonl').read_text().splitlines())}
    sources = [Path(__file__), Path(motion.__file__), Path(ap.__file__), Path(il.__file__), Path(follow.__file__),
               Path(__file__).parents[1] / 'tests/ilvis0_motion_controls_worker.py']
    inputs = [units / 'manifest.json', units / 'summary.json', corpus / 'records.jsonl',
              retention / 'summary.json', retention / 'cleanup.jsonl']
    manifest = dict(version=VERSION, tasks=tasks, python=platform.python_version(), numpy=np.__version__,
                    sources={str(p): il.sha256(p) for p in sources}, inputs={str(p): il.sha256(p) for p in inputs},
                    course_limit_deg_s=.05, regression_spans_s=list(motion.SPANS),
                    receiver_selection=dict(minimum_span_s=30, minimum_change_deg=3),
                    threads={k: os.environ.get(k) for k in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS')})
    if output.exists() and not (output / 'manifest.json').is_file():
        raise ValueError('unmarked motion controls directory')
    output.mkdir(parents=True, exist_ok=True)
    with (output / 'run.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if (output / 'manifest.json').exists():
            if json.loads((output / 'manifest.json').read_text()) != manifest:
                raise ValueError('motion controls source/input/environment mismatch')
        else:
            follow.atomic_json(output / 'manifest.json', manifest)
        def frozen():
            for p in sources + inputs:
                if il.sha256(p) != manifest['sources'].get(str(p), manifest['inputs'].get(str(p))):
                    raise ValueError('frozen motion controls source/input changed')
        reports = []
        for task in tasks:
            frozen()
            follow.atomic_json(output / 'status.json', dict(state='running', pid=os.getpid(),
                              completed=len(reports), total=len(tasks), task_id=task))
            dest = output / (task + '.json')
            if dest.exists():
                report = json.loads(dest.read_text())
            else:
                row = retained[task]
                try:
                    nav, receiver, provenance = motion.read_motion(follow.source_path(corpus, records[task]), row['source_sha256'])
                    report = dict(receiver_maneuvers(nav, receiver), provenance=provenance)
                except ValueError as error:
                    report = dict(error=str(error), events=[])
                report.update(task_id=task, filename=row['filename'])
                follow.atomic_json(dest, report)
            reports.append(report)
        known = pulse_controls()
        events = [e for r in reports for e in r['events']]
        detections = {}
        for span in motion.SPANS:
            key = str(span)
            detections[key] = {kind: dict(supported=sum(e['measurements'][key][kind]['supported'] for e in events),
                                         detected=sum(e['measurements'][key][kind]['exceeds_original_limit'] for e in events))
                               for kind in ('receiver', 'navigation')}
        summary = dict(version=VERSION, state='complete', files=len(reports), errors=sum('error' in r for r in reports),
                       results=reports, known_course_controls=known, recorded_ground_track_maneuvers=len(events),
                       recorded_maneuver_detections=detections, scientific_eligibility_changes=0,
                       earth_model_fit_attempts=0, originals_deleted=0)
        frozen()
        follow.atomic_json(output / 'summary.json', summary)
        compact = {k: v for k, v in summary.items() if k not in ('results', 'known_course_controls')}
        follow.atomic_json(output / 'status.json', dict(compact, pid=os.getpid()))
        print(json.dumps(compact), flush=True)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--corpus', type=Path, default=Path('data/ilvis0-ready'))
    parser.add_argument('--units', type=Path, default=Path('data/ilvis0-imu6-cross-date-20261007'))
    parser.add_argument('--retention', type=Path, default=Path('data/ilvis0-retention-84-20261007'))
    parser.add_argument('--output', type=Path, default=Path('data/ilvis0-course-controls-20261007'))
    a = parser.parse_args()
    run(a.corpus, a.units, a.retention, a.output)


if __name__ == '__main__':
    main()
