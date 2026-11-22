# SPDX-License-Identifier: AGPL-3.0-or-later
"""Earlier-only isolated X bias profile on the opened ESA direction controls."""

from contextlib import closing
from pathlib import Path
import sys

from .esa_force_direction_transfer import FOLDER, ID as PARENT, TRAINING, FrozenInputs, verified_force_settings
from .force_direction_bias import profile_direction_bias
from .studies.artifacts import atomic, digest, encoded
from .studies.closed import ClosedStudy


ID = 'esa-direction-bias-training-v1'
SCOPE = 'earlier-only X acceleration bias estimation and later direction scores on ESA 187'
PLAN = FOLDER + 'ESA_DIRECTION_BIAS_TRAINING_PLAN.md'
RESULT = FOLDER + 'esa-direction-bias-training-result.json'
PARENT_SHA = '8b30cacfdbf23fda054ed3b3f65275874c1641bcb0f45f5a542e202f57e77b0f'
GRID = tuple(i/2000. for i in range(-200, 201))
EDGE = .0225
PROFILES = 36
TASK = dict(identity='earlier-bias-profiles', input_key='interval', payload=dict(profiles=PROFILES),
            limits=dict(native_calls=0, packet_visits=0, bound_calls=PROFILES,
                        bound_steps=(len(GRID)+1)*PROFILES))


def prepare(root):
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    directory = root / 'data' / (ID + '-inputs')
    if (root / 'data' / ID).exists() or directory.exists():
        raise ValueError('existing direction bias freeze must be preserved')
    inputs = {}
    with closing(ClosedStudy(root, 'data/' + PARENT)) as previous:
        if previous.completion['manifest_sha256'] != PARENT_SHA or not previous.summary['passed']:
            raise ValueError('exact closed direction study required')
        for key in ('doppler', 'matching', 'direction', 'matched', 'training', 'interval', 'saved-input-binding'):
            target = directory / key
            atomic(target, previous.input(key, raw=True))
            inputs[key] = target.relative_to(root).as_posix()
    adapter = Path(__file__).relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE, adapter=adapter, inputs=inputs, tasks=[TASK],
        sources=source_closure(root, [adapter, PLAN, 'analysis/tests/test_force_direction_bias.py']),
        workers=1, threads=1, maximum_wall_s=90.)
    print(encoded(Definition.from_dict(definition, root).prepare(root)['limits']).decode(), end='')


def evaluate(task, context):
    if context.manifest['scope'] != SCOPE or task['payload'] != TASK['payload']:
        raise ValueError('frozen early direction bias comparison required')
    rows = []
    material = FrozenInputs(context)
    for width, source, nominal, response, fields in verified_force_settings(material):
        for field, vectors in fields.items():
            outcomes = {}
            for shape, path in vectors.items():
                context.charge(bound_calls=1, bound_steps=len(GRID)+1)
                outcomes[shape] = profile_direction_bias(path, nominal, response, grid=GRID,
                                                         training=TRAINING, positive_edge=EDGE)
            g, d = outcomes['globe'], outcomes['disc']
            gap = d['later_angular_rms_deg']-g['later_angular_rms_deg'] if g['status'] == d['status'] == 'scored' else None
            rows.append(dict(width_reports=width, source=source, field=field, profiles=outcomes,
                             disc_minus_globe_later_deg=gap))
    context.save_bytes('bias-profiles.json', encoded(dict(rows=rows, bias_grid_mps2=GRID,
        positive_edge_mps2=EDGE, later_scores_used_for_selection=False, protected_reads=0,
        original_data_reads=0, new_inertial_fits=0, scientific_decision='abstain')))
    return dict(passed=len(rows)*2 == PROFILES, rows=len(rows), scientific_decision='abstain')


def report(root):
    with closing(ClosedStudy(root, 'data/' + ID)) as run:
        if (not run.summary['passed'] or run.summary['charged']['bound_calls'] != PROFILES
                or run.summary['charged']['bound_steps'] != (len(GRID)+1)*PROFILES):
            raise ValueError('complete earlier-only bias study required')
        result = run.artifact(TASK['identity'], 'bias-profiles.json')
        result.update(study_manifest_sha256=run.completion['manifest_sha256'], parent_manifest_sha256=PARENT_SHA)
    raw = encoded(result)
    path = root / RESULT
    if not path.exists():
        atomic(path, raw)
    if path.read_bytes() != raw:
        raise ValueError('saved earlier-only bias report differs')
    print(digest(raw))


if __name__ == '__main__':
    if sys.argv[1:] == ['prepare']:
        prepare(Path.cwd())
    elif sys.argv[1:] == ['report']:
        report(Path.cwd())
    else:
        raise SystemExit('usage: python -m lll.esa_direction_bias_training {prepare,report}')
