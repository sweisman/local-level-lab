# SPDX-License-Identifier: AGPL-3.0-or-later
"""Inspect saved pilot preprocessing; never generate a flight or fit a science model."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'analysis'))

import numpy as np
from lll.attitude import epoch_of, estimate_forward_axis, mount_epochs
from lll.format import read_session
from lll.maneuvers import maneuver_mask
from lll.research_design import plain
from lll.segments import Thresholds, find_segments, gnss_kinematics


def audit(directory, matched_smoothing=False, reference_uncertainty=False):
    campaign_path = directory / 'campaign.json'
    campaign = json.loads(campaign_path.read_text())
    cases = []
    for row in campaign['records']:
        saved = directory / 'diagnostics' / row['task_id']
        session = read_session(saved / 'session.zip')
        flight = session.phase('flight')
        th = Thresholds()
        gyro = np.load(saved / 'turn-input.npz', allow_pickle=False)
        t, calibrated = gyro['t'], gyro['calibrated_gyro']
        gn = session.slice('gnss', flight['start_ns'], flight['end_ns'])
        motion = maneuver_mask(gnss_kinematics(gn, th), max_turn_dps=th.max_turn_dps,
                              max_vz_mps=th.max_vz_mps, min_speed_mps=th.min_speed_mps,
                              max_h_acc_m=th.max_h_acc_m)
        events = [(ns / 1e9, kind) for ns, kind, _ in session.events
                  if kind in ('index_turn', 'placement_shift')
                  and flight['start_ns'] <= ns <= flight['end_ns']]
        gs = session.slice(session.gyro_stream(), flight['start_ns'], flight['end_ns'])
        rate = session.manifest['imu']['config']['rate_hz']
        epochs, exclude = mount_epochs(t, calibrated, events, sat=gs.get('sat'),
                                      expected_period=1 / rate, aircraft_motion=motion)
        matrices = np.load(saved / 'mount-matrices.npy', allow_pickle=False)
        np.testing.assert_allclose(matrices, [e['R0'] for e in epochs])
        _, kin = find_segments(session, flight, th, exclude=exclude)
        bins = np.load(saved / 'fit-input.npz', allow_pickle=False)
        ge = epoch_of(t, epochs)
        keep = ge >= 0
        unresolved = next((i for i, e in enumerate(epochs)
                           if e.get('orientation_unresolved')), None)
        if unresolved is not None:
            keep &= ge < unresolved
        mapped = np.einsum('nij,nj->ni', matrices[ge[keep]], calibrated[keep])
        axis, quality = estimate_forward_axis(t[keep], mapped, kin['t'], kin['speed'],
                                              np.degrees(kin['psi']), bins['up_reference'])
        smoothing = None
        if matched_smoothing:
            from forward_smoothing_diagnostic import diagnose
            smoothing = diagnose(t[keep], mapped, kin['t'], kin['speed'],
                                 np.degrees(kin['psi']), bins['up_reference'])
        uncertainty = None
        if reference_uncertainty:
            from lll.forward_reference import estimate_forward_axis as matched_reference
            ref, ref_quality = matched_reference(t[keep],mapped,kin['t'],kin['speed'],
                                                np.degrees(kin['psi']),bins['up_reference'])
            uncertainty = dict(available=ref is not None,
                               axis=None if ref is None else ref.tolist(),quality=ref_quality,
                               full_pipeline_fitted=False)
        cases.append(dict(task_index=row['task_index'], task_id=row['task_id'],
                          failure=row.get('failure'), elapsed_s=row['elapsed_s'],
                          crab_model=row['fit_options']['crab_model'],
                          magnetic_ambiguity=row['fit_options'].get('magnetic_ambiguity', 'exclude'),
                          forward_available=axis is not None, forward_quality=quality,
                          **({'matched_smoothing_diagnostic': smoothing} if matched_smoothing else {}),
                          **({'matched_reference_uncertainty':uncertainty} if reference_uncertainty else {}),
                          retained_bins=len(bins['t']),
                          orientation_unresolved_epoch=unresolved,
                          saved_session_sha256=session.sha256))
    return plain(dict(scope='saved preprocessing only; no synthesis, science fit, SVD or search',
                      campaign_sha256=hashlib.sha256(campaign_path.read_bytes()).hexdigest(),
                      execution=campaign['execution'], cases=cases))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--matched-smoothing', action='store_true',
                        help='additional diagnostic only; supplies no forward uncertainty or science acceptance')
    parser.add_argument('--reference-uncertainty',action='store_true',
                        help='opt-in provisional joint-moment covariance; no science fit')
    args = parser.parse_args()
    result = audit(args.directory,args.matched_smoothing,args.reference_uncertainty)
    with args.output.open('x') as out:
        out.write(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps(result, allow_nan=False))
