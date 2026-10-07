# SPDX-License-Identifier: AGPL-3.0-or-later
"""Small registered-state checks on nominal pairwise timing passes, never calibration."""
import argparse
import gzip
import hashlib
import itertools
import json
from pathlib import Path
import time

import numpy as np
import screen_safe_turn_timings as timings
from lll.design_envelope import envelope_assumptions, nuisance_states

ROOT = timings.ROOT
baseline = timings.baseline
SOURCE = 'docs/research-next-stage-20261006/safe-turn-timing-screen.json'


def review():
    began = time.monotonic()
    inputs = {SOURCE: hashlib.sha256((ROOT / SOURCE).read_bytes()).hexdigest()}
    prior = json.loads((ROOT / SOURCE).read_text())
    tracks, cases = {}, []
    for relative in baseline.ARCHIVES:
        inputs[relative] = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
        with gzip.open(ROOT / relative, 'rt') as source:
            tracks.update({t['id']: t for t in json.load(source)['tracks']})
    for case in prior['cases']:
        promising = [(s, c) for s in case['scored'] for c in s['candidates']
                     if any(p['all_estimable'] for p in c['nominal_pair_criteria'].values())]
        if not promising:
            continue
        track = tracks[case['track_id']]
        spec = baseline.smooth_track_spec(baseline.track_spec(dict(id=case['track_id'],
            source_sha256=track['source_sha256'], status='prepared_geometry_only',
            rows=[r for r in track['rows'] if case['start_s'] <= r['t_s'] <= case['end_s']],
            candidate_window=dict(start_s=case['start_s'], end_s=case['end_s']))))
        replay = baseline.TrackReplay(spec)
        t = np.arange(0., replay.duration, 1.)
        kin = dict(t=t, **replay.sample(t), bearing_ok=replay.support(t))
        for scored, candidate in promising:
            schedule = scored['schedule_minutes']
            design = baseline.realize(600902, 'wind+bias_mixed', geometry='observed',
                trajectory_input=spec, turn_schedule=schedule)
            problem = baseline.geometry_problem(design, schedule, candidate['crab_model'],
                                                kin=(kin, replay.duration))
            states = [(label, values) for label, values in nuisance_states(problem)
                      if np.allclose(values[2::3], 0., atol=1e-14, rtol=0.)]
            states.sort(key=lambda item: np.linalg.norm(item[1]))
            pairs = [p for p, v in candidate['nominal_pair_criteria'].items() if v['all_estimable']]
            failures, tested = {}, []
            for (label, values), offset, (anchor, coefficients) in itertools.product(
                    states, (0., 3 * problem.forward_sigma, -3 * problem.forward_sigma),
                    baseline.models.EXPECTED_K.items()):
                z = np.zeros(problem.npar)
                z[:3] = coefficients
                z[problem.p:problem.p + problem.nc] = values
                z[-1] = offset
                _, jac = problem.prediction(z, True)
                jac, weights = problem.observation_information(z, jac,
                    np.full(len(problem.y), (baseline.RAD2DPH / 6.) ** 2))
                report = baseline.science_information(jac, weights)['report']
                retention = {p: report['model_contrast_information'][p]['pre_cutoff_retained_fraction']
                             for p in pairs}
                result = dict(nuisance_state=label, nuisance_values=values.tolist(),
                    forward_offset_deg=float(np.degrees(offset)), anchor=anchor,
                    pair_retention=retention)
                tested.append(result)
                for p, value in retention.items():
                    if value < baseline.CANDIDATE_POLICY['retention_threshold'] and p not in failures:
                        failures[p] = dict(tested_state_index=len(tested) - 1, **result)
                if len(failures) == len(pairs) or len(tested) >= 30:
                    break
            cases.append(dict(track_id=case['track_id'], start_s=case['start_s'], end_s=case['end_s'],
                trajectory_hash=spec['trajectory_hash'], schedule_minutes=schedule,
                crab_model=candidate['crab_model'], nominal_passing_pairs=pairs,
                envelope_assumptions=envelope_assumptions(problem.settings),
                tested_states=tested, counterexamples=failures,
                unresolved_pairs=[p for p in pairs if p not in failures], svd_evaluations=len(tested)))
    return dict(state='bounded_partial_timing_counterexample_checks_complete', cases=cases,
        maximum_svd_evaluations_per_schedule=30,
        svd_evaluations=sum(c['svd_evaluations'] for c in cases), elapsed_s=time.monotonic() - began,
        input_sha256=inputs, implementation_hash=baseline.implementation_hash(),
        retention_threshold=baseline.CANDIDATE_POLICY['retention_threshold'],
        helper_sha256={str(Path(p).resolve().relative_to(ROOT)): hashlib.sha256(Path(p).read_bytes()).hexdigest()
            for p in (__file__, timings.__file__, baseline.__file__)},
        additional_flight_attempts=0, error_rate_validated=False,
        limitations=['Adaptive subset of nominal passes; overlapping windows are not independent evidence.',
            'Exact registered reference-TAS wind states, offsets0/+15/-15deg, nominal mount epochs and6dph only.',
            'At most30 states per schedule; no-failure results remain inconclusive, not full-envelope passes.',
            'A recorded failing state disproves that pair passing every registered state.',
            'Broad wind already fails these nominal controls; physical wind assumptions remain provisional.',
            'No new simulated IMU, axis recovery, full preprocessing, nonlinear fit, power or calibration.'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = review()
    with args.output.open('x') as out:
        out.write(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps(dict(schedules=len(result['cases']), svd_evaluations=result['svd_evaluations'],
        disproved_pairs=sum(len(c['counterexamples']) for c in result['cases']),
        unresolved_pairs=sum(len(c['unresolved_pairs']) for c in result['cases']), elapsed_s=result['elapsed_s'])))
