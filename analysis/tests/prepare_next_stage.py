# SPDX-License-Identifier: AGPL-3.0-or-later
"""Review saved pilots and prepare prospective geometry/budget artifacts; never run flights."""
import argparse
from collections import Counter, defaultdict
import gzip
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT/'analysis'), str(ROOT/'server')]
from scipy.stats import beta, nbinom
from lll.inference_policy import INFERENCE_POLICY, digest
from lll.policy import eligibility_policies
from lll.research_design import freeze_manifest, geometry_stress_matrix, implementation_hash, validate_turn_schedule
from research import planning_eligible
from import_flight_tracks import summary


def load(path):
    with (gzip.open if path.suffix == '.gz' else open)(path, 'rt') as source:
        return json.load(source)


def review_campaigns(campaigns, margin=.1):
    seen, reports = set(), []
    reference = campaigns[-1]['config']
    for campaign in campaigns:
        rows = campaign.get('records', [])
        if campaign.get('partition') != 'development' or not rows or any(
                row.get('partition') != 'development' or row.get('replay') for row in rows):
            raise ValueError('requires original development evidence, never holdouts or replays')
        if campaign.get('eligibility_policies') != eligibility_policies():
            raise ValueError('eligibility policy differs; cannot standardize saved gates')
        if campaign.get('numerical_environment_hash') != campaigns[-1].get('numerical_environment_hash'):
            raise ValueError('numerical environments differ')
        manifest = campaign['manifest']
        if (manifest['manifest_hash'] != digest({k: v for k, v in manifest.items() if k != 'manifest_hash'})
                or manifest['implementation_hash'] != campaign['implementation_hash']
                or manifest['config'] != campaign['config']
                or manifest['inference_policy_hash'] != digest(INFERENCE_POLICY)):
            raise ValueError('campaign freeze is inconsistent')
        config = campaign['config']
        for key in ('protocol', 'variant', 'scenarios', 'truths', 'geometry'):
            if config[key] != reference[key]:
                raise ValueError('pilot domains differ')
        options = lambda value: {k: v for k, v in value.items() if k != 'rank_min_relative_margin'}
        if options(config['fit_options']) != options(reference['fit_options']):
            raise ValueError('nuisance/fit settings differ')
        groups = defaultdict(list)
        for row in rows:
            identity = (row['truth'], row['scenario'], row['seed'], row.get('variant'))
            if identity in seen:
                raise ValueError('overlapping or duplicate development attempts')
            seen.add(identity)
            groups[row['truth']+'/'+row['scenario']].append(row)
        cells = {}
        for key, group in groups.items():
            accepted = [r for r in group if planning_eligible(r, margin)]
            flagged = [r for r in group if 'mount_slip_detected' in r.get('flags', [])]
            design_failed = [r for r in group if 'model contrast not identified' in r.get('exclusions', [])]
            cells[key] = dict(attempts=len(group), eligible_common_margin=len(accepted),
                eligible_rank2=sum(r.get('model_test_rank') == 2 for r in accepted),
                diagnostic_null_rejections=sum(r.get('rejected') is True for r in accepted),
                analysis_failures=sum(bool(r.get('failure')) for r in group),
                valid_bootstrap=sum(r.get('bootstrap', {}).get('bootstrap_valid') is True for r in group),
                rank_counts=dict(Counter(str(r.get('model_test_rank')) for r in group)),
                watchdog_flags=len(flagged), design_failures=len(design_failed),
                design_failures_with_watchdog_flag=sum('mount_slip_detected' in r.get('flags', []) for r in design_failed),
                watchdog_flags_with_zero_injected_creep=sum(r['design']['simulator'].get('mount_slip_deg_per_h') == [0., 0.] for r in flagged),
                rank_boundary_failures=sum('unstable model-test rank' in r.get('exclusions', []) for r in group),
                pairwise_correct_winners=sum(r.get('pairwise_three_model_winner') == r['truth'] for r in group),
                pairwise_wrong_winners=sum(r.get('pairwise_three_model_winner') not in (None, r['truth']) for r in group),
                seconds_per_attempt=sum(r['elapsed_s'] for r in group)/len(group))
        details = [item for r in rows for item in (r.get('slip') or {}).get('variants', {}).get(
            (r.get('slip') or {}).get('decided_by'), []) if item.get('slip')]
        reports.append(dict(source_implementation_hash=campaign['implementation_hash'],
            source_manifest_hash=campaign['manifest_hash'], candidate_ids=sorted({r['candidate_id'] for r in rows}),
            recorded_rank_margin=config['fit_options'].get('rank_min_relative_margin', 0.),
            recorded_eligible=sum(r.get('rejected') is not None and not r.get('exclusions') for r in rows),
            seconds_per_attempt=campaign['elapsed_s']/len(rows), cells=cells,
            watchdog_details_available=any(bool(r.get('slip')) for r in rows),
            detailed_flagged_segments=len(details),
            flagged_segments_without_airframe_calibration=sum(not item['airframe_field_calibrated'] for item in details)))
    return dict(partition='development', mode='saved-record comparison; no fits or threshold estimation',
        common_rank_margin=margin, current_implementation_hash=implementation_hash(),
        gate_source_sha256=hashlib.sha256((ROOT/'analysis/lll/policy.py').read_bytes()).hexdigest(),
        source_versions_pooled_for_inference=False, reports=reports,
        conclusions=['Report wind/watchdog selection separately; retain protective exclusions.',
            'Rank 2 with a 10% margin remains the restricted proposed calibration stratum.',
            'Common-margin review does not overwrite recorded decisions or erase retained null rejections.',
            'No guarantees outside the exact simulated protocol/scenarios/sensor are established.',
            'No independent aircraft heading or real IMU evidence is available.'])


