# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved-only comparison of generated full-fit and observed ESA training cost."""

import argparse
import hashlib
import io
import json
import math
from pathlib import Path


def score_candidate(fit, summary, *, training_epochs):
    from .esa_training_linearization_report import analyze_fit

    cost = fit.get('residual_sum_squares')
    expected = summary.get('training_cost')
    if (not isinstance(cost,(int,float)) or not math.isfinite(cost) or
            not isinstance(expected,(int,float)) or not math.isfinite(expected)
            or abs(cost-expected) > max(1e-8,1e-10*abs(cost))):
        raise ValueError('saved candidate cost differs')
    converged = bool(fit.get('converged') is True and
                     fit.get('stopping_rule_verified') is True)
    if (summary.get('converged') is not converged or
            summary.get('active_bounds') != fit.get('active_bounds')):
        raise ValueError('saved candidate numerical status differs')
    status = ('numerical_nonpass' if not converged else
              'bound_active' if fit['active_bounds'] else
              'interior_complete')
    reference = (analyze_fit(fit,training_epochs=training_epochs)
                 if status == 'interior_complete' else None)
    return dict(status=status, training_cost=float(cost),
                active_bounds=fit['active_bounds'],
                linear_reference=reference,scientific_decision='abstain')


def validate_observed_reference(observed):
    if (observed.get('protected_confirmation_groups_opened') != 0 or
            set(observed.get('laws', {})) != {'increment', 'point'} or
            any(row.get('training_epochs') != 600
                for row in observed['laws'].values())):
        raise ValueError('sealed ESA training reference differs')


def _study(root):
    from .esa_fit_adjusted_control_study import ID
    from .studies.closed import ClosedStudy
    from .studies.combined_task_evidence import inspect as inspect_lineage
    from .airquantumgrav_observed_hybrid_combined_audit import CombinedStudy

    name = 'data/'+ID
    continuation = root/(name+'-continuation')
    if continuation.exists():
        lineage = inspect_lineage(root,continuation)
        if (lineage.get('verified') is not True or
                lineage.get('parent') != name or
                lineage.get('state') != 'all_tasks_finished' or
                lineage.get('completed') != 2 or
                lineage.get('pending_identities')):
            raise ValueError('complete verified two-task recovery required')
        return CombinedStudy(root,lineage),lineage['lineage_sha256']
    study = ClosedStudy(root,name)
    if study.completion['state'] != 'complete':
        study.close()
        raise ValueError('complete sealed two-task control required')
    return study,None


def _artifact(study,identity,name,*,raw=False):
    if not raw:
        return study.artifact(identity,name)
    if hasattr(study,'read_artifact'):
        path=f'artifacts/{identity}/{name}'
        expected=study.envelope(identity)['artifacts'][path]
        return study.read_artifact(identity,path,expected,raw=True)
    return study.artifact(identity,name,raw=True)


def build(root):
    import numpy as np
    from .esa_fit_adjusted_control_study import ID,SCOPE,LAWS,SEEDS,tasks,recipe
    from .esa_training_linearization_report import build as observed_build
    from .ilvis0_control_shards import verify_completion
    from .studies.artifacts import digest,encoded

    root = Path(root).resolve()
    parent = root/'data'/ID
    verify_completion(parent)
    study,lineage_sha = _study(root)
    try:
        if (study.manifest.get('scope') != SCOPE or
                study.input('recipe') != recipe() or
                set(study.tasks) != set(LAWS) or
                set(study.rows) != set(LAWS)):
            raise ValueError('unchanged two-case generated cohort required')
        cases = {}
        for task in tasks():
            identity = task['identity']
            if {key:value for key,value in study.tasks[identity].items()
                    if key not in ('index','shard')} != task:
                raise ValueError('frozen task differs')
            outcome = study.envelope(identity)['result']
            if (outcome.get('passed') is not True or
                    outcome.get('scientific_decision') != 'abstain' or
                    outcome.get('truth_law') != identity or
                    outcome.get('noise_seed') != SEEDS[identity] or
                    outcome.get('training_epochs') != 600 or
                    outcome.get('same_measured_input_for_both_laws') is not True or
                    outcome.get('original_reads') != 0 or
                    outcome.get('protected_reads') != 0):
                raise ValueError('complete generated-only paired outcome required')
            binding = study.artifact(identity,'input-binding.json')
            summaries = study.artifact(identity,'matched-fit-summary.json')
            rows = study.artifact(identity,'training-receiver.json')
            if (binding['training_epochs'] != 600 or
                    binding['truth_law'] != identity or
                    binding['noise_seed'] != SEEDS[identity] or
                    digest(encoded(rows)) != binding['training_receiver_sha256'] or
                    set(summaries) != set(LAWS) or
                    outcome['candidate_results'] != summaries):
                raise ValueError('same generated measured-input binding required')
            raw = _artifact(study,identity,'measured-inputs.npz',raw=True)
            with np.load(io.BytesIO(raw),allow_pickle=False) as archive:
                if set(archive.files) != {'theta','dv','dt','times'}:
                    raise ValueError('complete raw generated inputs required')
                arrays = {key:np.asarray(archive[key],dtype='<f8')
                          for key in ('theta','dv','dt')}
                if (len(arrays['dt']) != 270000 or
                        len(archive['times']) != 900 or
                        any(digest(value.tobytes()) != binding[
                            'measured_raw_array_sha256'][key]
                            for key,value in arrays.items())):
                    raise ValueError('saved generated IMU arrays differ')
            candidates = {}
            for law in LAWS:
                fit = study.artifact(identity,law+'/fit.json')
                earlier = study.artifact(identity,
                                          law+'/training-observations.json')
                if (earlier['training_epochs'] != 600 or
                        earlier['prediction_epochs'] != 300 or
                        earlier['prediction_receiver_positions_used'] is not False or
                        summaries[law]['input_binding_sha256'] !=
                            digest(encoded(binding))):
                    raise ValueError('candidate used changed training support')
                candidates[law] = score_candidate(
                    fit,summaries[law],training_epochs=600)
            cases[identity] = dict(truth_law=identity,
                noise_seed=SEEDS[identity],candidates=candidates,
                same_measured_input_for_both_laws=True,
                scientific_decision='abstain')
        observed = observed_build(root)
        validate_observed_reference(observed)
        return dict(version='esa-fit-adjusted-control-report-v1',
            study='data/'+ID,
            study_manifest_sha256=study.completion['manifest_sha256'],
            study_summary_sha256=study.completion['summary_sha256'],
            continuation_lineage_sha256=lineage_sha,
            report_source_sha256=hashlib.sha256((root/
                'analysis/lll/esa_fit_adjusted_control_report.py').read_bytes()
            ).hexdigest(),
            cases=cases, observed_esa_training_reference=dict(
                fit_manifest_sha256=observed['fit_manifest_sha256'],
                laws={law:dict(quadratic=observed['laws'][law]['quadratic'],
                    quadratic_to_linear_reference_ratio=observed['laws'][law][
                        'quadratic_to_linear_reference_ratio']) for law in LAWS}),
            generated_recordings=2,attempted_fits=4,
            protected_confirmation_groups_opened=0,
            fit_adjusted_tail_calibrated=False,
            observed_error_law_qualified=False,
            scientific_decision='abstain')
    finally:
        study.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',default='.')
    parser.add_argument('--output',required=True)
    args = parser.parse_args(argv)
    result = build(args.root)
    output = Path(args.output)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps({truth:{law:row['status'] for law,row in
        case['candidates'].items()} for truth,case in result['cases'].items()},
        sort_keys=True))


if __name__ == '__main__':
    main()
