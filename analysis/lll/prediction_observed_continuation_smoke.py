# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check a no-refit receiver bound against the sealed generated control."""

import argparse
from io import BytesIO
import gzip
import json
from pathlib import Path
from tempfile import TemporaryDirectory


def verify(root):
    """Use only the original generated inputs and saved earlier-only evidence."""
    import numpy as np

    from .airquantumgrav_inventory import environment
    from .ilvis0_noise_step import load as load_noise
    from .ilvis0_wide_tangent import load as load_tangent
    from .prediction_observed_continuation import (
        assemble_saved_laws, rebuild_native_point_bound)
    from .prediction_observed_development_study import (
        SMOKE_ID, smoke_recipe, smoke_task)
    from .prediction_observed_material import bind
    from .prediction_observed_scoring import score_recording
    from .studies.artifacts import digest, encoded, reports_equal
    from .studies.closed import ClosedStudy

    root = Path(root).resolve()
    closed = ClosedStudy(root, 'data/'+SMOKE_ID)
    try:
        task = smoke_task()
        identity = task['identity']
        if (closed.completion['state'] != 'complete' or
                closed.summary['passed'] is not True or
                closed.manifest['scope'] !=
                    'one short generated source-bound two-law forecast and receiver score' or
                closed.manifest['tasks'][0]['identity'] != identity or
                closed.input('numerical_environment') != environment()):
            raise ValueError('complete frozen generated control and environment required')
        sources = closed.manifest['sources']
        for name in ('analysis/lll/ilvis0_tangent.cpp',
                     'analysis/lll/ilvis0_noise_bridge.cpp',
                     'analysis/lll/ilvis0_wide_tangent.py'):
            if sources[name] != digest((root/name).read_bytes()):
                raise ValueError('native source changed since sealed control')
        recipe = closed.input('recipe')
        if recipe != smoke_recipe():
            raise ValueError('generated recipe changed since sealed control')
        with np.load(BytesIO(closed.input('interval', raw=True)),
                     allow_pickle=False) as archive:
            arrays = {key: archive[key] for key in ('theta', 'dv', 'dt')}
        material = bind(
            arrays=arrays, layout=closed.input('layout'),
            training_rows=json.loads(gzip.decompress(
                closed.input('training', raw=True))),
            frozen_hashes=closed.input('frozen-hashes'),
            source_id='generated-worker-smoke',
            maximum_interval_s=recipe['maximum_interval_s'],
            time_offset_bound_s=recipe['limits']['time_offset'])
        saved = {name: closed.artifact(identity, name) for name in (
            'input-binding.json', 'point/fit.json',
            'point/forecast.json', 'point/simultaneous-bounded-physical.json',
            'point/training-error-operator.json')}
        counts = dict(native_calls=0, packet_visits=0)

        def reserve(**work):
            if not set(work) <= set(counts):
                raise ValueError('unexpected numerical charge')
            for name, amount in work.items():
                if type(amount) is not int or amount < 0:
                    raise ValueError('invalid numerical charge')
                counts[name] += amount
            if (counts['native_calls'] > 10_000 or
                    counts['packet_visits'] > 1_000_000):
                raise ValueError('generated no-refit allowance exceeded')

        builds = []
        captured = {}

        def save(name, value):
            if name in captured:
                raise ValueError('duplicate generated continuation artifact')
            captured[name] = value

        with TemporaryDirectory(prefix='lll-continuation-smoke-') as directory:
            noise, _ = load_noise(
                directory,
                expected_source_sha256=sources['analysis/lll/ilvis0_tangent.cpp'],
                expected_bridge_sha256=sources['analysis/lll/ilvis0_noise_bridge.cpp'],
                expected_wide_loader_sha256=sources['analysis/lll/ilvis0_wide_tangent.py'],
                reserve_build=lambda: builds.append('noise'))
            tangent, _ = load_tangent(
                directory,
                gravity_anchor_height_m=material['training_rows'][0]['height_m'],
                expected_source_sha256=sources['analysis/lll/ilvis0_tangent.cpp'])
            diagnostic = rebuild_native_point_bound(
                saved['input-binding.json'], saved['point/fit.json'],
                saved['point/forecast.json'],
                saved['point/simultaneous-bounded-physical.json'],
                spec=task['payload'], recipe=recipe, material=material,
                kernel=None, tangent_kernel=tangent, noise_kernel=noise,
                reserve=reserve, save=save, check_continue=lambda: None,
                training_operator=saved['point/training-error-operator.json'])
        if set(captured) != {'simultaneous-bounded-receiver.json'}:
            raise ValueError('exactly the missing receiver bound required')
        expected_bound = closed.artifact(
            identity, 'point/simultaneous-bounded-receiver.json')
        expected_diagnostic = closed.artifact(
            identity, 'point/receiver-error-diagnostic.json')
        actual_diagnostic = json.loads(json.dumps(
            diagnostic, default=lambda value: value.tolist(), allow_nan=False))
        if (not reports_equal(captured['simultaneous-bounded-receiver.json'],
                              expected_bound) or
                not reports_equal(actual_diagnostic, expected_diagnostic)):
            raise ValueError('no-refit receiver bound differs from sealed control')
        fits = {'point': saved['point/fit.json'],
                'increment': closed.artifact(identity, 'increment/fit.json')}
        forecasts = {'point': saved['point/forecast.json'],
                     'increment': closed.artifact(
                         identity, 'increment/forecast.json')}
        physical = {'point': saved['point/simultaneous-bounded-physical.json'],
                    'increment': closed.artifact(
                        identity, 'increment/simultaneous-bounded-physical.json')}
        receiver = {'point': captured['simultaneous-bounded-receiver.json'],
                    'increment': closed.artifact(
                        identity, 'increment/simultaneous-bounded-receiver.json')}
        diagnostics = {'point': actual_diagnostic,
                       'increment': closed.artifact(
                           identity, 'increment/receiver-error-diagnostic.json')}
        assembled = {}
        reads = []

        def save_assembled(name, value):
            if name in assembled:
                raise ValueError('duplicate assembled artifact')
            assembled[name] = value

        def open_scoring():
            if not {'union-simultaneous-bounded-physical.json',
                    'union-simultaneous-bounded-receiver.json'} <= set(assembled):
                raise ValueError('withheld positions opened before both unions')
            reads.append('scoring')
            return json.loads(gzip.decompress(closed.input('scoring', raw=True)))

        result = assemble_saved_laws(
            saved['input-binding.json'], fits=fits, forecasts=forecasts,
            physical_bounds=physical, receiver_bounds=receiver,
            receiver_diagnostics=diagnostics,
            minimum_simultaneous_coverage=1-recipe['simultaneous_alpha'],
            save=save_assembled, open_scoring=open_scoring)
        score = score_recording(
            result, training_rows=material['training_rows'],
            times=material['times'], time_origin_s=material['time_origin_s'],
            save=save_assembled)
        expected_names = ('training-law-comparison.json',
                          'union-simultaneous-bounded-physical.json',
                          'union-simultaneous-bounded-receiver.json',
                          'withheld-receiver-score.json')
        if (reads != ['scoring'] or
                any(not reports_equal(assembled[name],
                                      closed.artifact(identity, name))
                    for name in expected_names) or
                not reports_equal(score, assembled['withheld-receiver-score.json'])):
            raise ValueError('no-refit law union or withheld score differs from sealed control')
        return dict(version='prediction-observed-continuation-smoke-v1',
                    passed=True, source='sealed generated control',
                    refits=0, withheld_receiver_reads=1,
                    exact_receiver_bound=True, exact_receiver_diagnostic=True,
                    exact_law_unions=True, exact_withheld_score=True,
                    charged=counts, builds=len(builds),
                    parent_manifest_sha256=closed.completion['manifest_sha256'],
                    parent_summary_sha256=closed.completion['summary_sha256'],
                    receiver_bound_sha256=digest(encoded(expected_bound)),
                    receiver_diagnostic_sha256=digest(
                        encoded(expected_diagnostic)),
                    checker_sha256=digest((root/'analysis/lll/'
                        'prediction_observed_continuation_smoke.py').read_bytes()),
                    continuation_sha256=digest((root/'analysis/lll/'
                        'prediction_observed_continuation.py').read_bytes()))
    finally:
        closed.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default='.')
    parser.add_argument('--output')
    args = parser.parse_args(argv)
    result = verify(args.root)
    if args.output:
        from .studies.artifacts import atomic, encoded
        atomic(args.output, encoded(result))
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
