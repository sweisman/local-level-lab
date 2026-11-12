# SPDX-License-Identifier: AGPL-3.0-or-later
"""Verify saved timing values without refitting a terminal technical study."""
import argparse
import hashlib
import json
import math
from pathlib import Path

from lll.studies.closed import ClosedStudy


STUDY = 'data/bounded-noisy-timing-probe-20261111'
MANIFEST_SHA256 = '9c78539032f7ae0653f979fce5b5e77d00890858f3d7cedc858cfa8b1966044d'
SUMMARY_SHA256 = 'bad9ce1efd43f481b65ed977e3a293093b8a8df18d94369b7157f74a3cfb425c'
SOURCE_SHA256 = '6e785290d061881b7a0349c004fce76409af7b55031e0b60a7963f10e9873987'
LABELS = ('saved_point', 'boundary_before_1ns', 'boundary_after_1ns',
          'minus_100ns', 'plus_100ns', 'minus_10us', 'plus_10us',
          'full_timing_component')
LIMITS = dict(native_calls=239816, packet_visits=1506051012)


def summarize(rows):
    if len(rows) != 8 or tuple(row.get('label') for row in rows) != LABELS:
        raise ValueError('eight unchanged timing points required')
    base = rows[0]['actual_cost']
    predicted_base = rows[0]['predicted_local_cost']
    for row in rows:
        keys = ('actual_cost', 'predicted_local_cost',
                'actual_change_from_center', 'predicted_change_from_center',
                'physical_offset_s')
        if (row.get('changed_packet_epochs') not in (0, 79) or
                any(type(row.get(k)) not in (int, float) or not math.isfinite(row[k]) for k in keys) or
                not math.isclose(row['actual_change_from_center'], row['actual_cost'] - base,
                                 rel_tol=0, abs_tol=1e-9) or
                not math.isclose(row['predicted_change_from_center'],
                                 row['predicted_local_cost'] - predicted_base,
                                 rel_tol=0, abs_tol=1e-9)):
            raise ValueError('saved objective costs or packet assignments differ')
    if [row['changed_packet_epochs'] for row in rows] != [0, 79, 0, 79, 0, 79, 0, 79]:
        raise ValueError('complete before/after boundary geometry required')
    return dict(evaluations=8, center_cost=base,
                full_timing_actual_change=rows[-1]['actual_change_from_center'],
                full_timing_predicted_change=rows[-1]['predicted_change_from_center'],
                maximum_local_cost_disagreement=max(abs(row['actual_change_from_center'] -
                    row['predicted_change_from_center']) for row in rows),
                scientific_decision='abstain', technical_wrapper_qualified=False)


def build(root):
    root = Path(root).resolve()
    study = ClosedStudy(root, STUDY)
    try:
        if (study.completion['state'] != 'terminal' or
                study.completion['manifest_sha256'] != MANIFEST_SHA256 or
                study.completion['summary_sha256'] != SUMMARY_SHA256 or
                len(study.tasks) != 1 or len(study.rows) != 1 or
                study.rows['saved-failed-case']['passed'] is not False or
                study.manifest['sources']['analysis/lll/bounded_noisy_timing_probe.py']
                != SOURCE_SHA256):
            raise ValueError('exact terminal timing diagnostic required')
        study.read('source-freeze/analysis/lll/bounded_noisy_timing_probe.py',
                   SOURCE_SHA256, raw=True)
        envelope = study.envelope('saved-failed-case')
        if (envelope['result'] != dict(error_type='ValueError', passed=False,
                reason='one explicit software result and continued scientific abstention required',
                scientific_decision='abstain')):
            raise ValueError('original technical wrapper failure required')
        values = study.artifact('saved-failed-case', 'timing-probe.json')
        prepay = study.artifact('saved-failed-case', 'native-prepayment.json')
        if (values.get('evaluations') != 8 or values.get('passed') is not True or
                values.get('model_decision') != 'abstain' or
                values.get('original_fit_changed') is not False or
                values.get('observed_starts') != 0 or values.get('protected_reads') != 0 or
                values.get('parent_manifest_sha256') !=
                '94929800fdf681887ae62f66dcd699ad26892378672a0465709a45b7da5dd8d9' or
                values.get('native_charges') != prepay['attempted'] or
                prepay['prepaid'] != LIMITS or
                prepay['scientific_qualification'] is not False):
            raise ValueError('saved values, input, abstention or charged work differ')
        result = summarize(values['outcomes'])
        source = root / 'analysis/lll/bounded_noisy_timing_report.py'
        return dict(verified=True, study=STUDY, state='terminal',
                    original_wrapper_reason=envelope['result']['reason'],
                    study_manifest_sha256=MANIFEST_SHA256,
                    study_summary_sha256=SUMMARY_SHA256,
                    frozen_probe_source_sha256=SOURCE_SHA256,
                    report_source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                    charges=prepay['attempted'], summary=result,
                    outcomes=values['outcomes'],
                    scientific_decision='abstain')
    finally:
        study.close()


def render(report):
    if report.get('verified') is not True or report['state'] != 'terminal':
        raise ValueError('verified terminal timing evidence required')
    full = report['outcomes'][-1]
    lines = ['# Noisy timing probe: saved values', '',
             '**Eight objective points were saved, but the study did not pass its technical wrapper.**',
             'The worker used the wrong key for its final abstention field. The terminal failure',
             'and all charges remain recorded. This report audits the sealed point values only;',
             'it does not relabel the study as passing.', '',
             'The reconstructed IMU samples and receiver rows matched the original failed case.',
             'The probe kept every other fitted parameter fixed and varied only the timing offset.',
             'At points immediately before the packet boundary, all 79 receiver queries switched',
             'packets; immediately after it, none switched.', '',
             '| Timing shift | Packet changes | Actual cost change | Local predicted change |',
             '|---|---:|---:|---:|']
    for row in report['outcomes']:
        lines.append(f"| {row['label'].replace('_', ' ')} ({row['physical_offset_s']:.9g} s) "
                     f"| {row['changed_packet_epochs']} | {row['actual_change_from_center']:.9g} "
                     f"| {row['predicted_change_from_center']:.9g} |")
    lines += ['',
              f"The full timing-only shift raises the objective by {full['actual_change_from_center']:.6g}; "
              f"the local tangent predicts a rise of {full['predicted_change_from_center']:.6g}.",
              'The two-minute noisy timing-only calculation therefore follows its tangent even',
              'across packet changes. Packet switching by itself does not explain the original',
              'failed *joint* calibration/timing step. That coupled direction remains the',
              'specific numerical question; the failed 24-case stopping gate is unchanged.', '',
              'This is one generated software diagnostic, not an observed-aircraft result,',
              'uncertainty calibration or Earth-model decision. No solver start or forecast was run.', '',
              '[Original failed-case diagnosis](NONLINEAR_DIAGNOSIS.md) ·',
              '[Finite plan](TIMING_PROBE_PLAN.md) · [Technical result](NONLINEAR_RESULT.md)']
    return '\n'.join(lines) + '\n'


def publish(root):
    report = build(root)
    target = Path(root) / 'docs/bounded-calibration-prediction'
    (target / 'TIMING_PROBE_RESULT.md').write_text(render(report))
    (target / 'timing-probe-verified.json').write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default='.')
    args = parser.parse_args()
    result = publish(args.root)
    print(f"{result['summary']['evaluations']} sealed timing points audited; study remains terminal")


if __name__ == '__main__':
    main()
