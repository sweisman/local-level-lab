# SPDX-License-Identifier: AGPL-3.0-or-later
"""Screen candidate platform rate conventions using its relative clock."""

from contextlib import closing
from itertools import permutations, product
import json
from pathlib import Path
import sys

from . import esa_girafe_platform_timing as timing
from . import esa_girafe_platform_vertical_holdout as holdout
from .esa_direction_holdout_forecast import frozen_input
from .esa_ground_tilt_closure import gyro_steps, tilt_pairs
from .studies.artifacts import atomic, digest, encoded, safe_path
from .studies.closed import ClosedStudy


ID = 'esa-girafe-platform-rate-v1'
SCOPE = 'screen platform angular-rate conventions on three existing GIRAFE excerpts'
PLAN = holdout.FOLDER+'ESA_GIRAFE_PLATFORM_RATE_PLAN.md'
RESULT = holdout.FOLDER+'esa-girafe-platform-rate-result.json'
MAX_ROWS = 14_000
SPANS = (1, 10)
CONVENTIONS = tuple(product(('degree_per_second', 'radian_per_second'),
                            permutations(range(3)), product((1, -1), repeat=3)))
COMPARISONS = len(CONVENTIONS)+len(holdout.OFFSETS)-1
TASK = dict(identity='screen-and-transfer-platform-rate-convention', input_key='receipt', payload={},
    limits=dict(native_calls=0, packet_visits=0, bound_calls=len(holdout.OFFSETS)+COMPARISONS,
                bound_steps=len(holdout.OFFSETS)*timing.RANGE_BYTES+COMPARISONS*MAX_ROWS))
METRICS = ('no_motion_rms_arcsec', 'gyro_change_rms_arcsec', 'gyro_prediction_rms_arcsec',
           'centered_change_similarity', 'centered_error_reduction', 'pairs')


def force_support(rows):
    if rows.ndim != 2 or rows.shape[1] != 7:
        raise ValueError('time and all six candidate sensor columns required')
    return timing.tenth_second_values(rows[:, 0], rows[:, 1:4])


def case_score(rows, centers, force, convention):
    import numpy as np

    if convention not in CONVENTIONS:
        raise ValueError('declared signed axis permutation and rate unit required')
    unit, axes, signs = convention
    rates = rows[:, 4+np.asarray(axes)]*np.asarray(signs)
    if unit == 'degree_per_second':
        rates = np.deg2rad(rates)
    rotations = gyro_steps(rows[:, 0], rates[:-1], centers)
    result = []
    for span in SPANS:
        score = tilt_pairs(force, rotations, span=span)
        result.append(dict(span_s=span/10., **{name: score[name] for name in METRICS}))
    return result


def prepare(root):
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    if (root/'data'/ID).exists():
        raise ValueError('existing sealed platform rate study required to stay intact')
    adapter = Path(__file__).relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE, adapter=adapter,
        inputs=dict(receipt=(holdout.DIRECTORY/'transfer-receipt.json').as_posix(), probes=timing.probe.RESULT),
        tasks=[TASK], sources=source_closure(root, [adapter, PLAN, 'analysis/tests/test_esa_girafe_platform_rate.py',
            'analysis/tests/test_esa_girafe_platform_probe.py', 'analysis/tests/test_esa_ground_tilt_closure.py']),
        workers=1, threads=1, maximum_wall_s=120.)
    return Definition.from_dict(definition, root).prepare(root)['limits']


def evaluate(task, context):
    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if declared != TASK or context.manifest['scope'] != SCOPE:
        raise ValueError('exact finite local rate screen required')
    transfer = frozen_input(context, 'receipt', holdout.RECEIPT_SHA)
    prefix = frozen_input(context, 'probes', timing.probe.PROBE_SHA)['prefix']
    if (tuple(entry['offset'] for entry in transfer['ranges']) != holdout.OFFSETS
            or transfer['verified_overlap_bytes'] != holdout.OVERLAP_BYTES):
        raise ValueError('original three saved excerpts required')
    root = context.root.parents[1]
    selection = None
    output = []
    for receipt in transfer['ranges']:
        offset = receipt['offset']
        context.charge(bound_calls=1, bound_steps=timing.RANGE_BYTES)
        path = safe_path(root, (holdout.DIRECTORY/f'range-{offset}.asc').as_posix())
        if path.stat().st_size != timing.RANGE_BYTES:
            raise ValueError('one exact saved range required')
        rows, _ = holdout.new_samples(path.read_bytes(), receipt, prefix, include_candidate_rates=True)
        if len(rows) > MAX_ROWS:
            raise ValueError('saved rows exceed the declared comparison limit')
        centers, force = force_support(rows)
        fitting = selection is None
        cases = []
        for index in range(len(CONVENTIONS)) if fitting else [selection]:
            context.charge(bound_calls=1, bound_steps=MAX_ROWS)
            scores = case_score(rows, centers, force, CONVENTIONS[index])
            unit, axes, signs = CONVENTIONS[index]
            cases.append(dict(index=index, unit=unit, rate_column_order=list(axes),
                              signs=list(signs), scores=scores))
        if fitting:
            winner = min(cases, key=lambda case: case['scores'][0]['gyro_prediction_rms_arcsec'])
            selection = winner['index']
        else:
            winner = cases[0]
        record = dict(offset=offset, source_sha256=receipt['sha256'], rows=len(rows),
            clock_support_s=[float(centers[0]), float(centers[-1])], selected=winner, cases=cases)
        output.append(record)
        context.save_bytes(f'range-{offset}.json', encoded(record))
    improvement = [row['selected']['scores'][0]['gyro_prediction_rms_arcsec']
                   < row['selected']['scores'][0]['no_motion_rms_arcsec'] for row in output]
    context.save_bytes('screen.json', encoded(dict(excerpts=output, selected_index=selection,
        improved_excerpts=sum(improvement), same_clock_only=True, absolute_timing_qualified=False,
        rate_mapping_qualified=False, protected_reads=0, model_fits=0, scientific_decision='abstain')))
    return dict(passed=True, improved_excerpts=sum(improvement), scientific_decision='abstain')


def report(root):
    identity = TASK['identity']
    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        if not study.summary['passed'] or study.rows[identity]['charged'] != TASK['limits']:
            raise ValueError('closed rate screen and exact charge ledger required')
        result = study.artifact(identity, 'screen.json')
        if (tuple(row['offset'] for row in result['excerpts']) != holdout.OFFSETS
                or [len(row['cases']) for row in result['excerpts']] != [len(CONVENTIONS), 1, 1]):
            raise ValueError('complete calibration and untouched held-out comparisons required')
        for row in result['excerpts']:
            if study.artifact(identity, f"range-{row['offset']}.json") != row:
                raise ValueError('sealed excerpt scores differ')
        result.update(manifest_sha256=study.completion['manifest_sha256'], charged=TASK['limits'])
    raw = encoded(result)
    target = root/RESULT
    if not target.exists():
        atomic(target, raw)
    if target.read_bytes() != raw:
        raise ValueError('preserved public screen differs from the closed result')
    return dict(sha256=digest(raw), improved_excerpts=result['improved_excerpts'],
                selected=[row['selected'] for row in result['excerpts']])


if __name__ == '__main__':
    operation = {'prepare': prepare, 'report': report}[sys.argv[1]]
    print(json.dumps(operation(Path.cwd()), sort_keys=True))
