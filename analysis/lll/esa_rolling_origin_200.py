# SPDX-License-Identifier: AGPL-3.0-or-later
"""Prepare a 200/120 cross-origin check inside the opened ESA development run.

The fixed cut tests temporal transfer of the prediction calculation. It does
not calibrate an error law or read any protected confirmation flight.
"""

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path


@dataclass(frozen=True)
class RollingMaterial:
    split: object
    binding: dict
    recipe: dict


def build_material(source):
    from .esa_training_split import partition_development_input

    required = {'interval', 'training', 'saved-increment-forecast',
                'saved-input-binding', 'recipe'}
    if not isinstance(source, dict) or not required <= source.keys():
        raise ValueError('complete sealed ESA parent input required')
    binding = json.loads(source['saved-input-binding'])
    recipe = json.loads(source['recipe'])
    forecast = json.loads(source['saved-increment-forecast'])
    if (binding.get('source_id') != 'esa-99f1530c3eda4318' or
            binding.get('training_epochs') != 800 or
            recipe.get('clock') != 'header_elapsed' or
            recipe.get('model') != 'sphere_rotating' or
            recipe.get('maximum_evaluations') != 200 or
            set(recipe.get('noise_by_law', {})) != {'increment', 'point'}):
        raise ValueError('unchanged development source, clock and laws required')
    split = partition_development_input(
        source['interval'], source['training'], forecast['times_s'],
        time_origin_s=binding['time_origin_s'],
        training_epochs=200, forecast_epochs=320,
        latency_s=abs(float(recipe['limits'].get('time_offset', 0.))))
    if len(split.scoring_rows) != 120 or len(split.times_s) != 320:
        raise ValueError('exact 200/120 rolling origin required')
    return RollingMaterial(split=split, binding=binding, recipe=recipe)


def preflight(root):
    from .esa_fixed_rate_protocol import stage_parent
    from .studies.artifacts import digest

    root = Path(root).resolve()
    source = stage_parent(root, smoke=False)
    parent = json.loads(source['parent_identity'])
    if (parent.get('source_id') != 'esa-99f1530c3eda4318' or
            parent.get('original_reads') != 0 or
            parent.get('protected_reads') != 0 or
            parent.get('refits') != 0):
        raise ValueError('hash-verified saved development parent required')
    material = build_material(source)
    split = material.split
    fit = split.fit_material()
    if set(fit) != {'interval', 'training', 'forecast_times'}:
        raise ValueError('future receiver rows entered the fit material')
    return dict(version='esa-rolling-origin-200-preflight-v1',
                source_id=parent['source_id'],
                source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                plan_sha256=digest((root/'docs/prediction-observed-development/'
                    'ROLLING_ORIGIN_200_PLAN.md').read_bytes()),
                training_receiver_reports=200,
                withheld_receiver_reports=len(split.scoring_rows),
                forecast_times=len(split.times_s),
                staged_imu_packets=split.packet_count,
                fit_input_sha256={key: digest(value) for key, value in fit.items()},
                scoring_positions_staged_with_fit=False,
                original_reads=0, protected_reads=0,
                native_calls=0, model_fits=0,
                scientific_decision='abstain')


def publish(root):
    from .studies.artifacts import atomic, encoded

    root = Path(root).resolve()
    result = preflight(root)
    base = root/'docs/prediction-observed-development'
    atomic(base/'ROLLING_ORIGIN_200_PREFLIGHT.json', encoded(result))
    page = ('# Earlier-origin input check\n\n'
            'A preflight on the saved ESA development recording selects the '
            'first 200 receiver reports for fitting and the next 120 for '
            'later scoring. The fit input includes {:,} IMU packets and all '
            '320 report times, but **no scoring positions**. Both existing '
            'IMU error-law assumptions remain in scope.\n\n'
            'This is an input and hash check. It has run no model fit, '
            'forecast or Earth-model test. Source-bound qualification and '
            'reboot recovery must pass before the finite study can start. '
            'The seven reserved ESA flight groups remain closed.\n\n'
            '[Fixed question and limits](ROLLING_ORIGIN_200_PLAN.md) · '
            '[Input hashes](ROLLING_ORIGIN_200_PREFLIGHT.json).\n').format(
                result['staged_imu_packets'])
    atomic(base/'ROLLING_ORIGIN_200_PREFLIGHT.md', page.encode())
    return result


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', nargs='?', default='preflight',
                        choices=('preflight', 'publish'))
    parser.add_argument('--root', default='.')
    args = parser.parse_args(argv)
    result = publish(args.root) if args.action == 'publish' else preflight(args.root)
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
