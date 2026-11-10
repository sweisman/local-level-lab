# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite generated training/forecast comparison of two tangent arithmetics."""
import json

SCOPE = 'generated paired wide/selective training and forecast; no observed or protected inputs'
PARENT_MANIFEST_SHA = '98d11063bd193578761d0fa4c79f56e4815bf03fbca9d3aa979f8c49cd789c77'
PARENT_SUMMARY_SHA = '403a495e75010708c80921ebe42639f3687a18d38abf4ac17d06c9f80b422a21'


def recipe():
    from lll.airquantumgrav_height_training import recipe as original
    return dict(original(), version='hybrid-paired-training-v1', duration_s=120.,
                queries=119, latitudes_deg=[55.], policies=['reported-short-v1'],
                starts=1, workers=4, threads=1, maximum_wall_s=7200.,
                paired_prediction_tolerance_m=0.01)


def construction_limits(r):
    from lll.airquantumgrav_height_training import construction_limits as original
    return {key: 2 * value for key, value in original(r).items()}


def tasks(r=None):
    from lll.airquantumgrav_height_training import prefix_limit
    from lll.airquantumgrav_truth import MODELS
    r = recipe() if r is None else r
    n = round(r['duration_s'] * r['rate_hz'])
    cut = 2 * r['queries'] // 3
    per_fit = (r['maximum_evaluations'] * prefix_limit(r) * cut
               + n * r['queries'])
    result = []
    for model in MODELS:
        for profile in (False, True):
            spec = dict(model=model, latitude_deg=55., profile=profile,
                        policy_id='reported-short-v1', start=0)
            result.append(dict(identity=f'{model}-{int(profile)}', input_key='recipe',
                               native_kind='tangent', payload=spec,
                               limits=dict(native_calls=2 * (r['maximum_evaluations'] + 1),
                                           packet_visits=2 * per_fit,
                                           bound_calls=0, bound_steps=0)))
    return result


def pair(spec, r, *, calculate, factories, reserve, reserve_construction,
         save, check_continue):
    """Run two existing generated protocols, saving all outputs separately."""
    from lll.ilvis0_hybrid_fit_check import compare
    from lll.studies.artifacts import digest, encoded

    if not isinstance(spec, dict) or spec not in [row['payload'] for row in tasks(r)]:
        raise ValueError('declared generated paired-fit case required')
    if set(factories) != {'wide', 'hybrid'} or any(not callable(v) for v in factories.values()):
        raise ValueError('two explicit tangent factories required')
    results = {}
    recorded = {}
    for variant in ('wide', 'hybrid'):
        check_continue()
        artifacts = {}
        def saving(name, value):
            artifacts[name] = value
            save(variant + '-' + name, value)
        results[variant] = calculate(spec, r, kernel_factory=factories[variant],
                                     reserve=reserve,
                                     reserve_construction=reserve_construction,
                                     save=saving, check_continue=check_continue)
        recorded[variant] = artifacts
    needed = ('input-binding.json', 'scoring-observations.json', 'scores.json')
    if any(key not in recorded[variant] for variant in recorded for key in needed):
        raise ValueError('complete matched fit/forecast artifacts required')
    comparison = compare(
        results['wide'], results['hybrid'],
        recorded['wide']['input-binding.json'], recorded['hybrid']['input-binding.json'],
        recorded['wide']['scores.json']['errors_neu_m'],
        recorded['hybrid']['scores.json']['errors_neu_m'],
        tolerance_m=r['paired_prediction_tolerance_m'],
        reference_scoring_sha256=digest(encoded(recorded['wide']['scoring-observations.json'])),
        candidate_scoring_sha256=digest(encoded(recorded['hybrid']['scoring-observations.json'])))
    save('comparison.json', comparison)
    return dict(reference=results['wide'], candidate=results['hybrid'],
                comparison=comparison, passed=comparison['passed'],
                original_reads=0, protected_reads=0,
                scientific_decision='abstain')


