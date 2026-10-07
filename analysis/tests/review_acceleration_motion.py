# SPDX-License-Identifier: AGPL-3.0-or-later
"""Apply the research correction to saved observations; score assumed truth afterwards."""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'analysis'))

import numpy as np
import acceleration_motion as correction
from audit_replay_residuals import assumed_attitude, mean_bins, rms, saved_prediction
from lll.attitude import epoch_of
from lll.calib import RAD2DPH
from lll.format import read_session
from lll.research_design import implementation_hash
from lll.trajectory import TrackReplay


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def observed_inputs(folder):
    """No campaign design, simulator options, truth labels or prescribed motion input."""
    session = read_session(folder/'session.zip')
    analysis = json.loads((folder/'analysis.json').read_text())
    bins = dict(np.load(folder/'fit-input.npz', allow_pickle=False))
    flight = session.phase('flight')
    gnss = session.slice('gnss', flight['start_ns'], flight['end_ns'])
    accel = session.slice('accel', flight['start_ns'], flight['end_ns'])
    t, at = gnss['t_ns']/1e9, accel['t_ns']/1e9
    epochs = [dict(t0_s=-np.inf if e['t0_s'] is None else e['t0_s'],
                   t1_s=np.inf if e['t1_s'] is None else e['t1_s']) for e in analysis['mount_epochs']]
    ae = epoch_of(at, epochs)
    mapped = np.full((len(at), 3), np.nan)
    valid = ae >= 0
    raw = np.column_stack([accel[k] for k in ('x', 'y', 'z')])
    mapped[valid] = np.einsum('nij,nj->ni', bins['mount_matrices'][ae[valid]], raw[valid])
    force, sem = np.full((len(t), 3), np.nan), np.full((len(t), 3), np.nan)
    support = np.zeros(len(t), bool)
    period = np.median(np.diff(at))
    for j, (lo, hi) in enumerate(zip(np.searchsorted(at, t-.5), np.searchsorted(at, t+.5))):
        if hi-lo < correction.MOTION_POLICY['minimum_imu_coverage_fraction']/period: continue
        if np.any(~valid[lo:hi]) or np.any(np.diff(at[lo:hi]) > 3*period): continue
        force[j] = np.mean(mapped[lo:hi], axis=0)
        sem[j] = np.std(mapped[lo:hi], axis=0)/np.sqrt(hi-lo)
        support[j] = True
    accuracy = [gnss[key] for key in ('speed_acc_mps', 'bearing_acc_deg', 'v_acc_m')]
    support &= np.isfinite(np.column_stack([gnss['speed_mps'], gnss['bearing_deg'], gnss['alt_m'], *accuracy])).all(axis=1)
    support &= (gnss['speed_mps'] >= 120) & (gnss['h_acc_m'] <= 25)
    support &= np.all(np.column_stack(accuracy) >= 0, axis=1)
    return dict(t=t, force=force, sem=sem, valid=support, gnss=gnss, bins=bins,
                forward=np.asarray(analysis['forward_axis']['axis_b']),
                sigma=analysis['forward_axis']['angle_sigma_rad'])


