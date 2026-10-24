# SPDX-License-Identifier: AGPL-3.0-or-later
"""Closed-result reporting revision covering Definition's complete source freeze.

The original calculation and verifier stay frozen. This revision verifies the
qualified subset and mandatory execution extension before supplying the full
manifest enumeration to the original saved-array checker.
"""


def qualification_sources(root):
    return ['analysis/lll/airquantumgrav_resolution_audit.py','analysis/lll/studies/source_binding.py',
        'analysis/tests/test_study_source_binding.py','analysis/tests/test_airquantumgrav_resolution_audit.py']


def required_tests():
    return ['test_source_binding_accepts_only_unchanged_qualified_subset_and_shared_engine',
        'test_source_binding_rejects_unqualified_science_and_nested_engine_paths',
        'test_source_binding_scope_restores_enumerator_on_failure',
        'test_resolution_reporting_revision_rejects_open_before_any_override']


def inspect(root,prefix='data/esa-stopping-resolution-20261024',*,qualification):
    from pathlib import Path
    from lll.studies.closed import ClosedStudy
    from lll.studies.artifacts import digest
    from lll.studies.qualification import checked
    from lll.studies.source_binding import verify,enumeration
    study=ClosedStudy(root,prefix)
    try:
        if qualification is None:raise ValueError('source-bound reporting qualification required')
        from lll.airquantumgrav_inventory import environment
        from lll import airquantumgrav_resolution as adapter
        from lll import airquantumgrav_resolution_report as original
        request,tests=checked(root,qualification,sources=qualification_sources(root),environment=environment(),
            required_tests=required_tests(),minimum_tests=len(required_tests()))
        declared=study.input('qualification-request')['sources']
        # Verify every actual frozen file, including engine files omitted from
        # the narrower preflight closure; never accept additional science code.
        proof=verify(root,declared=declared,manifest=study.manifest['sources'])
        with enumeration(adapter,sorted(study.manifest['sources'])):
            report=original.inspect(root,prefix)
        report['reporting_revision']=dict(version='engine-complete-source-binding-v2',**proof,
            qualified_metadata_tests=len(required_tests()),metadata_request_sha256=digest(request),
            metadata_test_report_sha256=digest(tests),reporter_sha256=digest(Path(__file__).read_bytes()),
            scientific_computations_changed=False,original_stopping_labels_changed=False)
        return report
    finally:study.close()


def publish(root,prefix='data/esa-stopping-resolution-20261024',output='docs/esa-stopping-resolution',*,qualification):
    import csv
    import io
    import json
    from pathlib import Path
    from lll.airquantumgrav_resolution_report import render
    from lll.airquantumgrav_inventory import environment
    from lll.ilvis0_control_publication import publish as package
    from lll.studies.artifacts import atomic,digest,encoded,safe_path
    from lll.studies.closed import ClosedStudy
    from lll.studies.qualification import checked
    from lll.studies.publication import archive_publication
    root=Path(root).resolve();public=safe_path(root,output);data=safe_path(root,prefix)
    if (public/'evidence-receipt.json').exists():raise ValueError('diagnostic publication already sealed')
    report=inspect(root,prefix,qualification=qualification);study=ClosedStudy(root,prefix)
    try:plan=study.manifest['sources']['docs/esa-stopping-resolution/PLAN.md']
    finally:study.close()
    if digest((public/'PLAN.md').read_bytes())!=plan:raise ValueError('original frozen plan changed')
    request,tests=checked(root,qualification,sources=qualification_sources(root),environment=environment(),
        required_tests=required_tests(),minimum_tests=len(required_tests()))
    fields=('identity','model','profile','policy_id','start','complete','source_converged','source_cost','fresh_cost',
        'residual_repeat_bitwise_equal','derivative_repeat_bitwise_equal','relative_saved_cost_difference',
        'maximum_relative_cost_change','maximum_linearization_error_norm','maximum_position_change_m','correction_available')
    stream=io.StringIO(newline='');writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader()
    writer.writerows({k:row.get(k) for k in fields} for row in report['rows'])
    package(data,public,render(report));receipt=json.loads((public/'evidence-receipt.json').read_bytes());receipt['artifacts']['PLAN.md']=plan
    additions=[('artifacts/publication/verified-report.json',encoded(report)),
        ('artifacts/publication/reporter.py',Path(__file__).read_bytes()),('fixed-points.csv',stream.getvalue().encode()),
        ('artifacts/publication/report-qualification-request.json',request),
        ('artifacts/publication/report-qualification-report.xml',tests)]
    additions.extend(('artifacts/publication/reporting-source-freeze/'+name,(root/name).read_bytes()) for name in qualification_sources(root))
    for name,raw in additions:atomic(public/name,raw);receipt['artifacts'][name]=digest(raw)
    atomic(public/'evidence-receipt.json',encoded(receipt))
    return dict(archive_publication(root,data,public),published=output,native_calls=0)
