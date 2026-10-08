# SPDX-License-Identifier: AGPL-3.0-or-later
"""Archival increment adapter and conditional geometry diagnostics; no Earth fits.

Group-1 attitude/rates are deliberately absent from this observation model.
Conversion hypotheses and ground-track orientation are never scientific eligibility.
"""
import argparse
from collections import Counter
import datetime
import fcntl
import gzip
import json
import os
from pathlib import Path
import platform

import numpy as np

from . import applanix as ap, ilvis0 as il, ilvis0_followup as follow
from . import ilvis0_installation as installation, ilvis0_motion_diagnosis as motion
from . import models

VERSION = 'ilvis0-archival-observation-v1'
POLICY = dict(version=VERSION, maximum_files=6, block_seconds=1,
              minimum_samples_per_block=190, maximum_imu_gap_s=.0075,
              minimum_block_span_s=.94, maximum_gps_distance_s=.51,
              maximum_gps_gap_s=2, coordinate_slope_span_s=2,
              attitude_envelope_deg=[-5, 0, 5], crab_envelope_deg=[-15, 0, 15],
              nuisance_svd_relative_cutoff=1e-10,
              scientific_eligible=False, earth_model_fits_enabled=False)


class IncrementBlocks:
    """Integer sums of increments, not net finite rotations or coning corrections."""
    def __init__(self, leap):
        self.leap, self.previous, self.current = leap, None, None
        self.blocks = []

    def feed(self, row, setting):
        time = follow.utc_tag(row, self.leap)
        if self.previous is not None:
            if row['time_types'] != self.previous['time_types']:
                raise ValueError('IMU time basis changed')
            dt = time - follow.utc_tag(self.previous, self.leap)
            if dt <= 0:
                raise ValueError('non-increasing IMU timestamps')
        else:
            dt = None
        if row['imu_type'] != 6 or row['rate_code'] != 2:
            raise ValueError('adapter requires the frozen IMU6/200Hz configuration')
        second = int(np.floor(time))
        if self.current is None or self.current['utc_second'] != second:
            self.finish()
            self.current = dict(utc_second=second, first_time_s=time, last_time_s=time,
                first_packet_offset=row['packet_offset'], last_packet_offset=row['packet_offset'],
                samples=0, raw_increment_sums=[0]*6, header_interval_sum_s=0.,
                flags=set(), installation_signature=None, imu_to_aircraft_rotation=None)
        block = self.current
        if dt is None:
            block['flags'].add('first_increment_interval_unknown')
        elif dt > POLICY['maximum_imu_gap_s'] or dt < .0025:
            block['flags'].add('unsupported_increment_interval')
        else:
            block['header_interval_sum_s'] += dt
        if row['data_status'] or row['imu_status']:
            block['flags'].add('raw_status_requires_interpretation')
        if setting is None or not setting['usable']:
            block['flags'].add('recorded_installation_unavailable')
        else:
            signature = setting['signature']
            if block['installation_signature'] not in (None, signature):
                block['flags'].add('installation_change_inside_block')
            block['installation_signature'] = signature
            block['imu_to_aircraft_rotation'] = setting['imu_to_aircraft_rotation']
        block['samples'] += 1
        for j, field in enumerate(ap.RAW_FIELDS):
            block['raw_increment_sums'][j] += int(row[field])
        block['last_time_s'], block['last_packet_offset'] = time, row['packet_offset']
        self.previous = row

    def finish(self):
        if self.current is None:
            return
        b = self.current
        if b['samples'] < POLICY['minimum_samples_per_block'] or b['last_time_s']-b['first_time_s'] < POLICY['minimum_block_span_s']:
            b['flags'].add('incomplete_second')
        b['flags'] = sorted(b['flags'])
        b['complete_diagnostic_block'] = not b['flags']
        b['nominal_interval_sum_s'] = b['samples']*installation.PERIOD_S
        b['dv_sum_mps_hypothesis'] = [v*installation.VELOCITY_SCALE for v in b['raw_increment_sums'][:3]]
        b['dtheta_sum_rad_hypothesis'] = [v*installation.ANGLE_SCALE for v in b['raw_increment_sums'][3:]]
        # Summed increments divided by elapsed time avoids a mean of jitter-amplified rates.
        b['angular_rate_native_rads_by_clock_hypothesis'] = {}
        if b['complete_diagnostic_block']:
            for label, denominator in (('header_elapsed', b['header_interval_sum_s']),
                                       ('nominal_200Hz', b['nominal_interval_sum_s'])):
                b['angular_rate_native_rads_by_clock_hypothesis'][label] = [v/denominator for v in b['dtheta_sum_rad_hypothesis']]
        self.blocks.append(b)
        self.current = None