def observed_corrections(inputs):
    """Evaluate the prespecified finite grid; simulator truth never selects a state."""
    policy = correction.MOTION_POLICY
    t, gnss, bins = inputs['t'], inputs['gnss'], inputs['bins']
    matrices = bins['mount_matrices'][bins['epoch']]
    states, motions, ups, masks, errors = [], [], [], [], []
    uncertainty = {}
    def evaluate(prepared, state, **options):
        states.append(state)
        try:
            result = correction.correct(prepared, inputs['forward'], inputs['sigma'], **options)
            motion, keep = correction.bin_average(t, result['motion'], result['valid'], bins)
            up, other = correction.bin_average(t, result['up'], result['valid'], bins)
            keep &= other
            motions.append(np.einsum('nji,nj->ni', matrices, motion))
            ups.append(np.einsum('nji,nj->ni', matrices, up))
            masks.append(keep); errors.append(None)
        except ValueError as error:
            motions.append(np.full((len(bins['t']), 3), np.nan))
            ups.append(np.full((len(bins['t']), 3), np.nan))
            masks.append(np.zeros(len(bins['t']), bool)); errors.append(str(error))
    for window in policy['windows_seconds']:
        prepared = correction.prepare(t, gnss['speed_mps'], gnss['bearing_deg'], gnss['alt_m'], inputs['force'], inputs['valid'], window)
        sigma_a, sigma_f = correction.independent_uncertainty(t, gnss['speed_mps'], gnss['bearing_deg'],
            gnss['speed_acc_mps'], gnss['bearing_acc_deg'], gnss['v_acc_m'], inputs['sem'], inputs['valid'], window)
        supported = prepared['valid'] & np.isfinite(sigma_a).all(axis=1) & np.isfinite(sigma_f).all(axis=1)
        uncertainty[str(window)] = dict(acceleration_sigma_max_mps2=np.nanmax(sigma_a[supported], axis=0).tolist(),
            force_sigma_max_mps2=np.nanmax(sigma_f[supported], axis=0).tolist(),
            interpretation='Marginal linear propagation under independent fixes/IMU samples; no temporal covariance or coverage claim')
        for crab, rate, forward in itertools.product(policy['crab_offsets_deg'], policy['crab_rates_dph'], policy['forward_sigma_multipliers']):
            state = dict(window_seconds=window, crab_deg=crab, crab_rate_dph=rate, forward_sigmas=forward, perturbation='none')
            evaluate(prepared, state, crab_deg=crab, crab_rate_dph=rate, forward_sigmas=forward)
        if window == 30.:
            # Fully correlated +/-3 marginal-sigma controls, not simulated noise draws.
            for name, scales in (('acceleration', sigma_a), ('force', sigma_f)):
                for axis, sign in itertools.product(range(3), (-1, 1)):
                    perturbed = {**prepared, 'valid':supported, name:prepared[name].copy()}
                    perturbed[name][:, axis] += sign*3*scales[:, axis]
                    state = dict(window_seconds=window, crab_deg=0., crab_rate_dph=0., forward_sigmas=0.,
                                 perturbation=name, axis=axis, sigmas=sign*3)
                    evaluate(perturbed, state)
    nominal = next(i for i, s in enumerate(states) if s == dict(window_seconds=30., crab_deg=0., crab_rate_dph=0., forward_sigmas=0., perturbation='none'))
    return dict(states=states, motion=np.array(motions), up=np.array(ups), valid=np.array(masks),
                errors=errors, nominal=nominal, uncertainty=uncertainty)


