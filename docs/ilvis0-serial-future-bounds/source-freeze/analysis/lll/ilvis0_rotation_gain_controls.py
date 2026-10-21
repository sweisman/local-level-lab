# SPDX-License-Identifier: AGPL-3.0-or-later
"""Independent physical-oracle checks of rotation/reciprocal-gain supports."""


def evaluate(task, context):
    import numpy as np
    from lll.ilvis0_shared_norm_controls import evaluate as physical_oracle
    from lll.ilvis0_sharded_native import read, plain
    from lll.ilvis0_shared_reference_terms import ReferenceErrors
    from lll.ilvis0_reference_acceleration import AccelerationTerms
    from lll.ilvis0_common_force_transform import ForceTransform
    from lll.ilvis0_rotation_gain_support import build, exact_slacks
    from lll.ilvis0_control_shards import _check_continue
    oracle = physical_oracle(task, context)
    case = read(context.input_path()); cfg = dict(case['configuration'])
    cfg['limits'] = np.array(cfg['limits'],float)
    center = np.full(27,.1); lo = -np.ones(27); hi = np.ones(27)
    family = task['payload']['family']
    if family == 'sector': lo[2]=0.; hi[2]=.25; center[2]=.125
    elif family == 'fixed': lo=center.copy(); hi=center.copy()
    elif family == 'gain-boundary': cfg['limits'][18:21]=.9
    elif family != 'full': raise ValueError('unknown rotation/gain control domain')
    r = ReferenceErrors(cfg,lo,hi,center,source_id=task['identity'])
    a = AccelerationTerms(r,case['dv'][0],case['dt'][0],cfg['gravity'])
    cut = build(a,ForceTransform(r)); worst = None; probes=[]
    context.save('support-reservation.json',dict(probes=64,exact_inequalities=4992))
    for row in oracle['probes']:
        _check_continue(context.root,context.manifest)
        point = np.r_[row['point'],row['common_error']]
        slack = max(exact_slacks(cut,point))
        worst = slack if worst is None else max(worst,slack)
        probes.append(dict(point=row['point'],common_error=row['common_error'],maximum_exact_slack=str(slack)))
    return plain(dict(identity=task['identity'],passed=oracle['passed'] and worst<=0,
        probe_points=len(probes),exact_inequalities=78*len(probes),
        maximum_exact_slack=str(worst),maximum_oracle_difference=oracle['maximum_oracle_difference'],
        cuts=cut.report(),probes=probes,physical_parameter_count=27,enclosure_parameter_count=51,
        native_evaluations=0,original_reads=0,optimizer_starts=0,
        observational_coverage_qualified=False,scientific_decision='abstain'))