def geometry_plan(bundles):
    matrix = geometry_stress_matrix()
    factors = ('latitude_deg', 'heading_count', 'heading_separation', 'duration_min', 'speed_mps', 'turn_count')
    anchor = dict(latitude_deg=35., heading_count=6, heading_separation='good', duration_min=60., speed_mps=270., turn_count=3)
    selected = []
    for cell in matrix:
        validate_turn_schedule([t for t, _ in cell['simulator']['index_turns']], cell['duration_min'])
        axis_case = sum(cell[key] != anchor[key] for key in factors) <= 1
        weak_interaction = (cell['latitude_deg'] in (-65., 5., 65.) and cell['heading_count'] == 2
                            and cell['heading_separation'] == 'poor' and cell['turn_count'] == 0)
        if axis_case or weak_interaction:
            selected.append(cell)
    tracks = []
    for bundle in bundles:
        if bundle.get('partition') != 'development' or bundle.get('track_format') != 'position-track-2':
            raise ValueError('requires provenance-bearing development position tracks')
        for track in bundle['tracks']:
            windows = summary(track)['windows_75min']
            qualified = [w for w in windows if w['observed_coverage_fraction'] >= .95]
            def geometry_key(window):
                positions = [r for r in track['rows'] if window['start_s'] <= r['t_s'] <= window['end_s']
                             and not r.get('is_provider_estimate')]
                if not positions: return (-1., -1., -window['start_s'])
                latitude_span = max(r['latitude_deg'] for r in positions)-min(r['latitude_deg'] for r in positions)
                return (latitude_span, max(abs(r['latitude_deg']) for r in positions), -window['start_s'])
            chosen = max(qualified, key=geometry_key) if qualified else max(
                windows, key=lambda w: (w['observed_coverage_fraction'], *geometry_key(w)), default=None)
            positions = [r for r in track['rows'] if chosen and chosen['start_s'] <= r['t_s'] <= chosen['end_s']]
            usable_intervals = [dict(start_s=a['t_s'], end_s=b['t_s']) for a, b in zip(positions, positions[1:])
                if not (a.get('is_provider_estimate') or b.get('is_provider_estimate')) and 0 < b['t_s']-a['t_s'] <= 90]
            tracks.append(dict(id=track['id'], source_filename=track['source_filename'], source_sha256=track['source_sha256'],
                displayed_timezone=bundle['displayed_timezone'], absolute_time_required_for_geometry_only=False,
                status='prepared_geometry_only' if qualified else 'blocked_by_observed_coverage',
                selection_rule='largest observed latitude span among qualifying windows; deterministic tie breaking',
                candidate_window=chosen, qualified_windows=len(qualified), rows=positions,
                observed_intervals=usable_intervals,
                interpolation='none; estimated points and long gaps remain unusable'))
    return dict(partition='development', state='prepared_not_run', full_matrix_cells=len(matrix),
        selected_synthetic_cells=selected, observed_track_cases=tracks,
        provisional_screen=dict(window_seconds=4500, maximum_observed_interval_seconds=90, minimum_observed_coverage=.95),
        proposed_comparisons=dict(truths=['sphere_rotating', 'sphere_still', 'flat_still'],
            scenarios=['bias_mixed', 'wind'], crab_models=['dynamic', 'wind'], common_seed_start=600500,
            bootstrap=0, mode='geometry-only design diagnostic; requires new compute budget'),
        simulated_assumptions=['A rigid mount, mount turns and sensor/nuisance processes must be explicit.',
            'Measured geometry supplies no IMU, independent heading, wind or altitude accuracy.',
            'Arbitrary observed-track replay needs integration before execution; no GNSS fallback is enabled.'],
        evidence_scope='No information/SVD calculation, inference, calibration or acceptance certification has run.')