def scan(path, expected_hash, leap):
    """One strict source pass; retain compact increments and checksummed primary GPS."""
    blocks, counts, versions = IncrementBlocks(leap), Counter(), Counter()
    settings, gga, zda, cross = [], [], [], []
    nmea, current = ap.NMEA(), None
    with il.open_source(path) as original:
        stream = follow.HashedReader(original)
        for frame in ap.frames(stream):
            counts[f'{frame.tag}:{frame.group}'] += 1
            if frame.tag == '$MSG' and frame.group in (1, 20):
                signature = frame.packet[10:-4].hex()
                if current is None or signature != current['signature']:
                    current = dict(installation.installation_message(frame), signature=signature)
                    settings.append(current)
            elif frame.tag == '$GRP' and frame.group == 4:
                row = ap.group4(frame)
                blocks.feed(row, current)
                if row['time_types'] == 33:
                    cross.append(row['time1_s']-row['time2_s'])
            elif frame.tag == '$GRP' and frame.group == 99:
                versions[ap.group99(frame)] += 1
            elif frame.tag == '$GRP' and frame.group == 10001:
                header = ap.time_header(frame)
                for sentence in nmea.feed(ap.group10001(frame)[1]):
                    if not sentence['valid']:
                        continue
                    f = sentence['fields']
                    if f[0].endswith('ZDA'):
                        zda.append(dict(header, date=datetime.date(int(f[4]), int(f[3]), int(f[2])).isoformat(), sod=follow.utc_sod(f[1])))
                    elif f[0].endswith('GGA') and int(f[6]) in (1, 2, 4, 5):
                        gga.append(dict(header, sod=follow.utc_sod(f[1]), latitude_deg=ap.coordinate(f[2], f[3]),
                                        longitude_deg=ap.coordinate(f[4], f[5]), fix_quality=int(f[6])))
            if max(len(blocks.blocks), len(gga), len(zda), len(settings)) > 20000:
                raise ValueError('bounded six-file observation capacity exceeded')
    blocks.finish()
    if stream.digest.hexdigest() != expected_hash:
        raise ValueError('original uncompressed SHA-256 mismatch')
    timing = follow.timing_check(zda, cross)
    if not timing['accepted'] or timing['gps_minus_utc_s'] != leap:
        raise ValueError('dated receiver/IMU time mapping did not reproduce')
    _, fixes = follow.mapped_context([], gga, timing)
    return blocks.blocks, fixes, dict(source_sha256=expected_hash, source_bytes=stream.size,
        frame_counts=dict(counts), versions=dict(versions), settings=settings, timing=timing,
        nmea=nmea.finish(), group1_used_for_observation=False,
        direct_IMU_Group10002_count=counts['$GRP:10002'],
        independent_attitude_observation_established=False,
        earth_rate_retention_established=False, processing=il.PROCESSING)


