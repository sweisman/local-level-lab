# SPDX-License-Identifier: AGPL-3.0-or-later
"""Score sealed common calibration columns with one shared value per column."""
from contextlib import closing
from fractions import Fraction
from io import BytesIO
from pathlib import Path

WITNESS_MANIFEST = '199aa293a49cf8738c3f6161e78165fe10f948f0d1e3f36f156e62224d26ad60'


def support(lower, upper, metric, columns):
    """Enclose signed score coefficients and compare linked and independent ranges."""
    import numpy as np

    lo, hi, metric, columns = (np.asarray(v,dtype=float) for v in (lower,upper,metric,columns))
    if (lo.ndim!=1 or hi.shape!=lo.shape or metric.shape!=lo.shape or columns.ndim!=2
            or len(columns)!=len(lo) or not len(lo) or not columns.shape[1]
            or any(not np.isfinite(v).all() for v in (lo,hi,metric,columns))
            or np.any(lo>hi) or np.any(metric<=0.)):
        raise ValueError('finite aligned score intervals and physical metric required')
    a,b = [Fraction(0)]*columns.shape[1], [Fraction(0)]*columns.shape[1]
    independent = Fraction(0)
    for low,high,scale,row in zip(lo,hi,metric,columns,strict=True):
        x = Fraction(float(low))*Fraction(float(scale))
        y = Fraction(float(high))*Fraction(float(scale))
        for index,value in enumerate(row):
            if value==0.:
                continue
            c = Fraction(float(value))
            left,right = (x*c,y*c) if c>=0 else (y*c,x*c)
            a[index] += left
            b[index] += right
            independent += max(abs(left),abs(right))
    linked = sum((max(abs(x),abs(y)) for x,y in zip(a,b,strict=True)),Fraction(0))
    return dict(linked=linked,independent=independent,lower=tuple(a),upper=tuple(b))


def score(root, profile_manifest):
    import numpy as np
    from .esa_shared_profile import ID, MODELS
    from .ilvis0_saved_prediction_audit import endpoint
    from .innovations_snapshot import restore
    from .shape_remainder_witness import ID as WITNESS, EARLIER
    from .state_space_directional_bound import adjoint_intervals
    from .studies.artifacts import digest
    from .studies.closed import ClosedStudy

    with closing(ClosedStudy(root,'data/'+ID)) as profile, closing(
            ClosedStudy(root,'data/'+WITNESS,store=profile.store)) as witness:
        if profile.completion['manifest_sha256']!=profile_manifest or not profile.summary['passed']:
            raise ValueError('complete hash-bound shared profiles required')
        if witness.completion['manifest_sha256']!=WITNESS_MANIFEST or not witness.summary['passed']:
            raise ValueError('exact sealed shape-direction witness required')
        shape = witness.input('shape-direction')
        snapshot = witness.input('later-operator',raw=True)
        if digest(snapshot)!=shape['factors_sha256']:
            raise ValueError('archived shape-direction weights must agree')
        operator = restore(snapshot,expected_sha256=shape['factors_sha256'],
                           expected_configuration=shape['configuration'],maximum_bytes=2**26)
        q = np.r_[np.zeros(3*EARLIER),shape['direction']]
        times = np.asarray(witness.input('forecast_times'))
        lo,hi = adjoint_intervals(operator,q)
        output = []
        for model in MODELS:
            raw = profile.artifact(model,'shared-profile.npz',raw=True)
            with np.load(BytesIO(raw),allow_pickle=False) as data:
                shared = data['shared']
                if shared.shape!=(len(q)//3,3,24) or not np.array_equal(data['times'],times):
                    raise ValueError('complete 24-column forecast profile required')
            metric = np.tile(shape['metric'],len(shared))
            rows = shared.reshape(len(q),24)
            groups = []
            for name,region in (('velocity_and_lever',slice(0,6)),('acceleration',slice(6,15)),
                                ('force',slice(15,24))):
                result = support(lo,hi,metric,rows[:,region])
                groups.append(dict(block=name,linked_upper=endpoint(result['linked'],True),
                                   independent_upper=endpoint(result['independent'],True),
                                   coefficient_lower=[str(v) for v in result['lower']],
                                   coefficient_upper=[str(v) for v in result['upper']]))
            output.append(dict(model=model,artifact_sha256=digest(raw),groups=groups))
        return dict(profile_manifest_sha256=profile_manifest,
                    witness_manifest_sha256=witness.completion['manifest_sha256'],
                    nominal_separation=shape['nominal'],rows=output,
                    full_aircraft_remainder_certified=False,scientific_decision='abstain')


def main():
    import argparse
    from .ilvis0_matched_observed_inputs import _write_equal
    from .studies.artifacts import digest,encoded

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest-sha256',required=True)
    args = parser.parse_args()
    root = Path.cwd()
    result = encoded(score(root,args.manifest_sha256))
    path = root/'docs/prediction-observed-development/esa-linked-shared-score.json'
    _write_equal(path,result)
    print(digest(result))


if __name__=='__main__':
    main()