def budget_plan(review, calibration_minimum, validation_minimum):
    if calibration_minimum < 1 or validation_minimum < 1:
        raise ValueError('accepted sample goals must be positive')
    latest = review['reports'][-1]
    cells = latest['cells']
    family = len(cells)
    probabilities = {name: cell['eligible_rank2']/cell['attempts'] for name, cell in cells.items()}
    lower = {name: float(beta.ppf(.025/family, cell['eligible_rank2'],
                                 cell['attempts']-cell['eligible_rank2']+1))
             if cell['eligible_rank2'] else 0. for name, cell in cells.items()}
    p, conservative = min(probabilities.values()), min(lower.values())
    def attempts(goal, probability, reserve=False):
        if not probability: return None
        return int(goal+nbinom.ppf(1-.025/(2*family), goal, probability)) if reserve else math.ceil(goal/probability)
    profiles = {}
    for name, probability, reserve in [('point_estimate', p, False), ('conditional_attempt_reserve', conservative, True)]:
        calibration, validation = attempts(calibration_minimum, probability, reserve), attempts(validation_minimum, probability, reserve)
        total = family*(calibration+validation) if calibration is not None else None
        profiles[name] = dict(acceptance_probability=probability, calibration_attempts_per_cell=calibration,
            validation_attempts_per_cell=validation, combined_attempts=total,
            estimated_serial_days=total*latest['seconds_per_attempt']/86400 if total else None)
    return dict(state='proposal_not_authorized', accepted_goals=dict(calibration=calibration_minimum, validation=validation_minimum),
        source='latest pilot only; earlier source remains a separate sensitivity comparison',
        latest_cell_acceptance=probabilities, simultaneous_one_sided975_lower_acceptance=lower, profiles=profiles,
        reserve_method='Split 5% planning error equally: Bonferroni acceptance bounds over cells, then negative-binomial caps over two phases per cell',
        limitations=['Reserve assumes independent attempts within each cell and stable future acceptance.',
            'Development-selected gates, source revisions and unknown calibrated-rule acceptance prevent a guaranteed budget.',
            'Runtime is extrapolated, not bounded; parallel scaling has not been measured.',
            'No real-flight or external-track domain is covered by this restricted proposal.'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--campaigns', type=Path, nargs='+', required=True)
    parser.add_argument('--track-bundles', type=Path, nargs='+', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--calibration-minimum', type=int, default=29285)
    parser.add_argument('--validation-minimum', type=int, default=33169)
    parser.add_argument('--calibration-manifest', type=Path, help='check the frozen proposal and write a durable readiness handoff')
    args = parser.parse_args()
    comparison = review_campaigns([load(path) for path in args.campaigns])
    comparison['source_archives'] = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in args.campaigns}
    geometry = geometry_plan([load(path) for path in args.track_bundles])
    geometry['source_implementation_hash'] = implementation_hash()
    geometry['source_archives'] = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in args.track_bundles}
    report = budget_plan(comparison, args.calibration_minimum, args.validation_minimum)
    args.output.mkdir(parents=True, exist_ok=True)
    for name, value in [('pilot-comparison.json', comparison), ('geometry-stress-plan.json', geometry), ('compute-budget.json', report)]:
        value['preparation_source_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        (args.output/name).write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')
    if args.calibration_manifest:
        manifest = load(args.calibration_manifest)
        if manifest != freeze_manifest(manifest['config']):
            raise ValueError('proposal source/configuration/environment freeze differs')
        config = manifest['config']
        if (config['partition'] != 'calibration' or config['model_test_ranks'] != [2]
                or config['rank_min_relative_margin'] != .1 or not config['pairwise_evidence']
                or config['protocol'] != load(args.campaigns[-1])['config']['protocol']
                or config['calibration_min_accepted'] != args.calibration_minimum
                or config['tail_min_accepted'] != args.validation_minimum
                or config['seeds'] != report['profiles']['conditional_attempt_reserve']['calibration_attempts_per_cell']):
            raise ValueError('proposal differs from the restricted domain/sample goals/attempt reserve')
        artifacts = [args.output/name for name in ('pilot-comparison.json', 'geometry-stress-plan.json', 'compute-budget.json')]
        readiness = dict(state='prepared_not_authorized', additional_authorized_flight_attempts=0,
            current_implementation_hash=implementation_hash(), calibration_manifest_hash=manifest['manifest_hash'],
            artifact_sha256={str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                            for path in artifacts+[args.calibration_manifest]},
            stages=dict(saved_record_review='complete', synthetic_geometry_cases='prepared_not_run',
                observed_geometry_replay='inputs_prepared; trajectory integration and execution pending',
                calibration='restricted proposal frozen; budget and final envelope review pending',
                validation='manifest waits for actual primary and pairwise calibration threshold files',
                real_imu_bench='pending hardware; collection and production qualification remain separate'),
            order=['Review prospective geometry and obtain a bounded development budget.',
                'Run geometry diagnostics; implement and check observed-trajectory replay before use.',
                'Review final domain and refreeze any changed source/configuration/policy/environment.',
                'Obtain calibration/validation budget, run fresh calibration and freeze thresholds.',
                'Freeze independent validation with actual thresholds, run it and assess simultaneous bounds.'])
        (args.output/'readiness.json').write_text(json.dumps(readiness, indent=2, allow_nan=False)+'\n')
    print(json.dumps(dict(eligible_by_pilot=[sum(c['eligible_common_margin'] for c in r['cells'].values()) for r in comparison['reports']],
        synthetic_cells=len(geometry['selected_synthetic_cells']), observed_cases=dict(Counter(c['status'] for c in geometry['observed_track_cases'])),
        budgets=report['profiles']), indent=2))


if __name__ == '__main__':
    main()