def geometry(fixes, blocks):
    """Coordinate rates only; no fused orientation, gyro residuals or window promotion."""
    if len(fixes) < 3:
        return dict(samples=0, reason='insufficient independent receiver positions')
    t = np.array([r['utc_week_s'] for r in fixes])
    if np.any(np.diff(t) <= 0):
        return dict(samples=0, reason='duplicate/reversed receiver epochs; no repair')
    lat = np.deg2rad([r['latitude_deg'] for r in fixes])
    lon = np.unwrap(np.deg2rad([r['longitude_deg'] for r in fixes]))
    dlat = motion.local_slope(t, lat, POLICY['coordinate_slope_span_s'], POLICY['maximum_gps_gap_s'])
    dlon = motion.local_slope(t, lon, POLICY['coordinate_slope_span_s'], POLICY['maximum_gps_gap_s'])
    valid = np.isfinite(dlat+dlon)
    selected, matching_errors = [], []
    for b in blocks:
        if not b['complete_diagnostic_block']:
            continue
        middle = (b['first_time_s']+b['last_time_s'])/2
        i = int(np.searchsorted(t, middle))
        candidates = [j for j in (i-1, i) if 0 <= j < len(t)]
        distances = [abs(t[j]-middle) for j in candidates]
        if not distances:
            continue
        best = min(distances)
        matches = [j for j, distance in zip(candidates, distances) if abs(distance-best) < 1e-8]
        if len(matches) != 1 or best > POLICY['maximum_gps_distance_s']:
            continue
        j = matches[0]
        if valid[j]:
            selected.append((middle, lat[j], dlat[j], dlon[j], b['installation_signature']))
            matching_errors.append(best)
    if len(selected) < 10:
        return dict(samples=len(selected), reason='fewer than ten complete coordinate-supported diagnostic seconds')
    values = np.array([r[:4] for r in selected])
    times, phi, phi_dot, lam_dot = values.T
    # Frame kinematics from reported coordinates; GNSS geometric assumptions remain conditional.
    rotating = models.earth_rate_sphere(phi)
    globe = np.column_stack((np.cos(phi)*lam_dot, -phi_dot, -np.sin(phi)*lam_dot))
    disc = np.column_stack((np.zeros(len(phi)), np.zeros(len(phi)), -lam_dot))
    heading = np.arctan2(np.cos(phi)*lam_dot, phi_dot)
    # Motion-free orientation sensitivity is restricted to a moving trajectory.
    speed_proxy = models.WGS84_A*np.hypot(phi_dot, np.cos(phi)*lam_dot)
    moving = speed_proxy >= 50
    segments = np.cumsum(np.r_[True, (np.diff(times)>1.1) |
        np.array([a[4]!=b[4] for a,b in zip(selected, selected[1:])])])
    fields = dict(samples=len(selected), moving_samples=int(sum(moving)),
        time_matching='Unique nearest receiver position within 0.51 s; no interpolation',
        maximum_receiver_matching_error_s=max(matching_errors),
        latitude_range_deg=np.rad2deg([phi.min(), phi.max()]).tolist(),
        speed_proxy_range_mps=[float(speed_proxy.min()), float(speed_proxy.max())],
        receiver_stationary_like_seconds=int(sum(speed_proxy <= .5)),
        stationary_like_is_not_independent_body_stillness=True,
        raw_rate_values_used_in_geometry=False, level_flight_established=False,
        coordinate_assumption='Receiver latitude/longitude accepted as reported coordinate labels; speed and heading proxies assume a globe metric. Not raw GNSS observables or measured body attitude.',
        diagnostic_orientation='Level body following ground track plus fixed crab/bank/pitch envelope. Aircraft rotation assumed known only for the conditional diagnostic.')
    if sum(moving) < 10:
        return dict(fields, reason='insufficient moving coordinate context for conditional geometry')
    moving_times, moving_segments = times[moving], segments[moving]
    moving_segments = np.cumsum(np.r_[True, (np.diff(moving_times)>1.1) | (np.diff(moving_segments)!=0)])
    envelope = contrast_envelope(moving_times, heading[moving], rotating[moving], globe[moving], disc[moving], moving_segments)
    return dict(fields, conditional_geometry=envelope,
        unconstrained_aircraft_motion=dict(retained_fraction_all_pairs=0.,
            reason='An unrestricted three-axis aircraft rotation at each epoch can absorb any additive Earth-model contrast. Independent motion constraints are required.'))


def projection(y, nuisance):
    y, nuisance = np.asarray(y, float), np.asarray(nuisance, float)
    norms = np.linalg.norm(nuisance, axis=0)
    x = nuisance[:, norms > 0]/norms[norms > 0]
    if not x.shape[1]:
        return y.copy(), 0
    u, singular, _ = np.linalg.svd(x, full_matrices=False)
    rank = int(np.sum(singular > singular[0]*POLICY['nuisance_svd_relative_cutoff']))
    return y-u[:, :rank]@(u[:, :rank].T@y), rank


