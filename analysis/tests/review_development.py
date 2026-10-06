# SPDX-License-Identifier: AGPL-3.0-or-later
"""Review recorded development selection and rank margins; no fits or threshold estimation."""
import argparse
from collections import Counter
import gzip
import hashlib
import json
import math
from pathlib import Path

from lll.policy import research_eligible
from lll.research_design import implementation_hash


def review(campaign, calibration_minimum=29285, validation_minimum=33169):
    if campaign.get('partition') != 'development':
        raise ValueError('selection tuning requires development evidence')
    if campaign.get('implementation_hash') != implementation_hash():
        raise ValueError('shared gate implementation differs from the recorded campaign')
    rows = campaign['records']
    if not rows or any(row.get('partition') != 'development' or row.get('replay') for row in rows):
        raise ValueError('expected original development records')
    seconds = campaign['elapsed_s']/len(rows)
    scenarios = {}
    for scenario in sorted({row['scenario'] for row in rows}):
        group = [row for row in rows if row['scenario'] == scenario]
        failures = [row for row in group if 'model contrast not identified' in row.get('exclusions', [])]
        flagged = [row for row in group if 'mount_slip_detected' in row.get('flags', [])]
        scenarios[scenario] = dict(attempts=len(group), slip_flags=len(flagged), design_failures=len(failures),
            design_failures_with_slip_flag=sum('mount_slip_detected' in row.get('flags', []) for row in failures),
            flagged_with_zero_injected_mount_slip=sum(
                row.get('design', {}).get('simulator', {}).get('mount_slip_deg_per_h') == [0., 0.] for row in flagged),
            failed_contrasts=dict(Counter(name for row in failures for name, item in
                row['design_identifiability']['model_contrast_information'].items() if not item['estimable'])))
    profiles = []
    for margin in (0., .05, .10, .20):
        counts, accepted = {}, []
        for row in rows:
            key = row['truth']+'/'+row['scenario']
            cell = counts.setdefault(key, dict(attempts=0, eligible=0, eligible_rank2=0, null_rejections=0))
            cell['attempts'] += 1
            policy = row.get('inference_policy', {})
            proposed = {**row, 'inference_policy': {**policy, 'settings': {
                **policy.get('settings', {}), 'rank_min_relative_margin': margin}}}
            if row.get('rejected') is not None and research_eligible(proposed):
                accepted.append(proposed)
                cell['eligible'] += 1
                cell['eligible_rank2'] += row.get('model_test_rank') == 2
                cell['null_rejections'] += bool(row['rejected'])
        if margin == 0.:
            original = sum(not row.get('failure') and not row.get('exclusions') and row.get('rejected') is not None for row in rows)
            if original != len(accepted):
                raise ValueError('baseline shared gate no longer reproduces recorded acceptance')
        probability = min(cell['eligible_rank2']/cell['attempts'] for cell in counts.values())
        calibration_n = math.ceil(calibration_minimum/probability) if probability else None
        validation_n = math.ceil(validation_minimum/probability) if probability else None
        total = len(counts)*(calibration_n+validation_n) if probability else None
        profiles.append(dict(proposed_relative_rank_margin=margin, eligible=len(accepted),
            null_rejections=sum(bool(row['rejected']) for row in accepted),
            eligible_rank_counts=dict(Counter(row.get('model_test_rank') for row in accepted)), cells=counts,
            minimum_observed_rank2_acceptance=probability,
            estimated_calibration_attempts_per_cell=calibration_n,
            estimated_validation_attempts_per_cell=validation_n,
            estimated_combined_attempts=total, estimated_serial_days=total*seconds/86400 if total else None))
    return dict(partition='development', mode='recorded gate sensitivity; no refits, no cutoff changes, no calibration',
        source_implementation_hash=campaign['implementation_hash'], source_manifest_hash=campaign.get('manifest_hash'),
        original_attempts=len(rows), seconds_per_attempt=seconds,
        sample_goals=dict(calibration_accepted_per_cell=calibration_minimum,
                          validation_accepted_per_cell=validation_minimum),
        scenarios=scenarios, rank_margin_profiles=profiles,
        limitations=['Proposed gates were not applied to any deployed policy.',
            'Calibration/validation costs use minimum observed cell acceptance, not a confidence bound.',
            'Future calibrated-rule acceptance can differ.',
            'Association with watchdog flags does not establish why a segment was excluded.',
            'No development results are independent validation evidence.'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('campaign', type=Path)
    parser.add_argument('-o', required=True, type=Path)
    args = parser.parse_args()
    opener = gzip.open if args.campaign.suffix == '.gz' else open
    with opener(args.campaign, 'rt') as source:
        result = review(json.load(source))
    result['source_archive_sha256'] = hashlib.sha256(args.campaign.read_bytes()).hexdigest()
    result['review_source_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    args.o.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print(json.dumps([dict(margin=p['proposed_relative_rank_margin'], eligible=p['eligible'],
        null_rejections=p['null_rejections']) for p in result['rank_margin_profiles']]))


if __name__ == '__main__':
    main()