def qualification_sources(root):
    from lll.studies.dependencies import source_closure
    return source_closure(root, [
        'analysis/lll/ilvis0_hybrid_fit_study.py',
        'analysis/lll/ilvis0_hybrid_fit_check.py',
        'analysis/tests/test_ilvis0_hybrid_fit_study.py',
        'analysis/tests/test_ilvis0_hybrid_fit_check.py',
        'analysis/tests/test_ilvis0_hybrid_tangent.py',
        'analysis/tests/run_numerical.py',
        'analysis/lll/ilvis0_tangent.cpp',
        'analysis/lll/ilvis0_native.c',
        'docs/mixed-tangent-hybrid/FULL_FIT_PLAN.md'])


def required_tests():
    return (
        'test_study_freezes_six_cases_and_two_finite_fit_allowances',
        'test_pair_uses_two_factories_and_preserves_matched_input_and_truth',
        'test_worker_rejects_changed_recipe_before_creating_artifacts',
        'test_report_rejects_unclosed_study',
        'test_preparation_requires_source_bound_tests_before_writing',
        'test_short_real_paired_fits_share_inputs_and_forecast',
        'test_matched_fits_pass_at_frozen_centimetre_threshold',
        'test_fits_reject_changed_inputs_and_silent_missing_epochs',
        'test_fits_reject_nonfinite_cost_and_forecast',
        'test_fits_fail_when_prediction_differs_or_one_fit_is_inadequate',
        'test_fits_reject_mismatched_cases',
        'test_fits_reject_different_withheld_truth',
        'test_hybrid_tangent_keeps_values_and_derivatives_across_six_generated_cases')


def prepare(root, *, qualification, identity='hybrid-paired-training-20261110'):
    """Freeze only a passing generated-data release and its finite allowances."""
    import re
    from pathlib import Path

    if qualification is None:
        raise ValueError('source-bound software qualification required before preparation')
    from lll.airquantumgrav_inventory import environment
    from lll.compute_budget import environment as threads
    from lll.ilvis0_wide_training import SOURCES, bind
    from lll.studies.artifacts import atomic, digest, encoded, safe_path
    from lll.studies.closed import ClosedStudy
    from lll.studies.qualification import checked
    from lll.studies.runtime import Definition

    root = Path(root).resolve()
    r = recipe()
    env = environment()
    if (not isinstance(identity, str)
            or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,95}', identity)
            or env['numerical_environment'] != threads(workers=r['workers'],
                                                        threads=r['threads'])):
        raise ValueError('safe identity and declared four-thread environment required')
    sources = qualification_sources(root)
    request, report = checked(root, qualification, sources=sources,
                              environment=env, required_tests=required_tests(),
                              minimum_tests=len(required_tests()))
    parent = ClosedStudy(root, 'data/hybrid-tangent-long-controls-20261110')
    try:
        if (len(parent.rows) != 6
                or parent.completion['manifest_sha256'] != PARENT_MANIFEST_SHA
                or parent.completion['summary_sha256'] != PARENT_SUMMARY_SHA
                or not all(parent.envelope(name)['result']['passed']
                           for name in parent.tasks)):
            raise ValueError('complete passing long-record kernel parent required')
        parent_proof = dict(manifest_sha256=parent.completion['manifest_sha256'],
                            summary_sha256=parent.completion['summary_sha256'],
                            six_long_cases_passed=True)
    finally:
        parent.close()
    base = safe_path(root, 'data/ilvis0-source-point-development/' + identity + '-inputs')
    if base.exists() or safe_path(root, 'data/' + identity).exists():
        raise ValueError('fresh paired-fit study identity required')
    hashes = {name: digest((root / 'analysis/lll' / name).read_bytes()) for name in SOURCES}
    _, _, binding = bind(expected_sources=hashes)
    base.mkdir(parents=True)
    values = (('recipe', encoded(r)), ('qualification-request', request),
              ('qualification-report', report),
              ('qualification-environment', encoded(env)),
              ('qualified-parent', encoded(parent_proof)),
              ('protocol-binding', encoded(binding)))
    inputs = {}
    for index, (name, value) in enumerate(values):
        path = base / f'input-{index:03d}'
        atomic(path, value)
        inputs[name] = str(path.relative_to(root))
    definition = dict(id=identity, scope=SCOPE,
                      adapter='analysis/lll/ilvis0_hybrid_fit_study.py',
                      sources=sources, inputs=inputs, tasks=tasks(r),
                      workers=r['workers'], threads=r['threads'],
                      maximum_wall_s=r['maximum_wall_s'])
    atomic(base / 'definition.json', encoded(definition))
    manifest = Definition.from_dict(definition, root).prepare(root)
    return dict(path='data/' + identity, cases=len(tasks(r)),
                allocation=manifest['allocation'], limits=manifest['limits'])


