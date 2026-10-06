# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved protocol diagnostics and independent attitude fixtures; no flights or fits."""
import argparse
from collections import defaultdict
import gzip
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from scipy.spatial.transform import Rotation

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT/'analysis'), str(ROOT/'server')]
from lll.attitude import c_bn, epoch_of, estimate_forward_axis, mount_epochs, turn_rotation
from lll.inference_policy import digest
from lll.inference import CandidateProblem, science_information
from lll.calib import RAD2DPH
from lll import models
from lll.research_design import implementation_hash, plain
from lll.runtime import numerical_environment


def mounted_axes(yaw=20., tilt=4.):
    """Independent IMU-to-aircraft matrix: +y forward, +z up before mount offsets."""
    tray = np.array([[0., 1., 0.], [1., 0., 0.], [0., 0., -1.]])
    return Rotation.from_euler('ZY', [yaw, tilt], degrees=True).as_matrix() @ tray


def plane_error(axis, reference, up):
    def horizontal(v):
        v = np.asarray(v) - np.dot(v, up)*up
        return v/np.linalg.norm(v)
    a, b = horizontal(axis), horizontal(reference)
    return float(np.degrees(np.arctan2(np.dot(up, np.cross(b, a)), np.dot(b, a))))


def contrast_stages(design):
    """Compare retained information with the same frozen cutoff before truncation."""
    cutoff = design['rank_threshold']
    values = [c for a in design['anchors'].values()
              for c in a['model_contrast_information'].values()]
    before = min(c['pre_cutoff_retained_fraction'] for c in values)
    after = min(c['retained_fraction'] for c in values)
    return dict(pre_cutoff_min_retention=before, retained_min_retention=after,
                before_pass=before >= cutoff, after_pass=after >= cutoff,
                cutoff_only_failure=before >= cutoff and after < cutoff)


def aircraft_turn_intervals(legs):
    """Existing simulator's documented 3 deg/s turns, five-second ramps, initial five minutes."""
    start = 300.
    out = []
    for (a, duration), (b, _) in zip(legs[:-1], legs[1:]):
        start += duration*60.
        change = (b-a+180.) % 360.-180.
        end = start+abs(change)/3.+5.
        out.append(dict(start_s=start, end_s=end, change_deg=change))
        start = end
    return out


def schedule_overlaps(simulator):
    out = []
    intervals = aircraft_turn_intervals(simulator['legs'])
    for minute, axis in simulator['index_turns']:
        start, end = minute*60., minute*60.+simulator['turn_seconds']
        for turn in intervals:
            if max(start-1., turn['start_s']) < min(end+1., turn['end_s']):
                out.append(dict(imu_turn_min=minute, axis=axis, aircraft_turn=turn,
                                integration_padding_s=1.))
    return out


