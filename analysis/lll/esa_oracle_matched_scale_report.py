# SPDX-License-Identifier: AGPL-3.0-or-later
"""Compare sealed known-answer forecast errors with matched generated scales."""

import argparse
import hashlib
import json
import math
from pathlib import Path


def complete_study(completion,summary,scope,rows):
    from .esa_oracle_matched_scale_study import SCOPE,LAWS
    return (completion.get('state')=='complete' and
            summary.get('completed')==2 and summary.get('passed') is True and
            scope==SCOPE and set(rows)==set(LAWS))


def build(root):
    from .esa_oracle_matched_scale_study import ID,SCOPE,LAWS
    from .esa_oracle_report import build as oracle_build
    from .studies.closed import ClosedStudy
    root=Path(root).resolve();oracle=oracle_build(root)
    study=ClosedStudy(root,'data/'+ID)
    try:
        if not complete_study(study.completion,study.summary,
                              study.manifest['scope'],study.rows):
            raise ValueError('two complete sealed matched-scale results required')
        binding=study.input('parent-binding')
        if binding['noisy']!=oracle['study_manifest_sha256']:
            raise ValueError('different sealed noisy oracle parent')
        cases={}
        for law in LAWS:
            row=study.envelope(law)['result']
            detail=study.artifact(law,'variance-comparison.json')
            predicted=detail['unconditional']
            observed=oracle['cases'][law]['oracle']
            horizontal=predicted['horizontal_rms_scale_m']
            vertical=predicted['height_rms_scale_m']
            if (row['passed'] is not True or
                    row['scientific_decision']!='abstain' or
                    detail['realized_noise_used'] is not False or
                    detail['confidence_calibrated'] is not False or
                    any(not math.isfinite(value) or value<=0 for value in
                        (horizontal,vertical)) or
                    row['unconditional_horizontal_rms_scale_m']!=horizontal or
                    row['unconditional_height_rms_scale_m']!=vertical):
                raise ValueError('incomplete matched law or scale')
            cases[law]=dict(
                predicted_horizontal_rms_scale_m=horizontal,
                realized_horizontal_rms_m=observed['horizontal_rms_m'],
                horizontal_realized_to_scale=observed['horizontal_rms_m']/horizontal,
                predicted_vertical_rms_scale_m=vertical,
                realized_vertical_rms_m=observed['vertical_rms_m'],
                vertical_realized_to_scale=observed['vertical_rms_m']/vertical)
        return dict(version='esa-oracle-matched-scale-report-v1',
            study='data/'+ID,
            study_manifest_sha256=study.completion['manifest_sha256'],
            study_summary_sha256=study.completion['summary_sha256'],
            noisy_parent_manifest_sha256=binding['noisy'],
            clean_parent_manifest_sha256=binding['clean'],
            report_source_sha256=hashlib.sha256((root/
                'analysis/lll/esa_oracle_matched_scale_report.py').read_bytes()).hexdigest(),
            cases=cases,generated_draws=2,
            original_reads=0,protected_confirmation_groups_opened=0,
            confidence_calibrated=False,scientific_decision='abstain')
    finally:study.close()


def publish(root):
    from .studies.artifacts import atomic,encoded
    root=Path(root).resolve();result=build(root)
    base=root/'docs/prediction-observed-development'
    atomic(base/'ORACLE_MATCHED_SCALE_REPORT.json',encoded(result))
    rows=[]
    for law in ('increment','point'):
        case=result['cases'][law]
        rows.append('| {} | {:.1f} | {:.1f} | {:.2f} | {:.1f} | {:.1f} | {:.2f} |'.format(
            law,case['predicted_horizontal_rms_scale_m'],
            case['realized_horizontal_rms_m'],case['horizontal_realized_to_scale'],
            case['predicted_vertical_rms_scale_m'],
            case['realized_vertical_rms_m'],case['vertical_realized_to_scale']))
    markdown=('# Error scales on the matched long generated trajectory\n\n'
        'The two sealed calculations use the same clean aircraft trajectory, '
        'known initial state and known calibration as the saved noisy forecasts. '
        'Only future reports 600–899 are compared; no future receiver errors '
        'enter the forecast-error scale.\n\n'
        '| Generated error law | Expected horizontal RMS scale (m) | Observed horizontal RMS (m) | Ratio | Expected vertical RMS scale (m) | Observed vertical RMS (m) | Ratio |\n'
        '| --- | ---: | ---: | ---: | ---: | ---: | ---: |\n' +
        '\n'.join(rows)+'\n\n'
        'These are two fixed generated draws. The expected scales assume '
        'the declared synthetic error laws and exact nominal geometry. '
        'The ratios do not establish coverage or identify the error process '
        'in an ESA recording. The seven reserved confirmation groups remain '
        'closed. [Machine-readable values](ORACLE_MATCHED_SCALE_REPORT.json) '
        'retain source and study hashes.\n')
    atomic(base/'ORACLE_MATCHED_SCALE_REPORT.md',markdown.encode())
    return result


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',default='.')
    args=parser.parse_args(argv)
    print(json.dumps(publish(args.root),sort_keys=True))


if __name__=='__main__':main()
