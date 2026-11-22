# SPDX-License-Identifier: AGPL-3.0-or-later
"""Earlier-to-later replay of motion-dependent covariance alternatives on ESA 187."""

import argparse
from contextlib import closing
import gzip
import io
import json
import math
from pathlib import Path


FOLDER = 'docs/prediction-observed-development/'
PLAN = FOLDER+'ESA_MOTION_ERROR_LAW_PLAN.md'
FREEZE = FOLDER+'esa-motion-error-law-freeze.json'
EARLY = FOLDER+'esa-motion-error-law-earlier.json'
RESULT = FOLDER+'esa-motion-error-law-result.json'
THRESHOLD_DEG_S = 1.
DECAY_S = 15.
ACCEL_STD_M_S2 = .001
ARMS = ('archived', 'persistent', 'maneuver', 'both')


def window(study, cut, rows, score):
    import numpy as np
    from .esa_changing_drift_transfer import _coordinates
    from .esa_native_rolling_transfer import LAWS, matched_window
    from .future_error_sensitivity import spectrum
    from .ilvis0_precision_value import longitude_residual
    from .ilvis0_solver_position import physical_metric
    from .innovations_snapshot import restore
    from .maneuver_error_roots import roots, turn_exposure
    from .studies.artifacts import digest, encoded

    training=json.loads(gzip.decompress(study.input(f'{cut}-training',raw=True)))
    times=study.input(f'{cut}-forecast_times')
    origin=study.input(f'{cut}-saved-input-binding')['time_origin_s']
    with np.load(io.BytesIO(study.input(f'{cut}-interval',raw=True)),allow_pickle=False) as interval:
        exposure=turn_exposure(interval['dt'],interval['theta'],times[cut:],
            previous_time=times[cut-1],threshold_deg_s=THRESHOLD_DEG_S)
    modes=roots(times[cut:],exposure,previous_time=times[cut-1],decay_s=DECAY_S)
    modes['both']=np.column_stack((modes['persistent'],modes['maneuver']))
    modes['archived']=np.zeros((360,1))
    metric=physical_metric(_coordinates(training[-1:]))[0]
    held=matched_window(rows,training,times,origin=origin)
    if len(held)!=120 or digest(encoded(held))!=score['held_receiver_sha256']:
        raise ValueError('original held-out receiver windows required')
    actual=_coordinates(held)
    work={}
    for law in LAWS:
        identity=f'{cut}-{law}'
        saved=study.input(identity+'-conditional')
        memo=study.artifact(identity,'factor-replay.json')
        operator=restore(study.artifact(identity,'rolling-factors.npz',raw=True),
            expected_sha256=memo['snapshot_sha256'],
            expected_configuration=saved['full_operator_configuration'], maximum_bytes=64*1024**2)
        residual=actual-np.asarray(saved['conditional_receiver_mean'])
        residual[:,1]=longitude_residual(residual[:,1])
        noise=np.zeros((3*len(times),360))
        noise[cut*3:]=np.eye(360)
        lower=np.tile(metric,120)[:,None]*operator.unwhiten(noise)[cut*3:]
        signed=(residual*metric).ravel()
        logdet=2*float(np.log(np.diag(lower)).sum())
        arms={}
        for arm in ARMS:
            point=spectrum(lower,signed,modes[arm]).score(ACCEL_STD_M_S2)
            arms[arm]=dict(quadratic=point['quadratic'],logdet=logdet+point['logdet_change'])
        if not np.isclose(arms['archived']['quadratic'],score['scores'][law]['squared_standardized_error'],
                          rtol=1e-12,atol=1e-12):
            raise ValueError('archived conditional score must verify exactly within numeric tolerance')
        work[law]=arms
    return dict(positive_exposure_count=int(np.count_nonzero(exposure)),
                exposure_total=float(exposure.sum()), exposures=exposure.tolist(),scores=work)


