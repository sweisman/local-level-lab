# SPDX-License-Identifier: AGPL-3.0-or-later
"""Deterministic saved-input comparison of generated noisy and clean IMU increments."""

import argparse
import hashlib
import json
import math
from pathlib import Path


def summarize_difference(clean,noisy,dt):
    import numpy as np
    clean,noisy,dt=(np.asarray(value,dtype=float)
                    for value in (clean,noisy,dt))
    if (clean.ndim!=2 or clean.shape[1:]!=(3,) or noisy.shape!=clean.shape
            or dt.shape!=(len(clean),) or len(clean)<2 or
            not all(np.all(np.isfinite(value)) for value in (clean,noisy,dt))
            or np.any(dt<=0)):
        raise ValueError('complete aligned finite IMU increments required')
    difference=noisy-clean
    cumulative=np.cumsum(difference,axis=0)
    half=len(clean)//2
    return dict(signed_total_increment=np.sum(difference,axis=0).tolist(),
        first_half_increment=np.sum(difference[:half],axis=0).tolist(),
        second_half_increment=np.sum(difference[half:],axis=0).tolist(),
        maximum_absolute_cumulative_increment=np.max(
            np.abs(cumulative),axis=0).tolist(),
        rms_rate_equivalent=np.sqrt(np.mean((difference/dt[:,None])**2,
            axis=0)).tolist(),samples=len(clean))


def build(root):
    import numpy as np
    from .airquantumgrav_training_controls import generated_training
    from .esa_fit_adjusted_control_study import recipe as parent_recipe
    from .esa_fit_adjusted_control_report import _study
    from .esa_oracle_control import load_case
    from .studies.artifacts import digest

    root=Path(root).resolve()
    parent,lineage=_study(root)
    try:
        sources=('analysis/lll/airquantumgrav_training_controls.py',
                 'analysis/lll/airquantumgrav_geographic_controls.py',
                 'analysis/lll/esa_fit_adjusted_control_study.py')
        if any(parent.manifest['sources'].get(name)!=hashlib.sha256(
                (root/name).read_bytes()).hexdigest() for name in sources):
            raise ValueError('clean generator differs from sealed noisy parent')
        manifest_sha=parent.completion['manifest_sha256']
    finally:
        parent.close()
    r=parent_recipe()
    spec=dict(model='sphere_rotating',latitude_deg=55.,profile=False,start=0)
    counted={}
    limits=dict(generated_samples=270_601,constructed_intervals=270_000)
    def reserve(**work):
        for key,value in work.items():
            counted[key]=counted.get(key,0)+value
            if counted[key]>limits[key]:
                raise ValueError('clean reconstruction allowance exceeded')
    clean=generated_training(spec,r,reserve=reserve,
        height_profile='climb',gravity_model='inverse_square_height')
    if counted!=limits:
        raise ValueError('complete clean reconstruction required')
    cases={}
    for law in ('increment','point'):
        measured=load_case(root,law)
        if (not np.array_equal(clean['dt'],measured['dt']) or
                not np.array_equal(clean['times'],measured['times']) or
                measured['parent_manifest_sha256']!=manifest_sha):
            raise ValueError('matched generated timing or parent differs')
        angle=summarize_difference(clean['theta'],measured['theta'],clean['dt'])
        velocity=summarize_difference(clean['dv'],measured['dv'],clean['dt'])
        cases[law]=dict(angle_increment_rad=angle,
            velocity_increment_mps=velocity,
            total_angle_difference_deg=(np.asarray(
                angle['signed_total_increment'])*180/math.pi).tolist(),
            clean_array_sha256={key:digest(np.asarray(
                clean[key],dtype='<f8').tobytes()) for key in
                ('theta','dv','dt')},
            noisy_input_sha256=measured['parent_input_sha256'])
    return dict(version='esa-oracle-noise-diagnostic-v1',
        parent_manifest_sha256=manifest_sha,lineage_sha256=lineage,
        generator_source_sha256={name:hashlib.sha256((root/name).read_bytes()
            ).hexdigest() for name in sources},
        report_source_sha256=hashlib.sha256((root/
            'analysis/lll/esa_oracle_noise_diagnostic.py').read_bytes()).hexdigest(),
        cases=cases,generated_work=counted,native_calls=0,
        original_reads=0,protected_confirmation_groups_opened=0,
        scientific_decision='abstain')


def publish(root):
    from .studies.artifacts import atomic,encoded
    root=Path(root).resolve();result=build(root)
    base=root/'docs/prediction-observed-development'
    atomic(base/'ORACLE_NOISE_DIAGNOSTIC.json',encoded(result))
    rows=[]
    for law in ('increment','point'):
        case=result['cases'][law]
        values=case['total_angle_difference_deg']
        speed=case['velocity_increment_mps']['signed_total_increment']
        rows.append('| {} | {:.4f}, {:.4f}, {:.4f} | {:.4f}, {:.4f}, {:.4f} |'.format(
            law,*values,*speed))
    markdown=('# Noisy versus clean generated IMU increments\n\n'
        'The two saved noisy streams were compared with the same deterministic '
        'clean generator. No fit or native forecast was run. Signed sums are '
        'shown in **sensor body axes**; they are input diagnostics, not a '
        'navigation-frame turn or a position forecast.\n\n'
        '| Injected error law | Sum of angle-increment difference X/Y/Z (degrees) | Sum of velocity-increment difference X/Y/Z (m/s) |\n'
        '| --- | --- | --- |\n'+'\n'.join(rows)+'\n\n'
        'These differences include injected random error and changing bias. '
        'They do not isolate a single component or establish the observed '
        'aircraft error law. The [machine-readable report](ORACLE_NOISE_DIAGNOSTIC.json) '
        'also records half-period sums, rate-equivalent RMS values and hashes.\n')
    atomic(base/'ORACLE_NOISE_DIAGNOSTIC.md',markdown.encode())
    return result


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',default='.')
    args=parser.parse_args(argv)
    result=publish(args.root)
    print(json.dumps({law:dict(angle_deg=result['cases'][law][
        'total_angle_difference_deg'],velocity_mps=result['cases'][law][
        'velocity_increment_mps']['signed_total_increment']) for law in
        ('increment','point')},sort_keys=True))


if __name__=='__main__':main()