def evaluate(task, context):
    """Execute one frozen generated pair with unchanged scientific inputs."""
    from lll.airquantumgrav_inventory import environment
    from lll.ilvis0_control_shards import _check_continue
    from lll.ilvis0_exploratory import load_kernel
    from lll.ilvis0_hybrid_tangent import load as hybrid_load
    from lll.ilvis0_wide_tangent import load as wide_load
    from lll.ilvis0_wide_training import SOURCES, bind
    from lll.studies.artifacts import digest
    from lll.studies.journal import Journal

    r = recipe()
    env = environment()
    declared = {key: value for key, value in task.items()
                if key not in ('index', 'shard')}
    known = {row['identity']: row for row in tasks(r)}
    read = lambda key: json.loads(context.input_path(key).read_bytes())
    if (declared != known.get(task['identity']) or read('recipe') != r
            or read('qualification-environment') != env
            or context.manifest['scope'] != SCOPE
            or any(context.manifest['sources'].get(name) != sha
                   for name, sha in read('qualification-request')['sources'].items())):
        raise ValueError('unchanged source-qualified generated pair required')
    parent_proof = read('qualified-parent')
    if (parent_proof.get('six_long_cases_passed') is not True
            or parent_proof.get('manifest_sha256') != PARENT_MANIFEST_SHA
            or parent_proof.get('summary_sha256') != PARENT_SUMMARY_SHA):
        raise ValueError('qualified long-record parent differs from frozen proof')
    hashes = context.manifest['sources']
    _, calculate, binding = bind(expected_sources={
        name: hashes['analysis/lll/' + name] for name in SOURCES})
    if binding != read('protocol-binding'):
        raise ValueError('explicit prediction protocol binding changed')
    context.save('protocol-binding.json', binding)
    identity = task['identity']
    limits = construction_limits(r)
    journal = Journal(context.directory / 'construction.sqlite',
                      freeze=digest((context.root / 'manifest.json').read_bytes()),
                      limits={identity: limits})
    journal.start(identity)
    directory = context.root / 'shards' / f'{context.shard:03d}' / 'kernels'

    def check():
        _check_continue(context.root, context.manifest)

    def reserve_construction(**work):
        check()
        for key, value in work.items():
            journal.reserve(identity, key, value)

    def factory(variant):
        def build(anchor):
            check()
            value, vm = load_kernel(directory, gravity_anchor_height_m=anchor)
            if variant == 'wide':
                tangent, tm = wide_load(directory, gravity_anchor_height_m=anchor,
                    expected_source_sha256=hashes['analysis/lll/ilvis0_tangent.cpp'])
            else:
                tangent, tm = hybrid_load(directory, gravity_anchor_height_m=anchor,
                    expected_source_sha256=hashes['analysis/lll/ilvis0_tangent.cpp'],
                    expected_loader_sha256=hashes['analysis/lll/ilvis0_wide_tangent.py'])
            if (vm['source_sha256'] != hashes['analysis/lll/ilvis0_native.c']
                    or vm['compiler'] != env['compilers']['cc']
                    or tm['compiler'] != env['compilers']['c++']):
                raise ValueError('unchanged native sources and compilers required')
            binary = directory / ('wide-tangent-' + tm['source_sha256'] + '.so')
            contents = binary.read_bytes()
            if digest(contents) != tm['binary_sha256']:
                raise ValueError('compiled tangent hash differs')
            context.save_bytes(variant + '-kernel.bin', contents)
            return value, tangent, dict(value=vm, tangent=tm, variant=variant)
        return build

    try:
        result = pair(task['payload'], r, calculate=calculate,
                      factories={name: factory(name) for name in ('wide', 'hybrid')},
                      reserve=context.charge, reserve_construction=reserve_construction,
                      save=context.save, check_continue=check)
        journal.verify()
        if any(journal.count(identity, key) != value for key, value in limits.items()):
            raise ValueError('paired generated construction charges differ')
        return result
    finally:
        context.note_file(journal.path)


