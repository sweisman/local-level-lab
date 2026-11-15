# SPDX-License-Identifier: AGPL-3.0-or-later
"""Stage a 400/120 ESA development cut without future receiver values."""

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

    required={'interval','training','saved-increment-forecast',
              'saved-input-binding','recipe'}
    if not isinstance(source,dict) or not required<=source.keys():
        raise ValueError('complete sealed ESA parent input required')
    binding=json.loads(source['saved-input-binding'])
    recipe=json.loads(source['recipe'])
    forecast=json.loads(source['saved-increment-forecast'])
    if (binding.get('source_id')!='esa-99f1530c3eda4318' or
            binding.get('training_epochs')!=800 or
            recipe.get('clock')!='header_elapsed' or
            recipe.get('model')!='sphere_rotating' or
            set(recipe.get('noise_by_law',{}))!={'increment','point'}):
        raise ValueError('unchanged development source, clock and error laws required')
    split=partition_development_input(
        source['interval'],source['training'],forecast['times_s'],
        time_origin_s=binding['time_origin_s'],
        training_epochs=400,forecast_epochs=520,
        latency_s=abs(float(recipe['limits'].get('time_offset',0.))))
    if len(split.scoring_rows)!=120 or len(split.times_s)!=520:
        raise ValueError('exact 400/120 rolling origin required')
    return RollingMaterial(split=split,binding=binding,recipe=recipe)


def preflight(root):
    from .esa_fixed_rate_protocol import stage_parent
    from .studies.artifacts import digest

    root=Path(root).resolve()
    source=stage_parent(root,smoke=False)
    parent=json.loads(source['parent_identity'])
    if (parent.get('source_id')!='esa-99f1530c3eda4318' or
            parent.get('original_reads')!=0 or
            parent.get('protected_reads')!=0 or
            parent.get('refits')!=0):
        raise ValueError('hash-verified saved development parent required')
    material=build_material(source)
    split=material.split
    fit=split.fit_material()
    if set(fit)!={'interval','training','forecast_times'}:
        raise ValueError('future receiver rows may not enter fit material')
    return dict(version='esa-rolling-origin-400-preflight-v1',
                source_id=parent['source_id'],
                source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                partition_source_sha256=digest((root/
                    'analysis/lll/esa_training_split.py').read_bytes()),
                parent_binding_sha256=digest(source['saved-input-binding']),
                parent_recipe_sha256=digest(source['recipe']),
                fit_input_sha256={key:digest(value) for key,value in fit.items()},
                training_receiver_reports=400,
                withheld_receiver_reports=len(split.scoring_rows),
                forecast_times=len(split.times_s),
                staged_imu_packets=split.packet_count,
                fit_input_keys=sorted(fit),
                future_receiver_positions_staged=False,
                error_laws=sorted(material.recipe['noise_by_law']),
                original_reads=0,protected_reads=0,
                native_calls=0,model_fits=0,
                technical_recovery_qualified=False,
                scientific_decision='abstain')


def publish(root):
    from .studies.artifacts import atomic,encoded
    root=Path(root).resolve();report=preflight(root)
    base=root/'docs/prediction-observed-development'
    atomic(base/'ROLLING_ORIGIN_400_PREFLIGHT.json',encoded(report))
    page=('# Earlier-origin fit preparation\n\n'
        'A preflight on the already saved ESA development recording selects '
        'receiver reports 0–399 for fitting and the next 120 times for '
        'prediction. Its fit material includes {:,} IMU packets through the '
        'prediction end, but **no later receiver positions**. Both existing '
        'error-law assumptions remain in scope.\n\n'
        'This only checks the input cut and its hashes. It has made no fit, '
        'forecast or Earth-model decision. A source-bound numerical study '
        'and interruption-recovery test are still required before launch. '
        'This is exploratory work on the already opened development flight; '
        'the seven reserved groups remain closed.\n\n'
        '[Planned question and limits](ROLLING_ORIGIN_400_PLAN.md) · '
        '[Input hashes](ROLLING_ORIGIN_400_PREFLIGHT.json).\n').format(
            report['staged_imu_packets'])
    atomic(base/'ROLLING_ORIGIN_400_PREFLIGHT.md',page.encode())
    return report


def main(argv=None):
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',default='.')
    args=parser.parse_args(argv)
    report=publish(args.root)
    print(json.dumps({key:report[key] for key in (
        'training_receiver_reports','withheld_receiver_reports',
        'staged_imu_packets','model_fits')},sort_keys=True))


if __name__=='__main__':main()
