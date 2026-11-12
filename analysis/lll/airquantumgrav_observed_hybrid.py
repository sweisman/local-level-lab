# SPDX-License-Identifier: AGPL-3.0-or-later
"""Source-bound selective-tangent check on the saved ESA development interval."""

from lll.airquantumgrav_inventory import METADATA, environment, validate_context
from lll.airquantumgrav_observed_height import UNCHANGED_INPUTS, require_qualification
from lll.airquantumgrav_observed_wide import tasks as wide_tasks

SCOPE = ('observed ESA recording-187 selective-tangent substitution; '
         'saved development inputs only; no original or protected reads')
PARENTS = {
    'wide': ('docs/esa-observed-wide-pilot',
             '73aa91117d60ca191f614f0fe826167e8b237fcff320b7676e2f505fd1bf6289',
             '2ce3ae7c4e48adb8d5d3048316a68d88a3015ff1528a3515bb212d1081e15f31', 22),
    'long': ('data/hybrid-long-paired-training-20261110-v2',
             'f4d8609c51a918493d1b9b0a83c719201b49426fe2d98938451bfbfa7f4ee956',
             '2df075a347a694e908608306bd05ed384602fd53b9c2bc3739d4af74521689f8', 6),
    'timed': ('data/hybrid-timed-paired-training-20261110',
              '07306cebe3acd71c37a54813e2c8b1ea22298df8a873a043bbbeb1561ec2eb6c',
              '0b14a4f3c0b5767139f71ac5cf45704873281c6c78fcdf6f1f5e71b6d8940cbb', 6),
}


def recipe(*, maximum_wall_s):
    import math
    from lll.airquantumgrav_observed_wide import recipe as wide_recipe
    if (type(maximum_wall_s) not in (int, float)
            or not math.isfinite(maximum_wall_s)
            or not 0 < maximum_wall_s <= 57600):
        raise ValueError('explicit finite paired allowance at most sixteen hours required')
    return dict(wide_recipe(maximum_wall_s=min(maximum_wall_s, 28800)),
                version='esa-observed-hybrid-paired-v1',
                maximum_wall_s=float(maximum_wall_s))


def tasks(layout):
    cases = wide_tasks(layout)
    return [dict(case, limits=dict(case['limits'],
                                   native_calls=2 * case['limits']['native_calls'],
                                   packet_visits=2 * case['limits']['packet_visits']))
            for case in cases]


def verify_parent(name, manifest_sha256, summary_sha256, *, six_passed):
    if (name not in PARENTS or manifest_sha256 != PARENTS[name][1]
            or summary_sha256 != PARENTS[name][2] or six_passed is not True):
        raise ValueError('qualified unchanged parent completion required')


def parent_proof(root):
    from lll.studies.closed import ClosedStudy

    proof = {}
    for name, (path, manifest, summary, count) in PARENTS.items():
        parent = ClosedStudy(root, path)
        try:
            passed = sum(bool(parent.envelope(identity)['result'].get('passed'))
                         for identity in parent.rows)
            valid = len(parent.rows) == (24 if name == 'wide' else 6) and passed == count
            verify_parent(name, parent.completion['manifest_sha256'],
                          parent.completion['summary_sha256'], six_passed=valid)
            proof[name] = dict(manifest_sha256=manifest,
                               summary_sha256=summary,
                               rows=len(parent.rows), passed=passed)
        finally:
            parent.close()
    return proof


def qualification_sources(root):
    from lll.ilvis0_wide_observed import SOURCES
    from lll.studies.dependencies import source_closure

    return source_closure(root, [
        'analysis/lll/airquantumgrav_observed_hybrid.py',
        'analysis/lll/airquantumgrav_observed_hybrid_report.py',
        'analysis/tests/test_airquantumgrav_observed_hybrid.py',
        'analysis/tests/test_airquantumgrav_observed_hybrid_report.py',
        'analysis/lll/ilvis0_hybrid_tangent.py',
        'analysis/lll/ilvis0_wide_tangent.py',
        'analysis/lll/ilvis0_native.c',
        'analysis/lll/ilvis0_tangent.cpp',
        'analysis/tests/run_numerical.py',
        'docs/esa-observed-hybrid/PLAN.md',
        *['analysis/lll/' + name for name in SOURCES],
    ])


