# SPDX-License-Identifier: AGPL-3.0-or-later
"""Shared lifecycle for source-bound paired training and forecast studies."""
import json
from pathlib import Path
import re


def prepare(root, *, qualification, identity, recipe, scope, sources,
            required_tests, parent_proof, adapter, tasks):
    from lll.airquantumgrav_inventory import environment
    from lll.compute_budget import environment as thread_environment
    from lll.ilvis0_wide_training import SOURCES, bind
    from lll.studies.artifacts import atomic, digest, encoded, safe_path
    from lll.studies.qualification import checked
    from lll.studies.runtime import Definition

    if qualification is None:
        raise ValueError('source-bound software qualification required before preparation')
    root = Path(root).resolve()
    r = recipe()
    env = environment()
    if (not isinstance(identity, str)
            or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,95}', identity)
            or env['numerical_environment'] != thread_environment(
                workers=r['workers'], threads=r['threads'])):
        raise ValueError('safe identity and declared four-thread environment required')
    request, report = checked(root, qualification, sources=sources,
                              environment=env, required_tests=required_tests,
                              minimum_tests=len(required_tests))
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
    definition = dict(id=identity, scope=scope, adapter=adapter,
                      sources=sources, inputs=inputs, tasks=tasks(r),
                      workers=r['workers'], threads=r['threads'],
                      maximum_wall_s=r['maximum_wall_s'])
    atomic(base / 'definition.json', encoded(definition))
    manifest = Definition.from_dict(definition, root).prepare(root)
    return dict(path='data/' + identity, cases=len(tasks(r)),
                allocation=manifest['allocation'], limits=manifest['limits'])


def evaluate(task, context, *, recipe, scope, parent_proof, tasks,
             construction_limits, pair):
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
            or context.manifest['scope'] != scope
            or any(context.manifest['sources'].get(name) != sha
                   for name, sha in read('qualification-request')['sources'].items())):
        raise ValueError('unchanged source-qualified generated pair required')
    if read('qualified-parent') != parent_proof:
        raise ValueError('qualified parent differs from frozen proof')
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


def inspect(root, prefix, *, recipe, scope, parent_proof, tasks,
            construction_limits):
    from lll.airquantumgrav_geographic_report import construction_counts
    from lll.airquantumgrav_inventory import environment
    from lll.ilvis0_hybrid_fit_check import compare
    from lll.studies.artifacts import digest, encoded
    from lll.studies.closed import ClosedStudy
    from lll.studies.source_binding import verify

    study = ClosedStudy(root, prefix)
    try:
        r = study.input('recipe')
        if (r != recipe() or study.manifest['scope'] != scope
                or study.input('qualified-parent') != parent_proof
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
