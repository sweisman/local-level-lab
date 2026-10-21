# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite all-domain restriction and source-cap checks, with no integration."""
def evaluate(task,context):
    from lll.ilvis0_sharded_native import read,plain
    from lll.ilvis0_coupled_map_controls import Allowance
    from lll.ilvis0_control_shards import _check_continue
    from lll.ilvis0_conditioned_acceleration import ConditionedAcceleration
    from lll.ilvis0_conditioned_subdomain import SubdomainAcceleration
    from lll.ilvis0_initial_source_bridge_v2 import certify
    from lll.ilvis0_orientation_cover import sector
    from lll.ilvis0_taylor_native import make_reference
    spec=task['payload'];bundle=read(context.input_path());case=read(context.input_path(spec['case_key']))
    if (len(case['dt'])!=1600 or case['configuration']['model']!=spec['model']
            or case['configuration']['profile']!=spec['profile']):
        raise ValueError('fixed generated source identity required')
    events=[]
    def persist(event):
        _check_continue(context.root,context.manifest)
        context.save(f'reservation-{len(events)+1:03d}.json',event);events.append(event)
    budget=Allowance(dict(setups=1,subdomain_audits=1,exact_supports=6),persist)
    parent=ConditionedAcceleration(bundle['parent_input'],bundle['parent_certificate'],
        reserve=lambda count:budget.reserve(dict(exact_supports=count)))
    child=bundle['child_training'];region=child['region'];lo=region['lower'][:27];hi=region['upper'][:27]
    budget.reserve(dict(subdomain_audits=1))
    proof=SubdomainAcceleration(parent,bundle['parent_input'],child,lo,hi);proof.match_training(child)
    budget.reserve(dict(setups=1));box=sector(spec['sector'])
    reference=make_reference(case['configuration'],case['theta'],case['dv'],case['dt'],
        **{key:box[key] for key in ('lower','upper','center')})
    if reference.report()!=bundle['parent_input']['reference']:raise ValueError('saved source reference changed')
    proof.match(reference.report(),lo,hi);context.save('restricted-proof.json',proof.report())
    context.charge(bound_calls=1,bound_steps=0)
    cap=certify(reference,lo,hi);context.save('source-cap.json',cap)
    return plain(dict(identity=task['identity'],model=spec['model'],profile=spec['profile'],sector=spec['sector'],
        passed=cap['nonlinear_cap_sufficient'],source_cap_sufficient=cap['nonlinear_cap_sufficient'],
        subdomain_verified=True,parent_bounds_unchanged=proof.norm_change==parent.norm_change
            and proof.component_changes==parent.component_changes and proof.original_remainder==parent.original_remainder,
        physical_parameter_count=27,expression_parameter_count=51,enclosure_parameter_count=78,
        parent_constraint_count=proof.inherited_constraint_count,work=budget.counts,
        native_evaluations=0,optimizer_starts=0,original_reads=0,
        observational_coverage_qualified=False,scientific_decision='abstain'))