def review(directory, output):
    campaign_path = directory/'campaign.json'
    campaign = json.loads(campaign_path.read_text())
    if not campaign['execution']['complete'] or implementation_hash() != campaign['implementation_hash']:
        raise ValueError('completed frozen replay with unchanged scientific implementation required')
    output.mkdir(exist_ok=False)
    cases, groups, sources = [], {}, {str(campaign_path.relative_to(ROOT)):sha(campaign_path)}
    for row in campaign['records']:
        folder = directory/'diagnostics'/row['task_id']
        for name in ('session.zip', 'fit-input.npz', 'fit-rows.npz', 'turn-input.npz', 'analysis.json'):
            path = folder/name; sources[str(path.relative_to(ROOT))] = sha(path)
        key = (sha(folder/'session.zip'), sha(folder/'fit-input.npz'))
        if key not in groups:
            inputs = observed_inputs(folder)
            result = observed_corrections(inputs)
            name = 'observed-input-'+str(len(groups))
            archive = output/(name+'.npz')
            np.savez_compressed(archive, motion=result['motion'], up=result['up'], valid=result['valid'])
            groups[key] = dict(inputs=inputs, result=result, name=name, archive=archive)
        group = groups[key]
        bins, result = group['inputs']['bins'], group['result']
        analysis = json.loads((folder/'analysis.json').read_text())
        saved = dict(np.load(folder/'fit-rows.npz', allow_pickle=False))
        residual, _, _, fitted_crab, _, _ = saved_prediction(row, analysis, bins, saved)
        base = np.cross(bins['dup_dt'], bins['up'])-bins['psi_dot'][:, None]*bins['up']
        # Truth enters only this posthoc scoring block, after all observed corrections exist.
        session = read_session(folder/'session.zip')
        start = session.phase('flight')['start_ns']/1e9
        times = np.load(folder/'turn-input.npz', allow_pickle=False)['t']
        options = row['design']['simulator']
        elapsed = np.rint((times-start)*options['fs'])/options['fs']
        replay = TrackReplay(options['trajectory_input'])
        C, _, _, _ = assumed_attitude(options, replay, elapsed, start)
        Cnext, _, _, _ = assumed_attitude(options, replay, elapsed+1/options['fs'], start)
        relative = np.swapaxes(C, 1, 2)@Cnext
        angular = np.column_stack([relative[:, 2, 1]-relative[:, 1, 2], relative[:, 0, 2]-relative[:, 2, 0],
                                   relative[:, 1, 0]-relative[:, 0, 1]])*options['fs']/2
        assumed, _ = mean_bins(angular, times, bins)
        common = np.all(result['valid'], axis=0)
        nominal = result['nominal']
        selected = result['valid'][nominal]
        metrics = []
        for i, state in enumerate(result['states']):
            metrics.append(dict(state=state, error=result['errors'][i], supported_bins=int(result['valid'][i].sum()),
                common_bin_motion_error_dph=rms((assumed-result['motion'][i]-fitted_crab)[common])['total_dph'] if common.any() else None,
                common_bin_fixed_prediction_residual_dph=rms((residual+base-result['motion'][i])[common])['total_dph'] if common.any() else None))
        cases.append(dict(task_id=row['task_id'], truth=row['truth'], crab_model=row['fit_options']['crab_model'],
            observed_group=group['name'], input_bins=len(bins['t']), nominal_supported_bins=int(selected.sum()), common_supported_bins=int(common.sum()),
            state_count=len(metrics), failed_states=sum(e is not None for e in result['errors']),
            baseline_residual_same_nominal_bins=rms(residual[selected]),
            nominal_fixed_prediction_residual=rms((residual+base-result['motion'][nominal])[selected]),
            baseline_motion_error_same_nominal_bins=rms((assumed-base-fitted_crab)[selected]),
            nominal_motion_error=rms((assumed-result['motion'][nominal]-fitted_crab)[selected]),
            gps_and_force_uncertainty=result['uncertainty'], states=metrics))
    helpers = {str(p.relative_to(ROOT)):sha(p) for p in (Path(__file__), Path(correction.__file__))}
    report = dict(scope='Observed-data research correction and separate posthoc prescribed-motion scoring; no new flights, fits or decisions',
        provenance=correction.provenance(), scientific_implementation_hash=campaign['implementation_hash'],
        additional_flight_attempts=0, optimizer_calls=0, input_sha256=sources, helper_sha256=helpers,
        observed_groups=len(groups), cases=cases,
        archives={str(g['archive'].relative_to(ROOT)):sha(g['archive']) for g in groups.values()},
        limitations=['Finite sensitivity states are not a confidence region or validated coverage.',
            'Reported GPS and sample SEM propagation assumes independent errors; correlated GPS/IMU and sensor offset/scale systematics remain open.',
            'Wind/crab range is a provisional angle/rate sensitivity grid, not the full fitted wind/TAS model or envelope.',
            'Local velocity derivatives omit model-dependent Coriolis/curvature accelerations; those require systematic bounds.',
            'Matched filtering changes motion bandwidth; unsupported bins are retained as exclusions and all states use a common-bin comparison.',
            'Saved science/bias/crab coefficients remain fixed; replacing motion alone is not a refit, calibration or power result.',
            'True motion is used only for posthoc scoring, never to compute or select an observed correction.'])
    (output/'review.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
    print(json.dumps([{k:c[k] for k in ('truth','crab_model','nominal_supported_bins','common_supported_bins','failed_states',
        'baseline_residual_same_nominal_bins','nominal_fixed_prediction_residual','nominal_motion_error')} for c in cases]))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    review(args.directory.resolve(), args.output.resolve())
