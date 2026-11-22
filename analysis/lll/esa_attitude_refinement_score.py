# SPDX-License-Identifier: AGPL-3.0-or-later
"""Refine the high-bound pieces of the sealed ESA attitude cover."""

from contextlib import closing
import json
from pathlib import Path

from .esa_attitude_cover_score import STEPS, attitude_cover
from .ilvis0_physical_partition import audit, split


ID = 'esa-attitude-refinement-score-v1-20261119'
PLAN = 'docs/prediction-observed-development/ESA_ATTITUDE_REFINEMENT_SCORE_PLAN.md'
SCOPE = 'Refinement of the eight high-bound ranges in the sealed ESA attitude cover'
PARENT_SHA = '649c544016da9ab9e812b7a769097330ec6464e81c2e642fd13586319d9f96f8'
RANGES = {'sphere_still': (4,5,6,7), 'flat_still': (0,1,2,3)}
AXES = (2,0)
CELLS = 4


def tasks():
    return [dict(identity=f'{model}-{index}', input_key=model,
                 payload=dict(model=model,index=index),
                 limits=dict(native_calls=0,packet_visits=0,
                             bound_calls=CELLS,bound_steps=CELLS*STEPS))
            for model,indices in RANGES.items() for index in indices]


def refine_range(cell):
    partition = split(cell['lower'],cell['upper'],axes=AXES)
    if audit(partition,cell['lower'],cell['upper'],axes=AXES)['children']!=CELLS:
        raise ValueError('each selected range must retain four closed children')
    return partition


def collect(root):
    """Reconstruct maximum bounds from the verified complete cover."""
    from .studies.closed import ClosedStudy

    summaries = []
    with closing(ClosedStudy(root,'data/'+ID)) as study:
        if (not study.summary['passed'] or study.summary['completed']!=len(tasks())
                or set(study.rows)!={t['identity'] for t in tasks()}):
            raise ValueError('all eight verified refinement results required')
        for model,indices in RANGES.items():
            prior = study.input(model+'-cover')
            parent = prior['support']
            rows = [{'parent_index':r['index'],'cell_index':None,'upper':r['upper']}
                    for r in parent['rows'] if r['index'] not in indices]
            for index in indices:
                identity = f'{model}-{index}'
                cell = prior['cover']['cells'][index]
                partition = study.artifact(identity,'subdivision.json')
                audit(partition,cell['lower'],cell['upper'],axes=AXES)
                result = study.artifact(identity,'refined-support.json')
                if (result['parent_index']!=index or result['previous_upper']!=parent['rows'][index]['upper']
                        or result['nominal_separation']!=parent['nominal_separation']
                        or result['retained']!=parent['rows'][index]['members']
                        or tuple(row['index'] for row in result['rows'])!=tuple(range(CELLS))
                        or result['upper']!=max(row['upper'] for row in result['rows'])
                        or result['upper']>result['previous_upper']):
                    raise ValueError('each replacement must be a complete certified refinement')
                rows.extend(dict(parent_index=index,cell_index=row['index'],upper=row['upper'],
                                 success=row['success']) for row in result['rows'])
            summaries.append(dict(model=model,previous_upper=parent['upper'],
                upper=max(row['upper'] for row in rows),
                nominal_separation=parent['nominal_separation'],rows=rows))
        return dict(rows=summaries,manifest_sha256=study.completion['manifest_sha256'],
                    scientific_decision='abstain')


def evaluate(task, context):
    from .esa_attitude_cover_score import score_cells

    declared = {k:v for k,v in task.items() if k not in ('shard','index')}
    if context.manifest['scope']!=SCOPE or declared not in tasks():
        raise ValueError('exact registered ESA cover-refinement task required')
    model, index = (task['payload'][n] for n in ('model','index'))

    def read(suffix):
        return json.loads(context.input_path(model+suffix).read_bytes())

    force = read('-force')
    cover = attitude_cover(force['lower'],force['upper'])
    frozen = read('-cover')
    parent = read(f'-range-{index}')
    parent_cell = cover['cells'][index]
    prior = frozen['support']['rows'][index]
    if (cover!=frozen['cover'] or parent['index']!=index or prior['index']!=index
            or parent['upper']!=prior['upper'] or parent['members']!=prior['members']
            or parent['cuts']['physical_lower']!=parent_cell['lower']
            or parent['cuts']['physical_upper']!=parent_cell['upper']
            or prior['upper']<=frozen['support']['nominal_separation']/2):
        raise ValueError('unchanged high-bound parent range required')
    partition = refine_range(parent_cell)
    context.save('subdivision.json',partition)
    result = score_cells(context,model,partition['children'],parent=parent)
    context.save('refined-support.json',dict(result,parent_index=index))
    return dict(passed=True,cells=len(result['rows']),upper=result['upper'],
                previous_upper=result['previous_upper'],linked_points_checked=len(result['retained']),
                fit_starts=0,later_observations_used=0,map_allowance_qualified=False,
                unshared_error_qualified=False,scientific_decision='abstain')


def prepare(root):
    from .esa_attitude_cover_score import ID as PARENT
    from .studies.artifacts import atomic, encoded
    from .studies.closed import ClosedStudy
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    base = root/'data'/(ID+'-inputs')
    if base.exists() or (root/'data'/ID).exists():
        raise ValueError('use the existing refinement freeze')
    staged = {}
    with closing(ClosedStudy(root,'data/'+PARENT)) as prior:
        if prior.completion['manifest_sha256']!=PARENT_SHA or not prior.summary['passed']:
            raise ValueError('complete certified parent cover required')
        staged['later-operator.npz'] = prior.input('later-operator',raw=True)
        for model,indices in RANGES.items():
            for suffix, ext in (('', '.npz'), ('-weights','.npz'), ('-settings','.json'),
                                ('-force','.json'), ('-first-sample','.json'), ('-cuts','.json'),
                                ('-witnesses','.json'), ('-reference','.json'),
                                ('-products','.json'), ('-parent','.json')):
                staged[model+suffix+ext] = prior.input(model+suffix,raw=True)
            cover = prior.artifact(model,'cover.json')
            support = prior.artifact(model,'cover-support.json')
            relevant = tuple(row['index'] for row in support['rows']
                             if row['upper']>support['nominal_separation']/2)
            if relevant!=indices:
                raise ValueError('frozen refinement set must cover every high-bound range')
            staged[model+'-cover.json'] = encoded(dict(cover=cover,support=support))
            for index in indices:
                staged[f'{model}-range-{index}.json'] = prior.artifact(model,f'cell-{index}.json',raw=True)
    base.mkdir(parents=True)
    inputs = {'plan': PLAN}
    for name,payload in staged.items():
        path = base/name
        atomic(path,payload)
        inputs[path.stem] = path.relative_to(root).as_posix()
    adapter = Path(__file__).relative_to(root).as_posix()
    manifest = Definition.from_dict(dict(id=ID,adapter=adapter,
        sources=source_closure(root,[adapter,PLAN]),inputs=inputs,tasks=tasks(),scope=SCOPE,
        workers=4,threads=1,maximum_wall_s=120.),root).prepare(root)
    print(json.dumps(dict(study=ID,limits=manifest['limits']),sort_keys=True))


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('prepare','report'),nargs='?',default='prepare')
    action = parser.parse_args().action
    if action=='report':
        print(json.dumps(collect(Path.cwd()),sort_keys=True))
    else:
        prepare(Path.cwd())
