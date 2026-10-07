# SPDX-License-Identifier: AGPL-3.0-or-later
"""Decompose saved replay residuals using its assumed motion; never synthesize or fit."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'analysis'))

import numpy as np
from scipy.spatial.transform import Rotation
from lll import models
from lll.calib import RAD2DPH
from lll.format import read_session
from lll.inference import CandidateProblem
from lll.inference_policy import INFERENCE_POLICY
from lll.research_design import implementation_hash
from lll.trajectory import TrackReplay

TRAY = np.array([[0., 1., 0.], [1., 0., 0.], [0., 0., -1.]])


def assumed_attitude(options, replay, elapsed, flight_start):
    """Independent SciPy composition of the frozen replay's prescribed attitude."""
    path = replay.sample(elapsed)
    wind = np.asarray(options['wind_ne_mps']) + elapsed[:, None]/3600*np.asarray(options['wind_rate_ne_mps_per_h'])
    air = np.column_stack([path['v_n'], path['v_e']]) - wind
    heading = np.arctan2(air[:, 1], air[:, 0])
    bank = np.arctan(path['speed']*path['psi_dot']/models.G0)
    pitch = np.radians(2 + options['pitch_trim_deg_per_h']*elapsed/3600)
    # The simulator's phase time has a fixed 1000-second elapsed-clock origin.
    pitch += np.radians(.1)*np.sin(2*np.pi*(flight_start-1000+elapsed)/400)
    mount = Rotation.from_euler('ZY', [options['mount_yaw_deg'], options['mount_tilt_deg']], degrees=True).as_matrix() @ TRAY
    yaw = np.zeros(len(elapsed))
    for minute, axis in options['index_turns']:
        if axis != 'z':
            raise ValueError('this audit supports the saved tray yaw turns only')
        yaw += np.pi*np.clip((elapsed-minute*60)/options['turn_seconds'], 0, 1)
    turn = Rotation.from_euler('Z', yaw[:, None]).as_matrix()
    aircraft = Rotation.from_euler('ZYX', np.column_stack([heading, pitch, bank])).as_matrix()
    return aircraft @ mount @ turn, path, bank, mount @ turn


def mean_bins(values, times, bins):
    lo = np.searchsorted(times, bins['t']-bins['dt']/2)
    hi = np.searchsorted(times, bins['t']+bins['dt']/2)
    if np.any(hi <= lo):
        raise ValueError('empty saved bin')
    cumulative = np.concatenate([np.zeros_like(values[:1]), np.cumsum(values, axis=0)])
    result = (cumulative[hi]-cumulative[lo])/(hi-lo).reshape((-1,) + (1,)*(values.ndim-1))
    return result, hi-lo


def rms(values):
    return dict(total_dph=float(np.sqrt(np.mean(values**2))*RAD2DPH),
                axes_dph=(np.sqrt(np.mean(values**2, axis=0))*RAD2DPH).tolist())


def segment_gradient(values, bins):
    result = np.zeros_like(values)
    for segment in np.unique(bins['seg']):
        mask = bins['seg'] == segment
        if mask.sum() >= 2:
            result[mask] = np.gradient(values[mask], bins['t'][mask], axis=0)
    return result


def unit(values):
    return values/np.linalg.norm(values, axis=-1, keepdims=True)


def saved_prediction(row, analysis, bins, saved):
    """Reconstruct the saved free prediction, with no optimizer call."""
    cal = analysis['calibration']
    b0, b1 = (np.asarray(cal[k]['bias_dph'])/RAD2DPH for k in ('pre', 'post'))
    t0, t1 = (cal[k]['t_mid_s'] for k in ('pre', 'post'))
    def bias(t):
        return b0 + np.clip((np.asarray(t)-t0)/(t1-t0), 0, 1)[..., None]*(b1-b0)
    settings = dict(row['fit_options'])
    for key in ('bias_knot_seconds', 'bias_rw_sigma_dph_sqrth', 'crab_rate_sigma_dph'):
        if settings.get(key) is None:
            settings[key] = INFERENCE_POLICY[key]
    if settings.get('crab_knot_seconds') is None:
        settings['crab_knot_seconds'] = INFERENCE_POLICY['wind_knot_seconds']
    if settings['crab_model'] == 'wind_tas':
        from lll.wind_tas import WIND_TAS_POLICY
        settings['wind_tas_policy'] = dict(WIND_TAS_POLICY)
    up = bins['up_reference']/np.linalg.norm(bins['up_reference'])
    fwd0 = np.asarray(analysis['forward_axis']['axis_b'])
    tangent = np.einsum('nji,j->ni', bins['mount_matrices'][bins['epoch']], np.cross(up, fwd0))
    problem = CandidateProblem(bins, bins['forward'], bias,
        np.asarray(analysis['bias_model']['prior_sigma_dph'])/RAD2DPH, settings,
        forward_sigma_rad=analysis['forward_axis']['angle_sigma_rad'], forward_tangent=tangent)
    if not np.allclose(problem.y, saved['y'], rtol=0, atol=1e-14):
        raise ValueError('saved observation reconstruction differs')
    z = saved['parameters']
    prediction, jacobian = problem.prediction(z, True)
    if not np.allclose(jacobian, saved['jacobian'], rtol=1e-7, atol=1e-12):
        raise ValueError('saved Jacobian reconstruction differs')
    science_z = z.copy()
    science_z[:problem.p] = 0
    science_z[:3] = z[:3]
    nuisance_z = science_z.copy()
    nuisance_z[:3] = 0
    motion = problem.prediction(nuisance_z).reshape(-1, 3)
    science = (problem.prediction(science_z)-problem.prediction(nuisance_z)).reshape(-1, 3)
    bias_prediction = prediction.reshape(-1, 3)-motion-science
    return problem.y.reshape(-1, 3)-prediction.reshape(-1, 3), science, bias_prediction, motion, bias, z[-1]


