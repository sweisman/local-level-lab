# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check independent scale support before preparing new ESA candidate fits."""

import argparse
from contextlib import closing
import hashlib
import io
import itertools
import json
import math
import os
from pathlib import Path


FOLDER = 'docs/prediction-observed-development/'
PLAN = FOLDER+'ESA_COMPONENT_PREFLIGHT_PLAN.md'
FREEZE = FOLDER+'esa-component-preflight-freeze.json'
RESULT = FOLDER+'esa-component-preflight-result.json'
WIDTH = 120
RECORDS = 9168819
MAX_DECODE_PER_WINDOW = 241000
ACCEL_SCALES = (.0001,.001)
EARLIER_SHA = '4c42b5cf1c50be8e889a10734cdc9ba4aacf42b549ea57cbb2dfcadff1399e07'


def rate_slice(stream, header, row_count, *, lower, upper):
    """Read just the rates needed for a left-held training interval."""
    import numpy as np
    from .airquantumgrav import HEADER, records

    if (len(header)!=WIDTH or header.decode('ascii').split()!=HEADER.split()
            or type(row_count) is not int or row_count<2
            or not 0<=lower<upper<604800 or not math.isfinite(lower+upper)):
        raise ValueError('verified fixed-width documented header and ordered training range required')

    def row(index):
        raw=stream.read(WIDTH)
        if index>=row_count or len(raw)!=WIDTH or not raw.endswith(b'\n') or b'\n' in raw[:-1]:
            raise ValueError('unexpected fixed-width record boundary')
        return raw

    def timestamp(index):
        stream.seek(WIDTH*(index+1))
        time=float(row(index).split(maxsplit=1)[0])
        if not 0<=time<604800:
            raise ValueError('finite GPS seconds of week required at the probe')
        return time

    def search(target):
        lo,hi=0,row_count
        while lo<hi:
            mid=(lo+hi)//2
            if timestamp(mid)<target:
                lo=mid+1
            else:
                hi=mid
        return lo

    first=search(lower)
    last=search(upper)
    if last>=row_count or first>=row_count:
        raise ValueError('training queries beyond the original IMU support')
    if timestamp(first)>lower:
        first-=1
    if not 0<=first<last or last-first>MAX_DECODE_PER_WINDOW:
        raise ValueError('declared training packet allowance or support exceeded')
    closing_time=timestamp(last)
    stream.seek(WIDTH*(first+1))
    decoded=records(itertools.chain((header,), (row(i) for i in range(first,last))))
    sampled=np.fromiter(((r['gps_time_s'],*r['angular_rate_rads']) for r in decoded),
                        dtype=np.dtype((np.float64,4)),count=last-first)
    ts=np.r_[sampled[:,0],closing_time]
    elapsed=np.diff(ts)
    if not ts[0]<=lower<ts[1] or not ts[-2]<upper<=ts[-1] or np.any(elapsed<=0) or np.any(elapsed>.005):
        raise ValueError('selected packet boundaries, chronology or timing support differ')
    return ts,sampled[:,1:]


def selected_support(root, metadata, selected):
    import numpy as np
    from .airquantumgrav_inventory import IMU_NAME, METADATA, validate_context
    from .esa_motion_error_transfer import THRESHOLD_DEG_S
    from .maneuver_error_roots import turn_exposure
    from .receiver_route_information import SOURCE, _read_queries
    from .studies.artifacts import safe_path

    context=validate_context(**metadata)
    original=safe_path(root,str(Path(METADATA['inspection']).with_name(IMU_NAME)))
    source=safe_path(root,SOURCE)
    windows=selected['plan']['windows']
    if (selected['plan']['fit_authorized'] is not False or selected['plan']['confirmation_authorized'] is not False
            or len(windows)!=3 or any(w['group_id']!=context['group_id']
            or w['receiver_source_sha256']!=context['receiver_sha256'] for w in windows)
            or metadata['inspection']['records']!=RECORDS):
        raise ValueError('unchanged three development windows and documented frame count required')
    records=_read_queries(source,windows,context['receiver_sha256'],metadata['receiver_report']['epochs'])
    report={}
    with original.open('rb') as stream:
        start=os.fstat(stream.fileno())
        if start.st_size!=WIDTH*(RECORDS+1):
            raise ValueError('verified fixed-width byte count required')
        sha=hashlib.file_digest(stream,'sha256').hexdigest()
        if sha!=context['imu_source_sha256']:
            raise ValueError('opened original IMU differs from the verified source')
        stream.seek(0)
        header=stream.read(WIDTH)
        for name,rows in records.items():
            times=np.array([r['time_s'] for r in rows])
            ts,rate=rate_slice(stream,header,RECORDS,lower=times[0],upper=times[-1])
            dt=np.diff(ts)
            origin=ts[0]
            exposure=turn_exposure(dt,rate*dt[:,None],times[1:]-origin,
                previous_time=times[0]-origin,threshold_deg_s=THRESHOLD_DEG_S)
            report[name]=dict(earlier_queries=len(times),gyro_rows_decoded=len(rate),
                total_exposure=float(exposure.sum()),
                exposures_by_quarter=[dict(positive_epochs=int(np.count_nonzero(block)),
                                          exposure=float(block.sum()))
                                    for block in np.array_split(exposure,4)])
        end=os.fstat(stream.fileno())
        if (start.st_size,start.st_mtime_ns,start.st_ctime_ns)!=(end.st_size,end.st_mtime_ns,end.st_ctime_ns):
            raise ValueError('original IMU changed during verified reads')
    return report


