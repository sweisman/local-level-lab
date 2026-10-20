# SPDX-License-Identifier: AGPL-3.0-or-later
"""Inspect six saved extreme matrices and one physical anchor per case."""


def evaluate(task,context):
    from lll.ilvis0_sharded_native import read
    from lll.ilvis0_matrix_gram import check_lifted
    from lll.ilvis0_control_shards import _check_continue
    bundle=read(context.input_path());row=bundle['source_result'];source=bundle['source_input']
    if (row['identity']!=task['identity'] or not row['passed'] or not row['supported']
            or task['payload']['maximum_checks']!=7):raise ValueError('complete saved width result and seven checks required')
    future=source['future'];region=source['training']['region'];configuration=bundle['configuration']
    transform=future['reference']['transform']
    if transform['binding']!=future['bound']['transform_binding']:raise ValueError('saved force reference changed')
    proposals=bundle['witnesses']['proposals']
    if len(proposals)!=6 or any(not p['supported'] for p in proposals):raise ValueError('six supported saved witnesses required')
    context.save('reservation.json',dict(matrix_checks=7,lp_proposals=0,native_calls=0))
    def inspect(point):
        _check_continue(context.root,context.manifest)
        return check_lifted(configuration['initial_r'],transform,configuration['limits'],region['center'][:27],point)
    anchor=inspect(source['anchor']);checks=[]
    for ordinal,proposal in enumerate(proposals):
        expected_axis=ordinal//2;expected_direction=1 if ordinal%2==0 else -1
        if (proposal['axis'],proposal['direction'])!=(expected_axis,expected_direction):raise ValueError('saved proposal ordering changed')
        checks.append(dict(axis=proposal['axis'],direction=proposal['direction'],**inspect(proposal['point'])))
    context.save('matrices.json',dict(anchor=anchor,witnesses=checks))
    return dict(identity=task['identity'],model=row['model'],profile=row['profile'],passed=not anchor['incompatible'],
        anchor_compatible=not anchor['incompatible'],witnesses_flagged=sum(p['incompatible'] for p in checks),
        maximum_defect_norm=max(p['defect_norm_upper'] for p in checks),matrix_checks=7,
        native_evaluations=0,lp_proposals=0,optimizer_starts=0,original_reads=0,
        physical_realizability_established=False,observational_coverage_qualified=False,scientific_decision='abstain')