def timing_tangents(simulator, shifted=False):
    """Known-axis coarse geometry with the existing aircraft-turn timeline.

    Sharp endpoint headings and approximate spherical latitude, excluding aircraft
    maneuvers with 15-second padding. These are analytic bins, not production cruise
    qualification or historical bin reconstruction. No solve is performed.
    """
    duration = sum(minutes for _, minutes in simulator['legs'])*60.+600.
    t = np.arange(30., duration, 60.)
    aircraft = aircraft_turn_intervals(simulator['legs'])
    keep = np.ones(len(t), dtype=bool)
    for turn in aircraft:
        keep &= ~((t >= turn['start_s']-15.) & (t <= turn['end_s']+15.))
    t = t[keep]
    groups = np.searchsorted([a['end_s'] for a in aircraft], t)
    psi = np.radians(np.array([leg[0] for leg in simulator['legs']])[groups])
    turns = [5., 25., 40., 55., 70., 80.] if shifted else [v[0] for v in simulator['index_turns']]
    hand_count = np.searchsorted(np.asarray(turns)*60.+simulator['turn_seconds'], t)
    mount = mounted_axes(simulator['mount_yaw_deg'], simulator['mount_tilt_deg'])
    hand = Rotation.from_euler('Z', (hand_count*np.pi)[:, None]).as_matrix()
    mount_frames = mount @ hand
    fwd = np.einsum('nji,j->ni', mount_frames, [1., 0., 0.])
    up = np.einsum('nji,j->ni', mount_frames, [0., 0., -1.])
    speed, radius = simulator['speed'], 6371000.+simulator['h']
    vn, ve = speed*np.cos(psi), speed*np.sin(psi)
    # Integrate on the complete one-minute grid, retaining heading at sharp turn endpoints.
    all_t = np.arange(30., duration, 60.)
    all_groups = np.searchsorted([a['end_s'] for a in aircraft], all_t)
    all_psi = np.radians(np.array([leg[0] for leg in simulator['legs']])[all_groups])
    lat = (np.radians(simulator['lat0'])+np.cumsum(speed*np.cos(all_psi))*60./radius)[keep]
    bins = dict(t=t, dt=np.full(len(t), 60.), seg=groups+hand_count*len(simulator['legs']),
        psi=psi, lat=lat, h=np.full(len(t), simulator['h']), v_n=vn, v_e=ve,
        lon_rate=ve/(radius*np.cos(lat)), up=up, dup_dt=np.zeros((len(t), 3)),
        psi_dot=np.zeros(len(t)), gyro=np.zeros((len(t), 3)))
    results = []
    for crab in ('dynamic', 'wind'):
        settings = dict(crab_model=crab, crab_knot_seconds=300., crab_rate_sigma_dph=1.,
            bias_model='dynamic', bias_knot_seconds=900., bias_rw_sigma_dph_sqrth=3.,
            forward_uncertainty=True)
        problem = CandidateProblem(bins, fwd, lambda _: 0., np.full(3, 2/RAD2DPH), settings,
                                   forward_sigma_rad=.02)
        for anchor, coefficients in models.EXPECTED_K.items():
            z = np.zeros(problem.npar)
            z[:3] = coefficients
            _, jacobian = problem.prediction(z, True)
            report = science_information(jacobian, problem.w)['report']
            contrasts = report['model_contrast_information']
            results.append(dict(crab_model=crab, anchor=anchor,
                rank=report['estimable_rank'], all_estimable=all(c['estimable'] for c in contrasts.values()),
                worst_retained_fraction=min(c['retained_fraction'] for c in contrasts.values()),
                worst_pre_cutoff_retained_fraction=min(c['pre_cutoff_retained_fraction'] for c in contrasts.values())))
    return dict(turn_schedule_min=turns, bins=len(t), tangent_results=results,
                limitations='Known axes; sharp headings, approximate spherical latitude and coarse maneuver mask; no production qualification, noise, watchdog, calibration or fits.')


def orientation_fixture():
    errors = []
    for yaw, tilt, heading, hand in [(20., 4., 10., 0.), (-35., 12., 190., 180.),
                                      (65., -8., 280., 180.)]:
        mount = mounted_axes(yaw, tilt) @ Rotation.from_euler('Z', hand, degrees=True).as_matrix()
        expected = (Rotation.from_euler('Z', heading, degrees=True).as_matrix() @ mount).T
        up, forward = mount.T @ [0., 0., -1.], mount.T @ [1., 0., 0.]
        measured = c_bn(up, forward, np.radians(heading))
        errors.append(float(np.max(np.abs(measured-expected))))
    return dict(cases=len(errors), max_matrix_error=max(errors),
                independent_reference='SciPy rotations and explicit frame composition')


def turn_fixture(aircraft_rate_dps=0.):
    """Known 180-degree hand turn; aircraft yaw is independent of the mount change."""
    t = np.arange(0., 80., .05)
    gyro = np.zeros((len(t), 3))
    gyro[(t >= 20.) & (t < 24.), 2] = np.radians(45.)
    gyro[(t >= 20.) & (t < 60.), 2] += np.radians(aircraft_rate_dps)
    matrix, info = turn_rotation(t, gyro, 39., expected_period=.05)
    expected = Rotation.from_euler('Z', 180., degrees=True).as_matrix()
    error = Rotation.from_matrix(expected.T @ matrix).magnitude()
    return dict(aircraft_rate_dps=aircraft_rate_dps, known_mount_turn_deg=180.,
                recovered_angle_deg=info['angle_deg'], mount_rotation_error_deg=float(np.degrees(error)),
                flagged_unresolved=bool(info.get('unresolved_gap')), integration=info)


