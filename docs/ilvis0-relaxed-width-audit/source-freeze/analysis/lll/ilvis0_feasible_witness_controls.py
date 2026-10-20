# SPDX-License-Identifier: AGPL-3.0-or-later
"""Known-answer controls for exact repair in all 51 coordinates."""


def evaluate(task,context):
    from fractions import Fraction as F
    from lll.ilvis0_feasible_witness import Region
    spec=task['payload'];family=spec['family'];axis=spec['axis']
    if axis not in (0,18,25,42,50) or family not in ('box','halfspace','boundary','point'):
        raise ValueError('unknown frozen witness control')
    lo=[F(-1)]*51;hi=[F(1)]*51;anchor=[F(0)]*51
    direction=[F(int(i==axis)) for i in range(51)]
    proposal=direction.copy();a=[];b=[]
    if family=='box':proposal[axis]=2;expected_fraction=F(1,2);expected_value=F(1)
    elif family=='halfspace':a=[direction];b=[F(1,4)];expected_fraction=F(3,4);expected_value=F(1,4)
    elif family=='boundary':a=[direction];b=[F(0)];expected_fraction=F(1);expected_value=F(0)
    else:lo=anchor.copy();hi=anchor.copy();expected_fraction=F(1);expected_value=F(0)
    context.save('reservation.json',dict(repairs=1,objective_checks=1,lp_proposals=0))
    region=Region(lo,hi,a,b);witness=region.repair(proposal,anchor)
    value=region.objective(direction,witness['point'])
    passed=witness['mixing_fraction']==expected_fraction and value==expected_value and len(witness['point'])==51
    return dict(identity=task['identity'],passed=passed,family=family,axis=axis,
        point=[str(v) for v in witness['point']],mixing_fraction=str(witness['mixing_fraction']),
        expected_fraction=str(expected_fraction),objective=str(value),expected_objective=str(expected_value),
        maximum_final_slack=str(witness['maximum_final_slack']),constraint_checks=witness['constraint_checks'],
        parameter_count=51,repairs=1,lp_proposals=0,native_evaluations=0,original_reads=0,
        optimizer_starts=0,physical_realizability_established=False,scientific_decision='abstain')