def inspect(root, prefix='data/hybrid-paired-training-20261110'):
    """Recheck sealed paired forecasts and charges without executing a fit."""
    from lll.airquantumgrav_geographic_report import construction_counts
    from lll.airquantumgrav_inventory import environment
    from lll.ilvis0_hybrid_fit_check import compare
    from lll.studies.artifacts import digest, encoded
    from lll.studies.closed import ClosedStudy
    from lll.studies.source_binding import verify

    study = ClosedStudy(root, prefix)
    try:
        r = study.input('recipe')
        if (r != recipe() or study.manifest['scope'] != SCOPE
                or study.input('qualification-environment') != environment()
                or set(study.tasks) != {row['identity'] for row in tasks(r)}):
            raise ValueError('complete unchanged generated paired-fit scope required')
        verify(root, declared=study.input('qualification-request')['sources'],
               manifest=study.manifest['sources'])
        rows = []
        for task in tasks(r):
            identity = task['identity']
            if identity not in study.rows:
                rows.append(dict(identity=identity, complete=False))
                continue
            envelope = study.envelope(identity)
            result = envelope['result']
            if (result['original_reads'] or result['protected_reads']
                    or result['scientific_decision'] != 'abstain'):
                raise ValueError('generated-only result required')
            artifacts = {}
            for variant in ('wide', 'hybrid'):
                artifacts[variant] = {name: study.artifact(identity, variant + '-' + name)
                                      for name in ('input-binding.json',
                                                   'scoring-observations.json',
                                                   'scores.json', 'compilation.json')}
                binary = study.artifact(identity, variant + '-kernel.bin', raw=True)
                if (digest(binary) != artifacts[variant]['compilation.json']
                        ['tangent']['binary_sha256']):
                    raise ValueError('compiled paired tangent binary differs')
            left, right = (artifacts[name] for name in ('wide', 'hybrid'))
            report = compare(
                result['reference'], result['candidate'],
                left['input-binding.json'], right['input-binding.json'],
                left['scores.json']['errors_neu_m'], right['scores.json']['errors_neu_m'],
                tolerance_m=r['paired_prediction_tolerance_m'],
                reference_scoring_sha256=digest(encoded(left['scoring-observations.json'])),
                candidate_scoring_sha256=digest(encoded(right['scoring-observations.json'])))
            if (encoded(report) != encoded(result['comparison'])
                    or encoded(report) != encoded(study.artifact(identity, 'comparison.json'))
                    or result['passed'] != report['passed']
                    or envelope['charged']['native_calls'] !=
                    result['reference']['native_calls'] + result['candidate']['native_calls']):
                raise ValueError('saved paired-fit comparison or charge differs')
            path = 'artifacts/' + identity + '/construction.sqlite'
            limits = construction_limits(r)
            counts = construction_counts(
                study.read(path, envelope['artifacts'][path], raw=True),
                study.completion['manifest_sha256'], identity, limits)
            rows.append(dict(identity=identity, complete=True, passed=report['passed'],
                             comparison=report, construction_counts=counts))
        return dict(verified=True, qualified=all(row.get('passed', False) for row in rows),
                    complete=sum(row['complete'] for row in rows), total=len(rows),
                    rows=rows, manifest_sha256=study.completion['manifest_sha256'],
                    summary_sha256=study.completion['summary_sha256'],
                    scientific_decision='abstain')
    finally:
        study.close()
