# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved-only coverage audit; never changes either constituent study's outcome."""
from pathlib import Path

MATRIX='docs/timing-feasible-matrix'
COMPLETION='docs/timing-matrix-completion'
COMPLETION_MANIFEST='4ca0a4bdc1da3b05f9c5d116af34ee52bc2915c7075961f2b1c12e55c4d216e2'
COMPLETION_SUMMARY='52c7b8c090bb755eda35b8fed87779bec4544667a28f80e3d303306613454d29'
PLAN='docs/TIMING_MATRIX_ASSEMBLY_PLAN.md'
TEST='analysis/tests/test_timing_matrix_assembly.py'


def verify_shared(left,right,current,left_environment,right_environment,current_environment):
    if (not left or not set(left)<=set(right) or any(right[k]!=v for k,v in left.items())
            or any(current.get(k)!=v for k,v in right.items()) or not left_environment
            or left_environment!=right_environment or right_environment!=current_environment):
        raise ValueError('identical shared execution sources, current auditor dependencies and environment required')
    return len(left)


def assemble(left,right):
    from lll import timing_matrix_completion as completion,timing_feasible_matrix_study as matrix
    completion.verify_interrupted_matrix(left)
    missing={t['identity'] for t in completion.tasks()};new=right.get('rows',[])
    if (right.get('verified') is not True or right.get('native_qualified') is not True
            or right.get('selected')!=4 or right.get('complete')!=4 or right.get('failures')
            or right.get('verification_failures') or right.get('original_binding_replays_exact') is not True
            or right.get('manifest_sha256')!=COMPLETION_MANIFEST or right.get('summary_sha256')!=COMPLETION_SUMMARY
            or len(new)!=4 or {r['identity'] for r in new}!=missing or not all(r['passed'] for r in new)
            or len(right.get('pairs',[]))!=2 or not all(r['passed'] for r in right['pairs'])):
        raise ValueError('complete four-case qualification and exact replay required')
    rows=[dict(r,evidence_study=MATRIX) for r in left['rows']]+[dict(r,evidence_study=COMPLETION) for r in new]
    pairs=[r for r in left['pairs'] if r['passed']]+right['pairs']
    keys=[tuple(r[k] for k in ('seed','law','model','profile')) for r in pairs]
    if len(rows)!=48 or len(pairs)!=24 or len(set(keys))!=24 or set(keys)!={matrix.pair_key(t) for t in matrix.tasks()}:
        raise ValueError('exact complete 48-case and 24-pair coverage required')
    return dict(version='timing-matrix-combined-coverage-v1',verified=True,qualified=True,cases=48,start_pairs=24,
        rows=rows,pairs=pairs,preserved_interruptions=left['failures'],interrupted_source_study_qualified=False,
        original_labels_changed=False,native_calls=0,refits=0,original_reads=0,protected_reads=0,
        confidence_calibrated=False)


def inspect(root):
    from lll.studies.closed import ClosedStudy
    from lll.studies.artifacts import digest,encoded
    from lll.airquantumgrav_inventory import environment
    from lll import timing_feasible_matrix_study as matrix,timing_matrix_completion as completion
    from lll.timing_optimizer_native_report import inspect as audit
    root=Path(root).resolve();a=ClosedStudy(root,MATRIX);b=ClosedStudy(root,COMPLETION)
    try:
        shared=verify_shared(a.manifest['sources'],b.manifest['sources'],
            {k:digest((root/k).read_bytes()) for k in b.manifest['sources']},
            a.input('qualification-environment'),b.input('qualification-environment'),environment())
        if a.completion['state']!='terminal' or b.completion['state']!='complete':
            raise ValueError('preserved terminal matrix and separately complete control study required')
        old=a.input('points');new=b.input('points');tasks=matrix.tasks();ids={t['identity'] for t in tasks}
        if len(old)!=4 or len({p['identity'] for p in old})!=4 or encoded(new)!=encoded(completion.select_reference(old)):
            raise ValueError('four original references with identical one-reference completion subset required')
        reference_tasks=[]
        for point in old:
            matches=[t['identity'] for t in tasks if t['payload']==matrix.computational_payload(point['payload'])]
            if len(matches)!=1:raise ValueError('one original reference must map to one computational case')
            reference_tasks+=matches
        if len(set(reference_tasks))!=4:raise ValueError('four distinct original replay cases required')
        result=assemble(audit(root,MATRIX,definition=matrix),audit(root,COMPLETION,definition=completion))
        if {r['identity'] for r in result['rows']}!=ids:raise ValueError('unique full case coverage required')
        result.update(shared_source_files=shared,all_shared_sources_identical=True,environment_identical=True,
            original_input_replays=4,original_replay_case_ids=reference_tasks,
            evidence={MATRIX:a.completion,COMPLETION:b.completion})
        return result
    finally:a.close();b.close()


def sources(root):
    from lll.timing_matrix_completion import sources as original
    from lll.studies.dependencies import source_closure
    return source_closure(root,original(root)+['analysis/lll/timing_matrix_assembly.py',TEST,PLAN])
