# SPDX-License-Identifier: AGPL-3.0-or-later
"""Shared saved-point accounting/input/native bindings; never reconstruct or refit."""


def audit_point(study,record,*,maximum_evaluations,work_allowance,bindings):
    from lll.studies.artifacts import encoded
    from lll.airquantumgrav_geographic_report import construction_counts
    from lll.compensated_prediction_release import case_recipe
    from lll.structured_noisy_training import limits
    identity=record['identity'];task=study.tasks[identity];envelope=study.envelope(identity)
    for name,sha in envelope['artifacts'].items():study.read(name,sha,raw=True)
    seed=record['payload']['draw_seed'];base='artifacts/'+identity+'/'
    if task['limits']!=work_allowance(seed):raise ValueError('separate native allowance changed')
    attempted=dict(native_calls=0,packet_visits=0)
    if base+'native-prepayment.json' in envelope['artifacts']:
        budget=study.artifact(identity,'native-prepayment.json')
        if budget['prepaid']!={k:envelope['charged'][k] for k in attempted}:
            raise ValueError('sealed prepaid charges differ')
        attempted=budget['attempted']
    if base+'diagnostic.json' not in envelope['artifacts']:return None,attempted
    d=study.artifact(identity,'diagnostic.json')
    if (not envelope['result']['diagnostic_complete'] or envelope['result']['evaluations']!=d['evaluations']):
        raise ValueError('diagnostic result and envelope differ')
    for name,limit,ident,complete in [
        ('evaluations.sqlite',dict(evaluations=maximum_evaluations),identity,False),
        ('construction.sqlite',limits(case_recipe(seed),'point')[1],identity,False),
        ('worker-build-journal.sqlite',dict(builds=2),'worker',True)]:
        counts=construction_counts(study.artifact(identity,name,raw=True),study.completion['manifest_sha256'],
            ident,limit,complete=complete)
        if name=='evaluations.sqlite' and counts['evaluations']!=d['evaluations']:
            raise ValueError('evaluation journal differs from diagnostic')
    for name,value in record['artifacts'].items():
        if encoded(study.artifact(identity,'reconstructed/'+name))!=encoded(value):
            raise ValueError('original input, training observations or error operator changed')
    meta=study.artifact(identity,'reconstructed/compilation.json');tm=meta['tangent'];nm=meta['noise_bridge']
    if (tm['source_sha256']!=bindings['wide_sha256'] or nm['source_sha256']!=bindings['bridge_sha256']
            or tm['compiler']!=bindings['compiler'] or nm['compiler']!=bindings['compiler']
            or tm['internal_mantissa_bits']<=53 or nm['internal_mantissa_bits']<=53):
        raise ValueError('compensated native/noise calculation or compiler changed')
    return d,attempted