def straight_control(root,store):
    import numpy as np
    from . import esa_maneuver_pairs as selected
    from .esa_native_rolling_transfer import LATER_SOURCE, LATER_SOURCE_SHA, matched_window
    from .studies.artifacts import digest
    from .studies.closed import ClosedStudy

    receipt=(root/selected.SELECTION).read_bytes()
    if (digest(receipt)!='8e65babaf0abe267b2ee8fa9a6228e31b0fcf3ea6d81b1a811d5972a3174187e'
            or json.loads(receipt)['selected']['turn_centres']):
        raise ValueError('sealed straight-flight motion selection required')
    with closing(ClosedStudy(root,selected.STUDY,store=store)) as study, closing(
            ClosedStudy(root,LATER_SOURCE,store=store)) as receiver:
        if (study.completion['manifest_sha256']!=selected.MANIFEST or study.rows[selected.TASK]['passed'] is not True
                or receiver.completion['manifest_sha256']!=LATER_SOURCE_SHA
                or receiver.manifest['inputs']['scoring']['sha256']!=selected.SCORING_SHA):
            raise ValueError('exact earlier long straight-flight control required')
        forecast=study.artifact(selected.TASK,'conditional-forecast.json')
        times=study.input('weighted-forecast')['times_s']
        cut=selected.CUT
        training=json.loads(gzip.decompress(study.input('training',raw=True)))
        rows=json.loads(gzip.decompress(receiver.input('scoring',raw=True)))
        origin=study.input('saved-input-binding')['time_origin_s']
        held=matched_window(rows,training,times,origin=origin)
        height=np.asarray([row['height_m'] for row in held])-np.asarray(forecast['conditional_receiver_mean'])[:,2]
        elapsed=np.asarray(times[cut:])-times[cut-1]
        mode=.5*elapsed**2
        best=float(mode@height/(mode@mode))
        remaining=height-best*mode
        return dict(epochs=len(held),fitted_acceleration_m_s2=best,
            original_height_rms_m=float(np.sqrt(np.mean(height**2))),
            residual_height_rms_m=float(np.sqrt(np.mean(remaining**2))),
            fraction_squared_error_removed=float(1-remaining@remaining/(height@height)))


def run(root,action):
    from . import esa_innovation_transfer as evidence
    from . import esa_native_rolling_transfer as original
    from .ilvis0_control_shards import runtime_environment
    from .ilvis0_matched_observed_inputs import _write_equal
    from .studies.artifacts import digest,encoded
    from .studies.closed import ClosedStudy
    from .studies.dependencies import source_closure

    with closing(ClosedStudy(root,'data/'+original.ID)) as study:
        if study.completion['manifest_sha256']!=evidence.SOURCE_SHA or study.completion['state']!='complete':
            raise ValueError('closed exact native rolling factors required')
        own=Path(__file__).relative_to(root).as_posix()
        frozen=encoded(dict(study_completion=study.completion,threshold=THRESHOLD_DEG_S,
            decay_s=DECAY_S,acceleration_std=ACCEL_STD_M_S2,arms=ARMS,
            sources={name:digest((root/name).read_bytes()) for name in source_closure(
                root,(own,PLAN,'analysis/tests/test_maneuver_error_roots.py'))},
            environment=runtime_environment(),original_scores=[evidence.EARLY_SCORE_SHA,evidence.LATE_SCORE_SHA],
            spectra=16,geometry_fit_starts=0,native_calls=0,protected_reads=0))
        if action=='freeze':
            _write_equal(root/FREEZE,frozen)
            return dict(freeze_sha256=digest(frozen))
        if (root/FREEZE).read_bytes()!=frozen:
            raise ValueError('frozen motion covariance policy or sources changed')
        if action=='earlier':
            prior=(root/original.EARLIER_REPORT).read_bytes()
            if digest(prior)!=evidence.EARLY_SCORE_SHA:
                raise ValueError('original earlier score changed')
            receiver=json.loads(gzip.decompress(study.input('400-training',raw=True)))
            earlier=window(study,200,receiver,json.loads(prior))
            report=dict(**earlier,later_opened=False)
            target=EARLY
        else:
            raw=(root/EARLY).read_bytes()
            earlier=json.loads(raw)
            prior=(root/original.REPORT).read_bytes()
            if (earlier['freeze_sha256']!=digest(frozen) or earlier['later_opened'] is not False
                    or digest(prior)!=evidence.LATE_SCORE_SHA):
                raise ValueError('bound earlier covariance scores required before later scoring')
            with closing(ClosedStudy(root,original.LATER_SOURCE,store=study.store)) as source:
                if source.completion['manifest_sha256']!=original.LATER_SOURCE_SHA:
                    raise ValueError('exact original late scoring source required')
                receiver=json.loads(gzip.decompress(source.input('training',raw=True)))
            later=window(study,400,receiver,json.loads(prior))
            comparison={}
            for law in original.LAWS:
                comparison[law]={}
                for arm in ARMS:
                    old=earlier['scores'][law][arm]['quadratic']
                    new=later['scores'][law][arm]
                    if old<=0:
                        raise ValueError('positive earlier score required for common scale')
                    scale=old/360.
                    q=new['quadratic']/scale
                    comparison[law][arm]=dict(later_mean_standardized_error=q/360.,
                        held_out_negative_log_score=(q+new['logdet']+
                            360*math.log(2*math.pi*scale))/2.,earlier_scale=scale)
            report=dict(**later,earlier_sha256=digest(raw),comparison=comparison,
                        straight_control=straight_control(root,study.store))
            target=RESULT
    payload=encoded(dict(**report,freeze_sha256=digest(frozen),geometry_fit_starts=0,
                         native_calls=0,protected_reads=0,scientific_decision='abstain'))
    _write_equal(root/target,payload)
    return dict(path=target,sha256=digest(payload))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('freeze','earlier','compare'))
    print(json.dumps(run(Path.cwd(),parser.parse_args().action),sort_keys=True))