def required_tests():
    from lll.airquantumgrav_observed_wide import required_tests as wide_tests

    return wide_tests() + [
        'test_hybrid_observed_recipe_preserves_wide_scientific_matrix',
        'test_hybrid_observed_requires_qualification_before_inputs',
        'test_hybrid_observed_adapter_loads_directly_and_freezes_sources',
        'test_hybrid_observed_only_expected_parent_hashes_pass',
        'test_hybrid_saved_pair_accepts_identical_positions_and_classification',
        'test_hybrid_saved_pair_rejects_tiny_angle_but_large_ground_distance',
        'test_hybrid_saved_pair_requires_every_nuisance_column_and_same_decisions',
        'test_hybrid_report_rejects_unclosed_study',
        'test_hybrid_report_rejects_failed_or_incomplete_qualification',
    ]


def prepare(root, *, qualification, maximum_wall_s,
            identity='esa-observed-hybrid-pilot-20261110'):
    return prepare_variant(root, qualification=qualification,
                           maximum_wall_s=maximum_wall_s, identity=identity,
                           recipe_fn=recipe, task_fn=tasks,
                           sources_fn=qualification_sources,
                           required_fn=required_tests, expected_tasks=24,
                           scope=SCOPE,
                           adapter='analysis/lll/airquantumgrav_observed_hybrid.py')


def prepare_variant(root, *, qualification, maximum_wall_s, identity,
                    recipe_fn, task_fn, sources_fn, required_fn,
                    expected_tasks, scope, adapter, extra_inputs=None):
    """Reuse the source-bound observed input preparation across tangent variants."""
    if qualification is None:
        raise ValueError('source-bound qualification required before input preparation')
    import json
    import re
    from pathlib import Path
    from lll.compute_budget import environment as thread_environment
    from lll.ilvis0_wide_observed import SOURCES, bind
    from lll.studies.artifacts import atomic, digest, encoded, safe_path
    from lll.studies.closed import ClosedStudy
    from lll.studies.qualification import checked
    from lll.studies.runtime import Definition

    r = recipe_fn(maximum_wall_s=maximum_wall_s)
    env = environment()
    if env['numerical_environment'] != thread_environment(
            workers=r['workers'], threads=r['threads']):
        raise ValueError('declared numerical environment required')
    root = Path(root).resolve()
    if not isinstance(identity, str) or not re.fullmatch(
            r'[A-Za-z0-9][A-Za-z0-9_.-]{0,95}', identity):
        raise ValueError('safe fresh study identity required')
    base = safe_path(root, 'data/ilvis0-source-point-development/' + identity + '-inputs')
    if base.exists() or safe_path(root, 'data/' + identity).exists():
        raise ValueError('fresh observed allowance required')
    sources = sources_fn(root)
    request, tests = checked(root, qualification, sources=sources,
                             environment=env, required_tests=required_fn(),
                             minimum_tests=60)
    parents = parent_proof(root)
    baseline = ClosedStudy(root, PARENTS['wide'][0])
    try:
        copied = {key: baseline.input(key, raw=True)
                  for key in baseline.manifest['inputs']
                  if key not in ('recipe', 'qualification-request',
                                 'qualification-report', 'qualification-environment',
                                 'protocol-binding')}
        old_hashes = {key: baseline.manifest['inputs'][key]['sha256'] for key in copied}
        if (not set(UNCHANGED_INPUTS) <= set(copied)
                or not set(METADATA) <= set(copied)
                or any(digest(value) != old_hashes[key] for key, value in copied.items())):
            raise ValueError('published prepared inputs differ from frozen hashes')
        layout = json.loads(copied['layout'])
        if len(task_fn(layout)) != expected_tasks:
            raise ValueError('unchanged selected task matrix required')
        binding = json.loads(copied['baseline-binding'])
        if binding['unchanged_input_sha256'] != {
                key: old_hashes[key] for key in UNCHANGED_INPUTS}:
            raise ValueError('unchanged original measurements and split required')
        require_qualification(json.loads(copied['qualified-controls']))
        metadata = {key: json.loads(copied[key]) for key in METADATA}
        if validate_context(**metadata) != json.loads(copied['context']):
            raise ValueError('prepared ESA development membership changed')
    finally:
        baseline.close()
    _, protocol = bind(expected_sources={
        name: digest((root / 'analysis/lll' / name).read_bytes()) for name in SOURCES})
    materials = dict(copied, recipe=encoded(r))
    materials['protocol-binding'] = encoded(protocol)
    materials['qualification-environment'] = encoded(env)
    materials['parent-proof'] = encoded(parents)
    materials['qualification-request'] = request
    materials['qualification-report'] = tests
    if extra_inputs is not None:
        for key, raw in extra_inputs(root).items():
            if key in materials:
                raise ValueError('variant input collides with prepared evidence')
            materials[key] = raw
    base.mkdir(parents=True)
    inputs = {}
    for index, (key, raw) in enumerate(materials.items()):
        path = base / f'input-{index:03d}'
        atomic(path, raw)
        inputs[key] = str(path.relative_to(root))
    definition = dict(id=identity, scope=scope,
                      adapter=adapter,
                      sources=sources, inputs=inputs, tasks=task_fn(layout),
                      workers=r['workers'], threads=r['threads'],
                      maximum_wall_s=r['maximum_wall_s'])
    atomic(base / 'definition.json', encoded(definition))
    manifest = Definition.from_dict(definition, root).prepare(root)
    return dict(path='data/' + identity, total=expected_tasks,
                limits=manifest['limits'], allocation=manifest['allocation'])


