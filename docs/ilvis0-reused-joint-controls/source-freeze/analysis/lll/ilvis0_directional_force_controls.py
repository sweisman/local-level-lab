# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite static-action qualification on existing generated physical inputs."""
from fractions import Fraction as F


def evaluate(task,context):
    import gzip,json
    import numpy as np
    from lll.ilvis0_sharded_native import read,plain
    from lll.ilvis0_control_shards import _check_continue
    from lll.ilvis0_receipt_journal import durable_write
    from lll.ilvis0_coupled_map_controls import Allowance,domain
    from lll.ilvis0_transform_native import make_reference
    from lll.ilvis0_directional_force import calibrated_force,action
    case=read(context.input_path());spec=task['payload'];count=1 if spec['family']=='fixed' else 64
    limits=dict(setups=1,actions=1,oracles=count,checks=6*count)
    if (spec['limits']!=limits or case['configuration']['model']!=spec['model']
            or case['configuration']['profile']!=spec['profile']):
        raise ValueError('fixed source, candidate and finite component allowance required')
    events=[]
    def persist(record):
        _check_continue(context.root,context.manifest)
        context.save(f'reservation-{len(events)+1:03d}.json',record);events.append(record)
    budget=Allowance(limits,persist);box=domain(spec['family']);config=case['configuration']
    budget.reserve(dict(setups=1))
    reference=make_reference(config,case['theta'],case['dv'],case['dt'],**box)
    context.save('reference.json',reference.report())
    r=reference.parent;lower=[F(float(v))*F(float(c)) for v,c in zip(r.limits,box['lower'])]
    upper=[F(float(v))*F(float(c)) for v,c in zip(r.limits,box['upper'])]
    budget.reserve(dict(actions=1))
    flo,fhi=calibrated_force(case['dv'][0],case['dt'][0],
        list(map(list,zip(lower[12:15],upper[12:15]))),list(map(list,zip(lower[18:21],upper[18:21]))))
    bounds=action(lower[:3],upper[:3],flo,fhi,installation=np.asarray(config['initial_r']).tolist())
    left=list(map(F,bounds['lower']));right=list(map(F,bounds['upper']))
    left[2]+=F(config['gravity'])+lower[24];right[2]+=F(config['gravity'])+upper[24]
    widths=[b-a for a,b in zip(left,right)]
    seed=[2026102041,spec['model'],int(spec['profile']),('full','sector','fixed','gain-boundary').index(spec['family'])]
    rng=np.random.default_rng(np.random.SeedSequence(seed));mid=(box['lower']+box['upper'])/2
    points=[mid] if count==1 else [box['lower'],box['upper'],mid]+[
        rng.uniform(box['lower'],box['upper']) for _ in range(count-3)]
    records=[];margin=F(1,10000000000)
    for point in points:
        budget.reserve(dict(oracles=1,checks=6))
        actual=reference.acceleration.acceleration_at(point)
        gap=max([F(0)]+[a-F(float(v))-margin for a,v in zip(left,actual)]+[
            F(float(v))-b-margin for v,b in zip(actual,right)])
        records.append(dict(point=point,acceleration=actual,passed=gap==0,maximum_violation=str(gap)))
    artifact=context.directory/'probes.json.gz';artifact.parent.mkdir(parents=True,exist_ok=True)
    durable_write(artifact,gzip.compress(json.dumps(plain(records),sort_keys=True,separators=(',',':'),allow_nan=False).encode(),mtime=0))
    context.note_file(artifact)
    context.save('action.json',dict(bounds,acceleration_lower=list(map(str,left)),acceleration_upper=list(map(str,right))))
    old=2*F(float(reference.acceleration.change))
    return dict(identity=task['identity'],passed=all(r['passed'] for r in records),model=spec['model'],
        profile=spec['profile'],family=spec['family'],probes=count,work=budget.counts,seed=seed,
        acceleration_widths_mps2=list(map(float,widths)),old_isotropic_width_mps2=float(old),
        width_ratios=[float(v/old) if old else None for v in widths],
        maximum_point_violation=str(max(F(r['maximum_violation']) for r in records)),
        parameter_count=27,comparison_margin_mps2=float(margin),native_evaluations=0,original_reads=0,
        optimizer_starts=0,native_propagation_qualified=False,whole_program_roundoff_qualified=False,
        observational_coverage_qualified=False,scientific_decision='abstain')
