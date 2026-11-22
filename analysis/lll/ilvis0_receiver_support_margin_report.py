# SPDX-License-Identifier: AGPL-3.0-or-later
"""Publish vertical-rate threshold margins from a sealed receiver-only study."""

import argparse
import csv
import hashlib
import io
import json
import math
from pathlib import Path

from .studies.artifacts import atomic, encoded
from .studies.closed import ClosedStudy


FIELDS = ('segment_id', 'filename', 'target_gps_s',
          'selected_half_window_s',
          'half_5_span_mps', 'half_5_margin_mps', 'half_5_reason',
          'half_10_span_mps', 'half_10_margin_mps', 'half_10_reason',
          'half_15_span_mps', 'half_15_margin_mps', 'half_15_reason')
WIDTHS = (5., 10., 15.)


def margin_rows(segments, *, vertical_limit_mps):
    """Describe the original selector's threshold distance without rerunning it."""
    if (not isinstance(vertical_limit_mps, (int, float)) or
            not math.isfinite(vertical_limit_mps) or vertical_limit_mps <= 0):
        raise ValueError('positive frozen vertical-rate limit required')
    rows = []
    counts = dict(targets=0, supported_targets=0, unsupported_targets=0,
                  evaluated_windows=0, selected_near_0_02=0,
                  selected_near_0_1=0, vertical_rejections=0,
                  vertical_rejected_near_0_02=0,
                  vertical_rejected_near_0_1=0)
    for segment in segments:
        if segment['disposition'] != 'screened':
            if segment['receiver_targets'] or segment['supported_targets']:
                raise ValueError('decoder abstention has receiver targets')
            continue
        targets = segment['support']['targets']
        if (len(targets) != segment['receiver_targets'] or
                sum(target['selected_half_window_s'] is not None
                    for target in targets) != segment['supported_targets']):
            raise ValueError('saved target counts differ from support inventory')
        for target in targets:
            windows = {row['half_window_s']: row for row in target['windows']}
            if set(windows) != set(WIDTHS) or len(target['windows']) != 3:
                raise ValueError('three frozen candidate windows required')
            selected = target['selected_half_window_s']
            accepted = [width for width in WIDTHS if windows[width]['accepted']]
            if selected != (max(accepted) if accepted else None):
                raise ValueError('selected window differs from saved acceptance')
            row = dict(segment_id=segment['segment_id'],
                       filename=segment['filename'],
                       target_gps_s=target['target_s'],
                       selected_half_window_s=selected if selected is not None else '')
            counts['targets'] += 1
            counts['supported_targets' if selected is not None
                   else 'unsupported_targets'] += 1
            for width in WIDTHS:
                item = windows[width]
                span = item['vertical_rate_span_mps']
                suffix = str(int(width))
                row['half_'+suffix+'_span_mps'] = '' if span is None else span
                row['half_'+suffix+'_margin_mps'] = (
                    '' if span is None else vertical_limit_mps-span)
                row['half_'+suffix+'_reason'] = item['reason'] or ''
                if span is None:
                    if item['accepted'] or item['reason'] == 'vertical_rate_span':
                        raise ValueError('vertical-rate decision lacks span')
                    continue
                if not isinstance(span, (int, float)) or not math.isfinite(span):
                    raise ValueError('finite saved vertical-rate span required')
                counts['evaluated_windows'] += 1
                if item['accepted'] and span > vertical_limit_mps:
                    raise ValueError('accepted window exceeds vertical-rate limit')
                if item['reason'] == 'vertical_rate_span':
                    if span <= vertical_limit_mps:
                        raise ValueError('vertical-rate rejection lacks excess')
                    counts['vertical_rejections'] += 1
                    excess = span-vertical_limit_mps
                    counts['vertical_rejected_near_0_02'] += excess <= .02+1e-12
                    counts['vertical_rejected_near_0_1'] += excess <= .1+1e-12
                if width == selected:
                    margin = vertical_limit_mps-span
                    counts['selected_near_0_02'] += margin <= .02+1e-12
                    counts['selected_near_0_1'] += margin <= .1+1e-12
            rows.append(row)
    return rows, counts


def publish(root='.'):
    """Write deterministic CSV and a hash receipt; never alter sealed evidence."""
    root = Path(root).resolve()
    study = ClosedStudy(root, 'data/ilvis0-receiver-support-inventory-20261113')
    try:
        if (study.completion['state'] != 'complete' or
                study.summary['completed'] != 1 or
                study.summary['passed'] is not True):
            raise ValueError('complete passing receiver-only inventory required')
        saved = study.artifact('receiver-support-all-53', 'support-windows.json')
        if (saved.get('version') != 'ilvis0-receiver-support-inventory-v1' or
                saved.get('receiver_only') is not True or
                saved.get('scientific_decision') != 'abstain' or
                saved.get('policy', {}).get('half_windows_s') != list(WIDTHS)):
            raise ValueError('unchanged receiver-only support policy required')
        prior_path = root/'docs/ilvis0-receiver-support-inventory/receipt.json'
        prior_raw = prior_path.read_bytes()
        prior = json.loads(prior_raw)
        if (prior['manifest_sha256'] != study.completion['manifest_sha256'] or
                prior['summary_sha256'] != study.completion['summary_sha256']):
            raise ValueError('published support receipt differs from sealed study')
        rows, counts = margin_rows(
            saved['segments'], vertical_limit_mps=saved['policy'][
                'maximum_vertical_rate_span_mps'])
        if (len(saved['segments']) != 53 or counts['targets'] != 2365 or
                counts['supported_targets'] != 2194 or
                counts['unsupported_targets'] != 171 or
                counts['evaluated_windows'] != 7095):
            raise ValueError('saved receiver cohort or candidate count differs')
        stream = io.StringIO(newline='')
        writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)
        table = stream.getvalue().encode('utf-8')
        source = root/'analysis/lll/ilvis0_receiver_support_margin_report.py'
        plan = root/'docs/ilvis0-receiver-support-inventory/MARGIN_PLAN.md'
        receipt = dict(
            version='receiver-support-margin-report-v1',
            manifest_sha256=study.completion['manifest_sha256'],
            summary_sha256=study.completion['summary_sha256'],
            prior_receipt_sha256=hashlib.sha256(prior_raw).hexdigest(),
            reporter_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
            plan_sha256=hashlib.sha256(plan.read_bytes()).hexdigest(),
            table_sha256=hashlib.sha256(table).hexdigest(),
            counts=counts, imu_observations_used=False,
            scientific_decision='abstain')
        output = root/'docs/ilvis0-receiver-support-inventory'
        for name, blob in (('vertical-margins.csv', table),
                           ('margin-receipt.json', encoded(receipt))):
            path = output/name
            if path.is_file() and path.read_bytes() != blob:
                raise ValueError('published margin report differs: '+name)
            if not path.is_file():
                atomic(path, blob)
        return receipt
    finally:
        study.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default='.')
    args = parser.parse_args()
    print(json.dumps(publish(args.root), sort_keys=True))


if __name__ == '__main__':
    main()