def nuisance_matrix(times, anchor, segments, treatment):
    """Separate offsets/drifts for each uninterrupted run and installation epoch."""
    n = len(times)
    columns = []
    for group in np.unique(segments):
        mask = segments == group
        centered = times-times[mask].mean()
        span = max(float(np.ptp(times[mask])), 1.)
        basis = [mask.astype(float)]
        if treatment != 'constant_bias':
            basis.append(mask*centered/span)
        for b in basis:
            for axis in range(3):
                c = np.zeros((n, 3)); c[:, axis] = b; columns.append(c.ravel())
        if treatment != 'linear_drift_gain_mount_tangents':
            continue
        # Unbounded tangent projection is conservative; it does not apply calibrated gain bounds.
        for axis in range(3):
            c = np.zeros((n, 3)); c[:, axis] = mask*anchor[:, axis]; columns.append(c.ravel())
            generator = np.eye(3)[axis]
            columns.append((np.cross(generator, anchor)*mask[:, None]).ravel())
    return np.column_stack(columns)


def contrast_envelope(times, heading, rotation, globe, disc, segments):
    names = list(models.EXPECTED_K)
    pairs = [(a, b) for i,a in enumerate(names) for b in names[i+1:]]
    result = {}
    for treatment in ('constant_bias', 'constant_and_linear_drift', 'linear_drift_gain_mount_tangents'):
        scores = {'|'.join(pair): None for pair in pairs}
        for crab in POLICY['crab_envelope_deg']:
            yaw = heading+np.deg2rad(crab)
            local_to_heading = np.array([installation.rotation([0, 0, np.rad2deg(h)]).T for h in yaw])
            for roll in POLICY['attitude_envelope_deg']:
                for pitch in POLICY['attitude_envelope_deg']:
                    transform = np.einsum('ij,njk->nik', installation.rotation([roll,pitch,0]).T, local_to_heading)
                    apply = lambda v: np.einsum('nij,nj->ni', transform, v)
                    anchors = dict(sphere_rotating=apply(rotation+globe), sphere_still=apply(globe), flat_still=apply(disc))
                    for anchor_name, anchor in anchors.items():
                        nuisance = nuisance_matrix(times, anchor, segments, treatment)
                        for a,b in pairs:
                            key = a+'|'+b
                            contrast = (anchors[a]-anchors[b]).ravel()
                            residual, rank = projection(contrast, nuisance)
                            total = float(contrast@contrast)
                            retained = float(residual@residual)
                            fraction = min(1., retained/total) if total else 0.
                            rms = np.sqrt(retained/len(times))*180/np.pi*3600
                            candidate = dict(retained_fraction=fraction, retained_vector_rms_deg_hour=float(rms),
                                total_vector_rms_deg_hour=float(np.sqrt(total/len(times))*180/np.pi*3600),
                                worst_state=dict(crab_deg=crab, roll_deg=roll, pitch_deg=pitch, model_anchor=anchor_name),
                                nuisance_rank=rank)
                            if scores[key] is None or fraction < scores[key]['retained_fraction']:
                                scores[key] = candidate
        result[treatment] = scores
    return dict(samples=len(times), independent_motion_assumed_known=True, decision_enabled=False,
                noise_weighting='Uniform diagnostic weights; no measured noise or power claim',
                nuisance='Per uninterrupted run/installation: offsets; then offsets and linear drifts; then also unbounded per-axis gain and mounting-angle tangents at every physical anchor. Gain/mount tangent loss is a local diagnostic, not a globally bounded physical fit.',
                comparisons=result)


def gzip_json(path, value):
    temporary = path.with_suffix(path.suffix+'.partial')
    with temporary.open('wb') as stream:
        with gzip.GzipFile(filename='', mode='wb', fileobj=stream, mtime=0) as compressed:
            compressed.write(json.dumps(value, sort_keys=True, allow_nan=False).encode())
        stream.flush(); os.fsync(stream.fileno())
    temporary.replace(path)


def verify_report(report, artifact, expected_task=None, expected_source=None):
    if report['version'] != VERSION or report['scientific_eligible'] or report['earth_model_fit_attempts']:
        raise ValueError('invalid cached observation report')
    if 'error' not in report and il.sha256(artifact) != report['blocks_sha256']:
        raise ValueError('cached increment artifact hash mismatch')
    if expected_task is not None and report['task_id'] != expected_task:
        raise ValueError('cached observation task mismatch')
    if expected_source is not None and 'error' not in report and report['provenance']['source_sha256'] != expected_source:
        raise ValueError('cached observation source mismatch')