def audit(directory):
    source = directory/'campaign.json'
    campaign = json.loads(source.read_text())
    if not campaign['execution']['complete'] or implementation_hash() != campaign['implementation_hash']:
        raise ValueError('requires completed replay and its unchanged scientific source')
    cases, inputs = [], {str(source.relative_to(ROOT)): hashlib.sha256(source.read_bytes()).hexdigest()}
    for row in campaign['records']:
        folder = directory/'diagnostics'/row['task_id']
        for name in ('session.zip', 'turn-input.npz', 'fit-input.npz', 'fit-rows.npz', 'analysis.json'):
            path = folder/name
            inputs[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
        analysis = json.loads((folder/'analysis.json').read_text())
        bins = dict(np.load(folder/'fit-input.npz', allow_pickle=False))
        saved = dict(np.load(folder/'fit-rows.npz', allow_pickle=False))
        options = row['design']['simulator']
        if options['mount'] != 'tray' or any(options['mount_slip_deg_per_h']) or options['turbulence'] or options['crab_deg']:
            raise ValueError('unsupported assumed attitude')
        crab = row['design']['crab_trajectory']
        if any(crab.get(k, 0) for k in ('offset_deg', 'rate_dph', 'amplitude_deg')):
            raise ValueError('unsupported additional crab trajectory')
        session = read_session(folder/'session.zip')
        start = session.phase('flight')['start_ns']/1e9
        times = np.load(folder/'turn-input.npz', allow_pickle=False)['t']
        elapsed = np.rint((times-start)*options['fs'])/options['fs']
        replay = TrackReplay(options['trajectory_input'])
        dt = 1/options['fs']
        C, path, bank, mount = assumed_attitude(options, replay, elapsed, start)
        Cnext, _, _, _ = assumed_attitude(options, replay, elapsed+dt, start)
        relative = np.swapaxes(C, 1, 2) @ Cnext
        # Match the saved simulator's finite-step sin(angle)/dt angular rate.
        angular = np.column_stack([relative[:, 2, 1]-relative[:, 1, 2],
                                   relative[:, 0, 2]-relative[:, 2, 0],
                                   relative[:, 1, 0]-relative[:, 0, 1]])/(2*dt)
        assumed_motion, counts = mean_bins(angular, times, bins)
        inertial = models.predict(row['truth'], path['lat'], path['h'], path['v_n'], path['v_e'])
        science, _ = mean_bins(np.einsum('nji,nj->ni', C, inertial), times, bins)
        # Known coordinated bank contribution to the gyro, independent of recovered axes.
        _, _, next_bank, _ = assumed_attitude(options, replay, elapsed+dt, start)
        roll_rate = np.column_stack([(next_bank-bank)/dt, np.zeros((len(times), 2))])
        roll, _ = mean_bins(np.einsum('nji,nj->ni', mount, roll_rate), times, bins)
        true_up, _ = mean_bins(-C[:, 2, :], times, bins)
        true_up = unit(true_up)
        acceleration = np.column_stack([np.gradient(path['v_n'], elapsed), np.gradient(path['v_e'], elapsed),
                                        np.gradient(-path['vz'], elapsed)])
        acceleration[:, 2] -= models.G0
        specific, _ = mean_bins(np.einsum('nji,nj->ni', C, acceleration), times, bins)
        specific_up = unit(specific)
        true_tilt_rate = np.cross(segment_gradient(true_up, bins), true_up)
        specific_tilt_rate = np.cross(segment_gradient(specific_up, bins), specific_up)
        observed_tilt_rate = np.cross(bins['dup_dt'], bins['up'])
        apparent_tilt_artifact = observed_tilt_rate-true_tilt_rate
        true_plumb_motion = true_tilt_rate-bins['psi_dot'][:, None]*true_up
        base_motion = np.cross(bins['dup_dt'], bins['up'])-bins['psi_dot'][:, None]*bins['up']
        residual, fitted_science, fitted_bias, fitted_motion, calibration, forward_angle = saved_prediction(row, analysis, bins, saved)
        sensor = bins['gyro']-calibration(bins['t'])-assumed_motion-science
        motion_error = assumed_motion-base_motion-fitted_motion
        science_error = science-fitted_science
        sensor_error = sensor-fitted_bias
        components = np.stack([motion_error, science_error, sensor_error])
        closure = float(np.max(np.abs(components.sum(axis=0)-residual))*RAD2DPH)
        if closure > 1e-7:
            raise ValueError('residual decomposition does not close')
        expected_white = options['noise_dps_rthz']*3600*np.sqrt(options['fs']/counts)
        # Quantization estimate assumes independent uniform rounding; not a guaranteed floor.
        quantization = options['gyro_range_dps']/32768*3600/np.sqrt(12*counts)
        axis = bins['up']/np.linalg.norm(bins['up'], axis=1)[:, None]
        aligned = np.sum(residual*axis, axis=1)
        horizontal = residual-aligned[:, None]*axis
        motion_without_roll = motion_error-roll
        apparent_model_artifact = base_motion-true_plumb_motion
        plumb_corrected_motion_error = assumed_motion-true_plumb_motion-fitted_motion
        cases.append(dict(task_index=row['task_index'], truth=row['truth'], crab_model=row['fit_options']['crab_model'],
            frozen_preliminary_sigma_dph=analysis['fit']['noise']['global_sigma_dph'],
            final_free_residual=rms(residual), final_horizontal_residual=rms(horizontal),
            final_vertical_residual_rms_dph=float(np.sqrt(np.mean(aligned**2))*RAD2DPH),
            expected_white_bin_sigma_range_dph=[float(expected_white.min()), float(expected_white.max())],
            independent_rounding_sigma_range_dph=[float(quantization.min()), float(quantization.max())],
            observed_bin_sem_rms_dph=(np.sqrt(np.mean(bins['gyro_sem']**2, axis=0))*RAD2DPH).tolist(),
            sensor_and_calibration_error=rms(sensor), sensor_after_fitted_bias=rms(sensor_error),
            aircraft_motion_mismatch=rms(motion_error), assumed_roll_contribution=rms(roll),
            aircraft_motion_mismatch_after_removing_assumed_roll=rms(motion_without_roll),
            apparent_tilt_artifact=rms(apparent_tilt_artifact),
            assumed_specific_force_tilt_artifact=rms(specific_tilt_rate-true_tilt_rate),
            observed_vs_assumed_specific_force_direction_max_deg=float(np.degrees(np.max(
                np.arccos(np.clip(np.sum(unit(bins['up'])*specific_up, axis=1), -1, 1))))),
            apparent_vs_true_up_angle_max_deg=float(np.degrees(np.max(
                np.arccos(np.clip(np.sum(unit(bins['up'])*true_up, axis=1), -1, 1))))),
            aircraft_motion_mismatch_using_true_plumb=rms(plumb_corrected_motion_error),
            diagnostic_residual_using_true_plumb=rms(residual+apparent_model_artifact),
            science_orientation_mismatch=rms(science_error),
            component_second_moment_dph2=(np.einsum('ani,bni->ab', components, components)/residual.size*RAD2DPH**2).tolist(),
            decomposition_max_error_dph=closure, fitted_forward_angle_deg=float(np.degrees(forward_angle))))
    return dict(scope='saved-data decomposition against prescribed replay attitude; no synthesis, optimizer, bootstrap or new flights',
        implementation_hash=campaign['implementation_hash'], input_sha256=inputs,
        helper_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), additional_flight_attempts=0,
        cases=cases, limitations=[
            'Assumed trajectory, coordinated bank, pitch and wind are simulator states, unavailable as real measurement truth.',
            'Residual weights are frozen from the preliminary fit; final residual RMS may differ.',
            'Components are correlated: their squared RMS values must not be added as independent variances.',
            'Sensor remainder includes quantization, white noise, drift and calibration error; these are not separately identified.',
            'Independent uniform quantization estimate is descriptive, not guaranteed under correlated rounding.',
            'One shared seed; no power, coverage, eligibility revision or calibrated decision claim.'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.directory.resolve())
    with args.output.open('x') as out:
        out.write(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print(json.dumps([dict(truth=c['truth'], crab=c['crab_model'], residual=c['final_free_residual']['total_dph'],
        motion=c['aircraft_motion_mismatch']['total_dph'], roll=c['assumed_roll_contribution']['total_dph'],
        motion_without_roll=c['aircraft_motion_mismatch_after_removing_assumed_roll']['total_dph'],
        sensor=c['sensor_after_fitted_bias']['total_dph'], science=c['science_orientation_mismatch']['total_dph']) for c in result['cases']]))