def forward_fixture(hand_start=None):
    """Small noiseless coordinated maneuver; not a synthesized flight or campaign draw.

    Generate body gyro using SciPy's rotation logarithm from independently composed
    known frames. No calibration, sensor encoding, cruise fitting or Earth-model solve.
    """
    dt = .05
    t = np.arange(0., 220., dt)
    # Smooth roll into a bank at 60--70 s and out at 130--140 s.
    bank = np.radians(15.)*(np.clip((t-60.)/10., 0., 1.)-np.clip((t-130.)/10., 0., 1.))
    speed, gravity = 270., 9.80665
    yaw_rate = gravity*np.tan(bank)/speed
    heading = np.radians(10.)+np.cumsum(yaw_rate)*dt
    hand = np.zeros_like(t) if hand_start is None else np.pi*np.clip((t-hand_start)/4., 0., 1.)
    mount = mounted_axes()
    aircraft = Rotation.from_euler('ZYX', np.column_stack([heading, np.zeros(len(t)), bank])).as_matrix()
    hand_frames = Rotation.from_euler('Z', hand[:, None]).as_matrix()
    frames = aircraft @ mount @ hand_frames
    relative = np.swapaxes(frames[:-1], 1, 2) @ frames[1:]
    gyro = Rotation.from_matrix(relative).as_rotvec()/dt
    gyro = np.vstack([gyro, gyro[-1]])
    events = [] if hand_start is None else [(hand_start+19., 'index_turn')]
    epochs, _ = mount_epochs(t, gyro, events, expected_period=dt)
    ei = epoch_of(t, epochs)
    ok = ei >= 0
    maps = np.array([e['R0'] for e in epochs])
    mapped = np.einsum('nij,nj->ni', maps[ei[ok]], gyro[ok])
    gt = np.arange(1., 219., 1.)
    bearing = np.degrees(np.interp(gt, t, heading))
    up, known = mount.T @ [0., 0., -1.], mount.T @ [1., 0., 0.]
    estimated, quality = estimate_forward_axis(t[ok], mapped, gt, np.full(len(gt), speed), bearing, up)
    epoch_error = None
    if events:
        hand_only = Rotation.from_euler('Z', 180., degrees=True).as_matrix()
        epoch_error = float(np.degrees(Rotation.from_matrix(hand_only.T @ maps[-1]).magnitude()))
    return dict(hand_start_s=hand_start, forward_available=estimated is not None,
                horizontal_axis_error_deg=None if estimated is None else plane_error(estimated, known, up),
                mount_mapping_error_deg=epoch_error, quality=quality,
                mount_turn=epochs[-1]['turn'])


