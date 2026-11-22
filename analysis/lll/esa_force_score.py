# SPDX-License-Identifier: AGPL-3.0-or-later
"""Apply a coupled force-map score bound to the sealed ESA coefficient profile."""
from contextlib import closing
from fractions import Fraction
import json
from pathlib import Path


ID = 'esa-force-score-v1-20261119'
PLAN = 'docs/prediction-observed-development/ESA_FORCE_SCORE_PLAN.md'
SCORE = 'docs/prediction-observed-development/esa-linked-shared-score.json'
SCORE_SHA = 'e268397e5e1f8e8dc6139eb30c8f83cf16f1b6186b9d97efe4d44643679c5a80'
SCOPE = 'Exact signed force-map score on saved ESA 187 calibration boxes'
MODELS = ('sphere_still','flat_still')
BOXES = 63


def tasks():
    return [dict(identity=model,input_key=model,payload=dict(model=model),
                 limits=dict(native_calls=0,packet_visits=0,bound_calls=1,bound_steps=BOXES))
            for model in MODELS]


def force_transform(inputs):
    import numpy as np
    from .ilvis0_common_force_transform import ForceTransform
    from .ilvis0_shared_reference_terms import ReferenceErrors
    center,lo,hi = (np.asarray(inputs[key],dtype=float) for key in ('center','lower','upper'))
    reference = ReferenceErrors(inputs['configuration'],lo,hi,center,source_id=inputs['source_id'])
    transform = ForceTransform(reference)
    if transform.report()!=inputs['transform']:
        raise ValueError('exact archived force transform required')
    return transform


def evaluate(task,context):
    from itertools import product
    import numpy as np
    from .ilvis0_force_score_bound import AXES,bound

    if (context.manifest['scope']!=SCOPE
            or {key:value for key,value in task.items() if key not in ('index','shard')} not in tasks()):
        raise ValueError('exact recorded force-score task required')
    inputs = json.loads(context.input_path().read_bytes())
    transform = force_transform(inputs)
    center,lo,hi = (np.asarray(inputs[key],dtype=float) for key in ('center','lower','upper'))
    low,high = (tuple(map(Fraction,inputs['coefficients'][key]))
                for key in ('coefficient_lower','coefficient_upper'))
    context.charge(bound_calls=1,bound_steps=BOXES)
    result = bound(transform,low,high,maximum_boxes=BOXES,maximum_seconds=40.)
    weights = np.asarray([float((a+b)/2) for a,b in zip(low,high,strict=True)])
    corner_values = []
    for sides in product((False,True),repeat=len(AXES)):
        point = center.copy()
        for axis,right in zip(AXES,sides,strict=True):
            point[axis] = hi[axis] if right else lo[axis]
        corner_values.append(float(weights@transform.normalized_values_at(point)))
    result.update(passed=result['lower']<=min(0.,*corner_values)
                   and max(0.,*corner_values)<=result['upper'],
                  corner_values=corner_values,
                  normalized_independent_upper=inputs['coefficients']['linked_upper'],
                  full_aircraft_remainder_certified=False)
    return result


def main():
    from io import BytesIO
    import numpy as np
    from .esa_shared_profile import PRECHECK, PRECHECK_SHA
    from .studies.artifacts import atomic,digest,encoded
    from .studies.closed import ClosedStudy
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    root = Path.cwd()
    base = root/'data'/(ID+'-inputs')
    if base.exists() or (root/'data'/ID).exists():
        raise ValueError('use the existing force-score freeze')
    raw = (root/SCORE).read_bytes()
    if digest(raw)!=SCORE_SHA:
        raise ValueError('original signed coefficients required')
    groups = {row['model']:row['groups'][-1] for row in json.loads(raw)['rows']}
    records = {}
    with closing(ClosedStudy(root,PRECHECK)) as study:
        if study.completion['manifest_sha256']!=PRECHECK_SHA or not study.summary['passed']:
            raise ValueError('the matched prefix study is required')
        for model in MODELS:
            record = study.artifact(model,'reference.json')
            metadata = study.input(model+'-metadata')
            with np.load(BytesIO(study.input(model,raw=True)),allow_pickle=False) as inputs:
                vectors = {key:inputs[key].tolist() for key in ('center','lower','upper')}
            coefficients = groups[model]
            if coefficients['block']!='force':
                raise ValueError('force-transform coefficient block required')
            records[model] = dict(configuration=metadata['configuration'],**vectors,
                                  transform=record['transform'],source_id=record['parent']['source_id'],
                                  coefficients=coefficients)
    base.mkdir(parents=True)
    inputs = {'plan':PLAN,'original-scores':SCORE}
    for model,record in records.items():
        path = base/(model+'.json')
        atomic(path,encoded(record))
        inputs[model] = path.relative_to(root).as_posix()
    adapter = Path(__file__).relative_to(root).as_posix()
    definition = dict(id=ID,adapter=adapter,sources=source_closure(root,[adapter,PLAN]),
                      inputs=inputs,tasks=tasks(),scope=SCOPE,workers=2,threads=1,maximum_wall_s=80.)
    manifest = Definition.from_dict(definition,root).prepare(root)
    print(json.dumps(dict(study='data/'+ID,allowance=manifest['limits']),sort_keys=True))


if __name__=='__main__':
    main()
