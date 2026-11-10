# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite generated long-record gate for selective derivative precision."""
import json
from pathlib import Path

from lll.ilvis0_mixed_benchmark import calculate, checks, construction_limits
from lll.ilvis0_mixed_benchmark import recipe as reference_recipe
from lll.ilvis0_mixed_benchmark import tasks as reference_tasks


SCOPE = 'generated selective-precision long-record comparison; no observed or protected inputs'


def recipe():
    return dict(reference_recipe(), version='hybrid-tangent-long-controls-v1')


def tasks():
    return reference_tasks()


def evaluate(task, context):
    from lll.airquantumgrav_inventory import environment
    from lll.ilvis0_control_shards import _check_continue
    from lll.ilvis0_hybrid_tangent import load
    from lll import ilvis0_wide_tangent as reference
    from lll.studies.artifacts import digest
    from lll.studies.journal import Journal

    expected = {row['identity']: row for row in tasks()}
    payload = {k: v for k, v in task.items() if k not in ('index', 'shard')}
    read = lambda key: json.loads(context.input_path(key).read_bytes())
    r = recipe()
    if (expected.get(task['identity']) != payload or read('recipe') != r
            or read('qualification-environment') != environment()
            or context.manifest['scope'] != SCOPE
            or any(context.manifest['sources'].get(name) != sha
                   for name, sha in read('qualification-request')['sources'].items())):
        raise ValueError('unchanged qualified selective-precision benchmark required')
    journal = Journal(context.directory/'construction.sqlite',
                      freeze=digest((context.root/'manifest.json').read_bytes()),
                      limits={task['identity']: construction_limits(r)})
    journal.start(task['identity'])
    try:
        def check():
            _check_continue(context.root, context.manifest)

        def reserve(**work):
            check()
            for key, value in work.items():
                journal.reserve(task['identity'], key, value)

        def factory(anchor):
            directory = context.root/'shards'/f'{context.shard:03d}'/'kernels'
            sources = context.manifest['sources']
            original_sha = sources['analysis/lll/ilvis0_tangent.cpp']
            loader_sha = sources['analysis/lll/ilvis0_wide_tangent.py']
            wide, wide_meta = reference.load(directory, gravity_anchor_height_m=anchor,
                                             expected_source_sha256=original_sha)
            hybrid, hybrid_meta = load(directory, gravity_anchor_height_m=anchor,
                                       expected_source_sha256=original_sha,
                                       expected_loader_sha256=loader_sha)
            for name, metadata in (('reference', wide_meta), ('candidate', hybrid_meta)):
                binary = directory/('wide-tangent-' + metadata['source_sha256'] + '.so')
                context.save_bytes(name + '-kernel.bin', binary.read_bytes())
            return dict(reference=wide, candidate=hybrid), dict(
                reference=wide_meta, candidate=hybrid_meta)

        result = calculate(task['payload'], r, kernel_factory=factory,
                           reserve=context.charge, reserve_construction=reserve,
                           save=context.save, save_bytes=context.save_bytes,
                           check_continue=check)
        journal.verify()
        if any(journal.count(task['identity'], key) != value
               for key, value in construction_limits(r).items()):
            raise ValueError('generated construction charges differ')
        return result
    finally:
        context.note_file(journal.path)


def inspect(root, prefix='data/hybrid-tangent-long-controls-20261110'):
    """Recheck sealed arrays and resource charges without native calculations."""
    from lll.studies.closed import ClosedStudy
    study = ClosedStudy(root, prefix)
    try:
        import io
        import numpy as np
        from lll.airquantumgrav_inventory import environment
        from lll.studies.artifacts import digest, encoded
        from lll.studies.source_binding import verify

        r = study.input('recipe')
        if (r != recipe() or study.manifest['scope'] != SCOPE
                or study.input('qualification-environment') != environment()
                or set(study.tasks) != {row['identity'] for row in tasks()}):
            raise ValueError('complete unchanged selective-precision scope required')
        verify(root, declared=study.input('qualification-request')['sources'],
               manifest=study.manifest['sources'])
        rows = []
        for spec in tasks():
            identity = spec['identity']
            if identity not in study.rows:
                rows.append(dict(identity=identity, complete=False))
                continue
            envelope = study.envelope(identity)
            result = envelope['result']
            descriptor = study.artifact(identity, 'comparison.json')
            with np.load(io.BytesIO(study.artifact(identity, 'comparison.npz', raw=True)),
                         allow_pickle=False) as archive:
                arrays = {key: archive[key] for key in archive.files}
            tested = checks(arrays, boundaries=[descriptor['boundaries'][name]
                                                for name in ('reference', 'candidate')])
            if (encoded(tested) != encoded(result['checks'])
                    or encoded(tested) != encoded(descriptor['checks'])
                    or result['passed'] != tested['passed']
                    or any(result[key] for key in ('optimizer_starts', 'original_reads', 'protected_reads'))
                    or result['native_calls'] != 2 or result['packet_visits'] != 864_000_000
                    or envelope['charged']['native_calls'] != 2
                    or envelope['charged']['packet_visits'] != 864_000_000
                    or descriptor['query_epochs'] != 1200 or descriptor['native_packets'] != 360000):
                raise ValueError('sealed hybrid comparison or charged work differs')
            compilation = study.artifact(identity, 'compilation.json')
            for name in ('reference', 'candidate'):
                meta = compilation[name]
                binary = study.artifact(identity, name + '-kernel.bin', raw=True)
                if meta['binary_sha256'] != digest(binary):
                    raise ValueError('compiled kernel hash differs')
            rows.append(dict(identity=identity, complete=True, passed=tested['passed'],
                             checks=tested, cpu_speed_ratio=(
                                 descriptor['timing']['reference']['cpu_s'] /
                                 descriptor['timing']['candidate']['cpu_s'])))
        return dict(verified=True, rows=rows, total=6,
                    complete=sum(row['complete'] for row in rows),
                    qualified=all(row.get('passed', False) for row in rows),
                    manifest_sha256=study.completion['manifest_sha256'],
                    summary_sha256=study.completion['summary_sha256'],
                    scientific_decision='abstain')
    finally:
        study.close()
