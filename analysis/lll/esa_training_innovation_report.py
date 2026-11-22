# SPDX-License-Identifier: AGPL-3.0-or-later
"""Publish sealed ESA training-only innovation diagnostics."""

import argparse
import hashlib
import json
from pathlib import Path


def build(root):
    from .esa_training_innovation_study import ID
    from .esa_training_split_study import ID as FIT_ID, LAWS
    from .studies.closed import ClosedStudy

    root=Path(root).resolve()
    study=ClosedStudy(root,'data/'+ID)
    fit=ClosedStudy(root,'data/'+FIT_ID)
    try:
        if (study.completion['state']!='complete' or
                study.summary['completed']!=2 or
                study.summary['passed'] is not True or
                set(study.tasks)!=set(LAWS) or
                fit.completion['state']!='complete' or
                study.input('source-binding')['fit_manifest_sha256']!=
                    fit.completion['manifest_sha256']):
            raise ValueError('two sealed matching training diagnostics required')
        rows={}
        for law in LAWS:
            outcome=study.envelope(law)['result']
            saved=study.artifact(law,'innovation-summary.json')
            fitted=fit.artifact(law,'fit.json')
            if (outcome['passed'] is not True or
                    outcome['optimization_performed'] is not False or
                    outcome['later_receiver_values_used'] is not False or
                    outcome['protected_reads']!=0 or
                    saved['law']!=law or
                    saved['training_epochs']!=600 or
                    saved['training_replay']['replay_passed'] is not True or
                    abs(saved['quadratic']-fitted['residual_sum_squares'])>
                        max(1e-6,1e-8*fitted['residual_sum_squares']) or
                    saved['fit_manifest_sha256']!=
                        fit.completion['manifest_sha256'] or
                    saved['later_receiver_values_used'] is not False or
                    saved['protected_reads']!=0):
                raise ValueError('training innovation or no-leak check differs')
            rows[law]=dict(quadratic=saved['quadratic'],
                whitened_rms=saved['whitened_rms'],
                channels=saved['channels'],
                operator_configuration=saved['operator_configuration'],
                training_replay=saved['training_replay'],
                optimization_performed=False)
        return dict(version='esa-training-innovation-diagnostic-v1',
            study='data/'+ID,
            study_manifest_sha256=study.completion['manifest_sha256'],
            study_summary_sha256=study.completion['summary_sha256'],
            fit_manifest_sha256=fit.completion['manifest_sha256'],
            report_source_sha256=hashlib.sha256((root/
                'analysis/lll/esa_training_innovation_report.py').read_bytes()
            ).hexdigest(),
            training_epochs=600,laws=rows,
            fit_adjusted_reference_calibrated=False,
            independent_validation=False,
            protected_confirmation_groups_opened=0,
            scientific_decision='abstain')
    finally:
        study.close();fit.close()


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',default='.')
    parser.add_argument('--output',required=True)
    args=parser.parse_args(argv)
    result=build(args.root)
    output=Path(args.output)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps({law:dict(rms=value['whitened_rms'],
        up_lags=value['channels'][2]['lags']) for law,value in
        result['laws'].items()},sort_keys=True))


if __name__=='__main__':
    main()
