# SPDX-License-Identifier: AGPL-3.0-or-later
"""Reconstruct exact seeded white/bias components of two sealed generated IMUs."""

import argparse
import hashlib
import io
import json
from pathlib import Path


def reconstruct_components(clean,law,*,seed):
    """Regenerate one declared seeded IMU law and retain its two components."""
    import numpy as np
    from .airquantumgrav_noisy_inputs import (
        noise_settings,rate_point_noise_settings,_bias_parameters)
    from .measurement_noise import perturb_imu,perturb_linear_rate_points

    if law not in ('increment','point'):
        raise ValueError('declared noise law required')
    settings=(noise_settings(seed=seed) if law=='increment'
              else rate_point_noise_settings(seed=seed))
    square=lambda value:np.eye(3)*value*value
    args=dict(theta=clean['theta'],dv=clean['dv'],dt=clean['dt'],
              seed=seed,maximum_steps=len(clean['dt']),
              **_bias_parameters(settings,square))
    if law=='increment':
        return perturb_imu(**args,
            gyro_white_psd=square(settings['gyro_white_rads_per_sqrt_s']),
            accel_white_psd=square(settings['accel_white_mps_per_sqrt_s']))
    charged={}
    def reserve(**work):
        for key,value in work.items():
            charged[key]=charged.get(key,0)+value
            if charged[key]>12*(len(clean['dt'])+1):
                raise ValueError('point noise reconstruction allowance exceeded')
    regenerated=perturb_linear_rate_points(**args,
        gyro_point_covariance=square(settings['gyro_point_std_rads']),
        accel_point_covariance=square(settings['accel_point_std_mps2']),
        reserve=reserve)
    if charged!=dict(noise_normal_variates=12*(len(clean['dt'])+1)):
        raise ValueError('complete point noise reconstruction required')
    return regenerated


def build(root):
    import numpy as np
    from .esa_oracle_control import load_case
    from .esa_oracle_channel_study import ID as CHANNEL_ID
    from .esa_fit_adjusted_control_study import SEEDS
    from .esa_fit_adjusted_control_report import _study,_artifact
    from .esa_oracle_noise_diagnostic import summarize_difference
    from .studies.closed import ClosedStudy
    from .studies.artifacts import digest

    root=Path(root).resolve()
    channel=ClosedStudy(root,'data/'+CHANNEL_ID)
    try:
        if channel.completion['state']!='complete' or channel.summary[
                'completed']!=4:
            raise ValueError('complete staged channel input required')
        raw=channel.input('clean-increments',raw=True)
        binding=channel.input('parent-binding')
        with np.load(io.BytesIO(raw),allow_pickle=False) as staged:
            if set(staged.files)!={'theta','dv','dt','times'}:
                raise ValueError('complete staged clean IMU required')
            clean={key:np.array(staged[key],dtype=float,copy=True)
                   for key in staged.files}
        channel_sha=channel.completion['manifest_sha256']
    finally:channel.close()
    parent,lineage=_study(root)
    try:
        names=('analysis/lll/measurement_noise.py',
               'analysis/lll/airquantumgrav_noisy_inputs.py')
        if (parent.completion['manifest_sha256']!=binding[
                'parent_manifest_sha256'] or lineage!=binding['lineage_sha256']
                or any(parent.manifest['sources'].get(name)!=hashlib.sha256(
                    (root/name).read_bytes()).hexdigest() for name in names)):
            raise ValueError('sealed noise generator differs')
        cases={}
        for law in ('increment','point'):
            measured=load_case(root,law)
            regenerated=reconstruct_components(clean,law,seed=SEEDS[law])
            if (not np.array_equal(regenerated['theta'],measured['theta']) or
                    not np.array_equal(regenerated['dv'],measured['dv']) or
                    not np.array_equal(regenerated['dt'],measured['dt']) or
                    binding['noisy_input_sha256'][law]!=measured[
                        'parent_input_sha256']):
                raise ValueError('regenerated noise does not reproduce sealed IMU')
            noise=regenerated['noise'];components={}
            for channel_name in ('gyro','accel'):
                unit=noise[channel_name];components[channel_name]={}
                for component in ('white','bias'):
                    increments=np.asarray(unit[component+'_increments'],float)
                    components[channel_name][component]=dict(
                        summary=summarize_difference(np.zeros_like(increments),
                            increments,clean['dt']),
                        array_sha256=digest(increments.astype('<f8').tobytes()))
            artifact=_artifact(parent,law,'input-binding.json')
            if any(artifact['measured_raw_array_sha256'][name]!=digest(
                    np.asarray(measured[name],dtype='<f8').tobytes())
                    for name in ('theta','dv','dt')):
                raise ValueError('sealed noisy array hashes differ')
            cases[law]=dict(components=components,
                reproduced_sealed_measured_arrays_exactly=True,
                seed=SEEDS[law],input_sha256=measured['parent_input_sha256'])
        return dict(version='esa-oracle-noise-components-v1',
            channel_study_manifest_sha256=channel_sha,
            parent_manifest_sha256=binding['parent_manifest_sha256'],
            generator_source_sha256={name:hashlib.sha256((root/name).read_bytes()
                ).hexdigest() for name in names},
            report_source_sha256=hashlib.sha256((root/
                'analysis/lll/esa_oracle_noise_components.py').read_bytes()).hexdigest(),
            cases=cases,native_calls=0,original_reads=0,
            protected_confirmation_groups_opened=0,
            scientific_decision='abstain')
    finally:parent.close()


def publish(root):
    from .studies.artifacts import atomic,encoded
    root=Path(root).resolve();report=build(root)
    base=root/'docs/prediction-observed-development'
    atomic(base/'ORACLE_NOISE_COMPONENTS.json',encoded(report))
    rows=[]
    for law in ('increment','point'):
        for component in ('white','bias'):
            values=report['cases'][law]['components']['gyro'][component][
                'summary']['signed_total_increment']
            rows.append('| {} | {} | {:.4f}, {:.4f}, {:.4f} |'.format(
                law,component,*(np*180/3.141592653589793 for np in values)))
    markdown=('# Exact injected gyro components\n\n'
        'The seeded white-error and changing-bias arrays were regenerated '
        'from the frozen clean stream. Their sum reproduces both archived '
        'measured IMU streams exactly. No fit or native forecast was run.\n\n'
        '| Error law | Gyro component | Signed body-axis angle sum X/Y/Z (degrees) |\n'
        '| --- | --- | --- |\n'+'\n'.join(rows)+'\n\n'
        'These signed sums are input checks, not navigation-frame angular '
        'motion or separate causal effects on predicted position. The '
        '[machine-readable report](ORACLE_NOISE_COMPONENTS.json) records '
        'all gyro and accelerometer component summaries and hashes.\n')
    atomic(base/'ORACLE_NOISE_COMPONENTS.md',markdown.encode())
    return report


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',default='.')
    args=parser.parse_args(argv);report=publish(args.root)
    print(json.dumps({law:{component:report['cases'][law]['components'][
        'gyro'][component]['summary']['signed_total_increment']
        for component in ('white','bias')} for law in ('increment','point')},
        sort_keys=True))


if __name__=='__main__':main()
