# SPDX-License-Identifier: AGPL-3.0-or-later
"""Read saved replay noise/information diagnostics without generating or fitting data."""
import argparse
import hashlib
import json
from pathlib import Path

PAIR = 'sphere_still_vs_flat_still'


def audit(directory):
    campaign_path = directory / 'campaign.json'
    campaign = json.loads(campaign_path.read_text())
    if not campaign['execution']['complete']:
        raise ValueError('requires the completed frozen replay')
    cases = []
    for row in campaign['records']:
        path = directory / 'diagnostics' / row['task_id'] / 'analysis.json'
        analysis = json.loads(path.read_text())
        fit = analysis['fit']
        noise = fit['noise']
        sigma = noise['sigma_by_bin_axis_dph']
        planning = row['pairwise'][PAIR]['design_information']
        actual = row['identifiability']['model_contrast_information'][PAIR]
        profile = row['pairwise'][PAIR]
        cases.append(dict(task_index=row['task_index'], truth=row['truth'],
            crab_model=row['fit_options']['crab_model'],
            analysis_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            residual_global_sigma_dph=noise['global_sigma_dph'],
            residual_axis_sigma_range_dph=[[min(s[a] for s in sigma), max(s[a] for s in sigma)] for a in range(3)],
            planning_gyro_sigma_dph=row['design_identifiability']['envelope_configuration']['evaluated_noise_dph'],
            planning_worst_pair_information=planning['information'],
            free_fit_weighted_pair_information=actual['pre_cutoff_information'],
            free_fit_pair_retention=actual['pre_cutoff_retained_fraction'],
            profile_sd=profile['sd'], profile_statistics=profile['statistics']))
    return dict(scope='saved residual-weight and planning-information comparison only', cases=cases,
        campaign_sha256=hashlib.sha256(campaign_path.read_bytes()).hexdigest(),
        implementation_hash=campaign['implementation_hash'],
        helper_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), additional_flight_attempts=0,
        limitations=['Residual-based scales include simulated sensor processes and processing/model discrepancy, not real-device noise.',
            'Fixed-noise envelope information and free-fit information use different states/weights; their ratio is diagnostic.',
            'Profile uncertainty includes nonlinear fitting and nuisance priors; it is not simply inverse design information.',
            'One shared generating seed; no power, coverage, threshold estimation or decision claim.',
            'No original record, scientific source, eligibility threshold or noise assumption changed.'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.directory)
    with args.output.open('x') as out:
        out.write(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps([dict(truth=c['truth'], crab=c['crab_model'],
        residual_sigma_dph=c['residual_global_sigma_dph'], planning_information=c['planning_worst_pair_information'],
        weighted_information=c['free_fit_weighted_pair_information'], profile_sd=c['profile_sd']) for c in result['cases']]))