def audit(directory):
    manifest = json.loads((directory/'manifest.json').read_text())
    if digest({k: v for k, v in manifest.items() if k != 'manifest_hash'}) != manifest['manifest_hash']:
        raise ValueError('invalid historical manifest hash')
    archive = directory/'records.jsonl.gz'
    rows = [json.loads(line) for line in gzip.decompress(archive.read_bytes()).splitlines()]
    if ([r['case'] for r in rows] != manifest['config']['cases'] or
            any(r['manifest_hash'] != manifest['manifest_hash'] for r in rows)):
        raise ValueError('historical task/provenance mismatch')
    groups, cases = defaultdict(list), []
    for row in rows:
        r, case = row['result'], row['case']
        stages = contrast_stages(r['design_identifiability'])
        sim = r['design']['simulator']
        mount = mounted_axes(sim['mount_yaw_deg'], sim['mount_tilt_deg'])
        if sim['mount'] != 'tray':
            raise ValueError('nominal-axis review currently supports the frozen tray mount only')
        known, up = mount.T @ [1., 0., 0.], mount.T @ [0., 0., -1.]
        forward = r['forward_axis']
        entry = dict(case=case, **stages,
            nominal_horizontal_forward_error_deg=plane_error(forward['axis_b'], known, up),
            forward_sigma_deg=float(np.degrees(forward['angle_sigma_rad'])), forward_r2=forward['r2'],
            pre_watchdog_bins=r['slip']['pre_exclusion_geometry']['n_bins'],
            watchdog_excluded_segments=r['slip']['exclude_segments'],
            retained_heading_groups=len(r['heading_diversity']['groups']),
            turn_overlaps=schedule_overlaps(sim))
        cases.append(entry)
        groups[(case['cell_id'], case['crab_model'])].append(entry)
    grouped = []
    for (protocol, crab), entries in groups.items():
        def bounds(key):
            values = [v[key] for v in entries]
            return [min(values), max(values)]
        grouped.append(dict(protocol=protocol, crab_model=crab, evaluations=len(entries),
            before_cutoff_pass=sum(e['before_pass'] for e in entries),
            after_cutoff_pass=sum(e['after_pass'] for e in entries),
            cutoff_only_failures=sum(e['cutoff_only_failure'] for e in entries),
            pre_cutoff_min_retention_range=bounds('pre_cutoff_min_retention'),
            retained_min_retention_range=bounds('retained_min_retention'),
            nominal_horizontal_forward_error_deg_range=bounds('nominal_horizontal_forward_error_deg'),
            forward_sigma_deg_range=bounds('forward_sigma_deg'), forward_r2_range=bounds('forward_r2'),
            pre_watchdog_bins=sorted({e['pre_watchdog_bins'] for e in entries}),
            watchdog_excluded_cases=sum(bool(e['watchdog_excluded_segments']) for e in entries)))
    simulator_by_protocol = {row['case']['cell_id']: row['result']['design']['simulator'] for row in rows}
    revised = simulator_by_protocol['repeated-opposing-directions-90min']
    shifted = dict(revised, index_turns=[[minute, 'z'] for minute in [5., 25., 40., 55., 70., 80.]])
    return plain(dict(partition='development', mode='saved diagnostics and independent attitude fixtures; no flights or fits',
        historical_manifest_hash=manifest['manifest_hash'],
        historical_implementation_hash=manifest['implementation_hash'],
        source_archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),
        audit_implementation_hash=implementation_hash(), audit_environment=numerical_environment(),
        audit_script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        groups=grouped, cases=cases,
        orientation_fixture=orientation_fixture(),
        isolated_turn_fixtures=[turn_fixture(rate) for rate in (0., -3., 3.)],
        coordinated_forward_fixtures=[forward_fixture(start) for start in (None, 20., 60.)],
        known_axis_timing_tangents={name: timing_tangents(sim) for name, sim in simulator_by_protocol.items()},
        timing_only_proposal=dict(state='unrun proposal; not optimized or scientifically approved',
            turn_schedule_min=[v[0] for v in shifted['index_turns']],
            known_aircraft_turn_overlaps=schedule_overlaps(shifted),
            known_axis_tangents=timing_tangents(revised, shifted=True)),
        limitations=['Saved summaries omit raw gyro/bins and mount matrices; exact historical reconstruction is unavailable.',
                    'Nominal mount-axis comparisons omit pitch/bank averaging and accumulated mapping errors; they are diagnostic, not certified uncertainty coverage.',
                    'Component fixtures isolate a mechanism, not its causal contribution in any historical campaign case.',
                    'No gate, cutoff, source-selection rule or calibration threshold is changed.']))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--campaign', type=Path, default=ROOT/'docs/protocol-development-20261006')
    parser.add_argument('--output', type=Path, default=ROOT/'docs/protocol-development-20261006/processing-audit.json')
    args = parser.parse_args()
    report = audit(args.campaign)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
    print(json.dumps({k: report[k] for k in ('groups', 'orientation_fixture',
        'isolated_turn_fixtures', 'known_axis_timing_tangents', 'timing_only_proposal')}, indent=2))


if __name__ == '__main__':
    main()