def held_support(study, early):
    import numpy as np
    from .covariance_component_support import information
    from .esa_motion_error_transfer import DECAY_S, THRESHOLD_DEG_S
    from .esa_native_rolling_transfer import LAWS
    from .innovations_snapshot import restore
    from .maneuver_error_roots import roots,turn_exposure

    result={}
    for cut in (200,400):
        times=study.input(f'{cut}-forecast_times')
        with np.load(io.BytesIO(study.input(f'{cut}-interval',raw=True)),allow_pickle=False) as data:
            exposure=turn_exposure(data['dt'],data['theta'],times[cut:],
                   previous_time=times[cut-1],threshold_deg_s=THRESHOLD_DEG_S)
        basis=roots(times[cut:],exposure,previous_time=times[cut-1],decay_s=DECAY_S)
        result[str(cut)]={}
        for law in LAWS:
            identity=f'{cut}-{law}'
            report=study.artifact(identity,'factor-replay.json')
            op=restore(study.artifact(identity,'rolling-factors.npz',raw=True),
                expected_sha256=report['snapshot_sha256'],expected_configuration=report['configuration'],
                maximum_bytes=64*1024**2)
            right=np.zeros((3*len(times),360))
            right[3*cut:]=np.eye(360)
            # The position components are expressed in metres at the last
            # training receiver epoch, as in the original motion error replay.
            from .ilvis0_solver_position import physical_metric
            coords=np.asarray(study.input(identity+'-training-observations')['coordinates'])
            metric=np.tile(physical_metric(coords[-1:])[0],120)
            scale=early['scores'][law]['archived']['quadratic']/360.
            native=metric[:,None]*op.unwhiten(right)[3*cut:]*math.sqrt(scale)
            result[str(cut)][law]=[dict(reference_acceleration_sd_m_s2=s,
                **information(dict(native=native,persistent=s*basis['persistent'],maneuver=s*basis['maneuver'])))
                for s in ACCEL_SCALES]
    return result


def run(root,action):
    from . import esa_innovation_transfer as evidence
    from . import esa_motion_error_transfer as motion
    from . import esa_native_rolling_transfer as original
    from .airquantumgrav_inventory import METADATA
    from .ilvis0_control_shards import runtime_environment
    from .ilvis0_matched_observed_inputs import _write_equal
    from .receiver_route_information import SELECTION
    from .studies.artifacts import digest,encoded
    from .studies.closed import ClosedStudy
    from .studies.dependencies import source_closure

    with closing(ClosedStudy(root,'data/'+original.ID)) as study:
        if (study.completion['manifest_sha256']!=evidence.SOURCE_SHA
                or study.completion['state']!='complete'
                or any(not row['passed'] for row in study.rows.values())):
            raise ValueError('exact archived four-arm rolling study required')
        records={label:(root/name).read_bytes() for label,name in METADATA.items()}
        selection=(root/SELECTION).read_bytes()
        early=(root/motion.EARLY).read_bytes()
        if digest(early)!=EARLIER_SHA:
            raise ValueError('verified earlier native variance anchor required')
        own=Path(__file__).relative_to(root).as_posix()
        definition=encoded(dict(study=study.completion, selection_sha256=digest(selection),
            metadata={key:digest(raw) for key,raw in records.items()},earlier_score_sha256=EARLIER_SHA,
            sources={name:digest((root/name).read_bytes()) for name in source_closure(root,
                (own,PLAN,'analysis/tests/test_covariance_component_support.py','analysis/tests/test_esa_component_preflight.py'))},
            environment=runtime_environment(),reads=dict(imu_full_hash_passes=1,receiver_hash_passes=1,
                imu_training_rows_max=3*MAX_DECODE_PER_WINDOW,receiver_training_rows=2400),
            prospective_outcome_rows=0,protected_reads=0,native_calls=0,fit_starts=0,
            component_cases=8,acceleration_scales=ACCEL_SCALES))
        if action=='freeze':
            _write_equal(root/FREEZE,definition)
            return dict(freeze_sha256=digest(definition))
        if (root/FREEZE).read_bytes()!=definition:
            raise ValueError('frozen preflight policy or source metadata changed')
        known=held_support(study,json.loads(early))
        prospective=selected_support(root,{key:json.loads(raw) for key,raw in records.items()},json.loads(selection))
    output=encoded(dict(freeze_sha256=digest(definition),archived_information=known,
        preselected_training_exposure=prospective,prospective_outcome_rows=0,
        protected_reads=0,native_calls=0,fit_starts=0,scientific_decision='abstain'))
    _write_equal(root/RESULT,output)
    return dict(sha256=digest(output),existing_cuts=len(known),prospective_windows=len(prospective))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('freeze','replay'))
    print(json.dumps(run(Path.cwd(),parser.parse_args().action),sort_keys=True))