def run(corpus, prior, output):
    corpus, prior, output = map(Path, (corpus, prior, output))
    old = json.loads((prior/'summary.json').read_text())
    if old['state'] != 'complete' or old['errors'] or old['files'] != 6:
        raise ValueError('requires the completed six-file installation audit')
    records = {r['task_id']:r for r in map(json.loads, (corpus/'records.jsonl').read_text().splitlines())}
    sources = [Path(m.__file__) for m in (ap, il, follow, installation, motion, models)] + [Path(__file__),
        Path(__file__).parents[1]/'tests/ilvis0_observation_worker.py']
    context_paths = {r['task_id']:Path('data/ilvis0-followup-20261007')/(r['task_id']+'.json') for r in old['results']}
    inputs = [prior/'summary.json', prior/'manifest.json', corpus/'records.jsonl'] + list(context_paths.values())
    manifest = dict(version=VERSION, policy=POLICY, sources={str(p):il.sha256(p) for p in sources},
        inputs={str(p):il.sha256(p) for p in inputs}, tasks=[r['task_id'] for r in old['results']],
        python=platform.python_version(), numpy=np.__version__,
        threads={k:os.environ.get(k) for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS')},
        selection='Frozen six metadata/date/hash-selected IMU6 representatives; no Earth residual selection',
        no_original_deletion=True, no_fused_attitude_in_observation=True)
    if output.exists() and not (output/'manifest.json').exists():
        raise ValueError('unmarked observation output directory')
    output.mkdir(parents=True, exist_ok=True)
    with (output/'run.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (output/'manifest.json').exists():
            if json.loads((output/'manifest.json').read_text()) != manifest:
                raise ValueError('frozen observation implementation/input/environment mismatch')
        else:
            follow.atomic_json(output/'manifest.json', manifest)
        reports = []
        for row in old['results']:
            for p in sources+inputs:
                if il.sha256(p) != manifest['sources'].get(str(p),manifest['inputs'].get(str(p))):
                    raise ValueError('frozen observation source/input changed')
            task = row['task_id']; dest = output/(task+'.json'); artifact = output/(task+'-blocks.json.gz')
            follow.atomic_json(output/'status.json', dict(state='running',pid=os.getpid(),completed=len(reports),total=6,task_id=task))
            if dest.exists():
                report = json.loads(dest.read_text()); verify_report(report, artifact,task,row['provenance']['source_sha256'])
            else:
                try:
                    timing = json.loads(context_paths[task].read_text())['timing']
                    if not timing['accepted'] or len(timing['dates']) != 1:
                        raise ValueError('unsupported prior dated timing context')
                    blocks, fixes, provenance = scan(follow.source_path(corpus,records[task]),
                        row['provenance']['source_sha256'],follow.leap_seconds(timing['dates'][0]))
                    gzip_json(artifact, dict(version=VERSION, blocks=blocks, receiver_fixes=fixes,
                        units_status='Empirical IMU6 scale/clock hypotheses; no scientific promotion',
                        source_sha256=row['provenance']['source_sha256']))
                    flags = Counter(f for b in blocks for f in b['flags'])
                    report = dict(provenance=provenance, blocks=len(blocks),
                        complete_diagnostic_blocks=sum(b['complete_diagnostic_block'] for b in blocks),
                        block_flags=dict(flags), blocks_sha256=il.sha256(artifact),
                        geometry=geometry(fixes,blocks))
                except ValueError as error:
                    report = dict(error=str(error))
                report.update(version=VERSION,task_id=task,filename=row['filename'],scientific_eligible=False,earth_model_fit_attempts=0)
                follow.atomic_json(dest,report)
            reports.append(report)
        summary = dict(version=VERSION,state='complete',files=6,errors=sum('error' in r for r in reports),
            results=reports,earth_model_fit_attempts=0,scientific_eligibility_changes=0,originals_deleted=0)
        follow.atomic_json(output/'summary.json',summary)
        compact = {k:v for k,v in summary.items() if k != 'results'}
        follow.atomic_json(output/'status.json',dict(compact,pid=os.getpid()))
        print(json.dumps(compact),flush=True)
    return summary


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--corpus',type=Path,default=Path('data/ilvis0-ready'))
    parser.add_argument('--prior',type=Path,default=Path('data/ilvis0-installation-clock-20261007'))
    parser.add_argument('--output',type=Path,default=Path('data/ilvis0-observation-20261007'))
    args=parser.parse_args(); run(args.corpus,args.prior,args.output)


if __name__ == '__main__':
    main()