def evaluate(task, context):
    from lll.ilvis0_hybrid_tangent import load as load_hybrid
    return evaluate_variant(task, context, load_hybrid=load_hybrid,
                            recipe_fn=recipe, task_fn=tasks, scope=SCOPE)


def evaluate_variant(task, context, *, load_hybrid, recipe_fn, task_fn, scope,
                     expected_precision_revision=None):
    """Run paired methods with an explicit frozen tangent loader."""
    import gzip
    import json
    import numpy as np
    from lll.ilvis0_control_shards import _check_continue
    from lll.ilvis0_exploratory import load_kernel
    from lll.ilvis0_wide_tangent import load as load_wide
    from lll.ilvis0_wide_observed import SOURCES, bind
    from lll.airquantumgrav_observed_hybrid_report import compare_pair

    read = lambda key: json.loads(context.input_path(key).read_bytes())
    r = read('recipe')
    layout = read('layout')
    declared = {key: value for key, value in task.items()
                if key not in ('index', 'shard')}
    if (r != recipe_fn(maximum_wall_s=r['maximum_wall_s'])
            or context.manifest['scope'] != scope
            or {case['identity']: case for case in task_fn(layout)}.get(task['identity']) != declared
            or read('qualification-environment') != environment()
            or read('parent-proof') != {
                name: dict(manifest_sha256=info[1], summary_sha256=info[2],
                           rows=24 if name == 'wide' else 6, passed=info[3])
                for name, info in PARENTS.items()}):
        raise ValueError('unchanged source-bound observed substitution required')
    require_qualification(read('qualified-controls'))
    if read('baseline-binding')['unchanged_input_sha256'] != {
            key: context.manifest['inputs'][key]['sha256'] for key in UNCHANGED_INPUTS}:
        raise ValueError('published prepared measurements or split changed')
    binding = validate_context(**{key: read(key) for key in METADATA})
    if binding != read('context'):
        raise ValueError('ESA development membership changed')
    calculate, protocol = bind(expected_sources={
        name: context.manifest['sources']['analysis/lll/' + name]
        for name in SOURCES})
    if protocol != read('protocol-binding'):
        raise ValueError('observed protocol binding changed')
    context.save('protocol-binding.json', protocol)
    with np.load(context.input_path(), allow_pickle=False) as archive:
        arrays = {key: archive[key] for key in ('theta', 'dv', 'dt')}
    query = read('query-layout')
    training = json.loads(gzip.decompress(context.input_path('training').read_bytes()))
    count = int(np.searchsorted(np.cumsum(arrays['dt']),
                                query['times_s'][799] + r['limits']['time_offset'],
                                side='left')) + 1
    if (len(arrays['dt']) != layout['native_packets']
            or count != layout['training_prefix_packets']
            or len(training) != 800 or len(query['times_s']) != 1200):
        raise ValueError('unchanged prepared packets and earlier prefix required')
    input_binding = dict(
        group_id=binding['group_id'], layout=layout,
        input_sha256={key: value['sha256']
                      for key, value in context.manifest['inputs'].items()},
        original_reads=0, protected_reads=0)
    env = environment()
    results = {}
    saved = {}
    for variant, load_tangent in (('wide', load_wide), ('hybrid', load_hybrid)):
        directory = (context.root / 'shards' / f'{context.shard:03d}' /
                     'kernels' / variant)
        context.save(variant + '-input-binding.json', input_binding)
        saved[variant] = {}

        def save(name, value):
            context.save(variant + '-' + name, value)
            saved[variant][name] = value

        def factory(anchor):
            value, vm = load_kernel(directory, gravity_anchor_height_m=anchor)
            kwargs = dict(gravity_anchor_height_m=anchor,
                          expected_source_sha256=context.manifest['sources'][
                              'analysis/lll/ilvis0_tangent.cpp'])
            if variant == 'hybrid':
                kwargs['expected_loader_sha256'] = context.manifest['sources'][
                    'analysis/lll/ilvis0_wide_tangent.py']
            tangent, tm = load_tangent(directory, **kwargs)
            if (vm['source_sha256'] != context.manifest['sources'][
                    'analysis/lll/ilvis0_native.c']
                    or vm['compiler'] != env['compilers']['cc']
                    or tm['compiler'] != env['compilers']['c++']
                    or (variant == 'hybrid'
                        and tm.get('shared_loader_unchanged') is not True)):
                raise ValueError('frozen native source and compilers required')
            if (variant == 'hybrid' and expected_precision_revision is not None
                    and tm.get('precision_revision') != expected_precision_revision):
                raise ValueError('revised tangent precision metadata differs')
            return value, tangent, dict(value=vm, tangent=dict(
                tm, gravity_model=r['gravity_model']))

        result = calculate(
            task['payload'], r, arrays=arrays, training_rows=training,
            layout=query,
            open_scoring=lambda: json.loads(gzip.decompress(
                context.input_path('scoring').read_bytes())),
            kernel_factory=factory, reserve=context.charge, save=save,
            check_continue=lambda: _check_continue(context.root, context.manifest))
        if result['weight_configuration'] != read('working-errors')[
                task['payload']['policy_id']]['configuration']:
            raise ValueError('training weights differ from prepared source')
        results[variant] = dict(result, group_id=binding['group_id'])
    if results['wide']['passed'] and results['hybrid']['passed']:
        comparison = compare_pair(
            results['wide'], results['hybrid'],
            saved['wide']['fit.json'], saved['hybrid']['fit.json'],
            saved['wide']['forecast.json'], saved['hybrid']['forecast.json'],
            tolerance_m=.01)
    else:
        comparison = dict(passed=False,
                          reason='at least one matched numerical fit did not qualify')
    context.save('comparison.json', comparison)
    return dict(passed=comparison['passed'], wide=results['wide'],
                hybrid=results['hybrid'], comparison=comparison,
                original_reads=0, protected_reads=0,
                scientific_decision='abstain')
