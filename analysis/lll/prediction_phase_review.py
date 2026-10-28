# SPDX-License-Identifier: AGPL-3.0-or-later
"""One bounded saved-fit review, without simulation, fitting or native loading."""
import csv
import io
import json
import time
from pathlib import Path

from .studies.artifacts import digest, encoded
from .studies.closed import ClosedStudy


def identities(study, seed):
    """Two processing cases, two starts, failing and preceding seed; one stop."""
    chosen = []
    for name, task in study.tasks.items():
        p = task['payload']; case = p['case']
        if name not in study.rows or p['draw_seed'] not in (seed - 1, seed):
            continue
        if case['law'] == 'increment' and (
                case['model'] == 'sphere_rotating' or
                (p['draw_seed'] == seed and case['model'] == 'flat_still'
                 and case['profile'] == 0 and case['start'] == 0)):
            chosen.append(name)
    if not chosen or len(chosen) > 24:
        raise ValueError('one nonempty selection of at most 24 saved records required')
    return sorted(chosen)


def read_selected(study, selected, *, maximum_wall_s=600):
    """Read only declared, hash-checked records; never invoke an evaluator."""
    if not selected or len(selected) > 24 or len(set(selected)) != len(selected):
        raise ValueError('one unique nonempty selection of at most 24 records required')
    if not 0 < maximum_wall_s <= 600:
        raise ValueError('review ceiling must not exceed 600 seconds')
    deadline = time.monotonic() + maximum_wall_s
    records = []
    for name in selected:
        if time.monotonic() >= deadline:
            raise TimeoutError('saved-results review allowance exhausted')
        envelope = study.envelope(name)
        fit_path = 'artifacts/' + name + '/fit.json'
        fit = study.artifact(name, 'fit.json') if fit_path in envelope['artifacts'] else None
        records.append(dict(identity=name, case=study.tasks[name]['payload'],
                            result=envelope['result'], fit=fit))
    return dict(version='prediction-phase-saved-review-v1', records=records,
                manifest_sha256=study.completion['manifest_sha256'],
                summary_sha256=study.completion['summary_sha256'],
                optimizer_starts=0, new_noise_draws=0, native_calls=0,
                maximum_wall_s=maximum_wall_s, numerical_threads=1)


def clock_geometry(fit, times_s, dt_s, *, expected_dt_sha256, expected_times_sha256):
    """Locate saved queries on a hash-verified clock, without generating data.

    Reconstructed timestamps are acceptable only when their little-endian float64
    bytes match the original input binding. Proximity alone establishes neither
    a derivative error nor the cause of a solver failure.
    """
    import bisect
    import math
    import statistics
    import struct
    if (not isinstance(times_s,(list,tuple)) or not 1<=len(times_s)<=10000
            or not isinstance(dt_s,(list,tuple)) or not 1<=len(dt_s)<=2000000
            or any(type(v) not in (int,float) or not math.isfinite(v) for v in (*times_s,*dt_s))
            or any(v<=0 for v in dt_s) or any(b<=a for a,b in zip(times_s,times_s[1:]))):
        raise ValueError('bounded finite increasing queries and positive interval durations required')
    hashes={name:digest(struct.pack('<'+str(len(values))+'d',*values))
            for name,values in (('dt',dt_s),('times',times_s))}
    if hashes!={'dt':expected_dt_sha256,'times':expected_times_sha256}:
        raise ValueError('clock arrays differ from saved input hashes')
    try:offset=fit['parameters']['time_offset']
    except (KeyError,TypeError) as exc:raise ValueError('saved fitted time offset required') from exc
    if type(offset) not in (int,float) or not math.isfinite(offset):
        raise ValueError('finite fitted time offset required')
    endpoints=[0.]
    for dt in dt_s:
        end=endpoints[-1]+dt
        if not math.isfinite(end) or end<=endpoints[-1]:raise ValueError('invalid accumulated clock')
        endpoints.append(end)
    distances=[];indices=[]
    for time_s in times_s:
        query=time_s+offset
        if not endpoints[0]<=query<=endpoints[-1]:raise ValueError('query outside saved clock support')
        at=bisect.bisect_left(endpoints,query)
        indices.append(max(0,at-1))
        nearest=min(endpoints[max(0,at-1):at+1],key=lambda end:abs(query-end))
        distances.append(query-nearest)
    absolute=list(map(abs,distances))
    return dict(version='saved-clock-geometry-v1',time_offset_s=offset,
        query_count=len(times_s),packet_count=len(dt_s),array_sha256=hashes,
        signed_distance_s=distances,interval_indices=indices,minimum_absolute_distance_s=min(absolute),
        median_absolute_distance_s=statistics.median(absolute),maximum_absolute_distance_s=max(absolute),
        arithmetic='float64 cumulative interval durations and saved query times',
        proximity_proves_failure_cause=False,numerical_starts=0,native_calls=0,new_noise_draws=0)


def review_clock(root, prefix, selected):
    """Review at most 24 saved fits; reconstruct only hash-bound clock metadata."""
    study=ClosedStudy(root,prefix)
    try:
        saved=read_selected(study,selected)
        rate=study.input('population')['descriptor']['recipe']['rate_hz']
        if type(rate) is not int or rate not in (300,600):raise ValueError('supported declared sample rate required')
        rows=[]
        for record in saved['records']:
            identity=record['identity'];fit=record['fit']
            if fit is None:raise ValueError('saved fitted point required for clock review')
            binding=study.artifact(identity,'input-binding.json')
            n=binding['native_packets']
            if type(n) is not int or not 1<=n<=2000000:raise ValueError('bounded packet count required')
            # This regenerates no inertial, position, noise or truth measurements.
            # The stored hashes must establish the exact reconstructed clock bytes.
            dt=[(i+1)/rate-i/rate for i in range(n)]
            times=study.artifact(identity,'forecast.json')['times_s']
            geometry=clock_geometry(fit,times,dt,
                expected_dt_sha256=binding['full_array_sha256']['dt'],
                expected_times_sha256=binding['full_array_sha256']['times'])
            rows.append(dict(identity=identity,fit_sha256=study.envelope(identity)['artifacts'][
                'artifacts/'+identity+'/fit.json'],converged=fit['converged'],
                evaluations=fit['evaluations'],stability_probe=fit['stability_probe'],geometry=geometry))
        return dict(version='saved-clock-review-v1',manifest_sha256=saved['manifest_sha256'],
            summary_sha256=saved['summary_sha256'],rows=rows,optimizer_starts=0,
            native_calls=0,new_noise_draws=0,original_reads=0,protected_reads=0,
            original_fit_labels_unchanged=True,proximity_proves_failure_cause=False)
    finally:study.close()


def replay_linear_probe(fit, *, reserve):
    """One charged replay of saved local algebra, never a new nonlinear fit."""
    import numpy as np
    from scipy.optimize import lsq_linear
    try:
        local=fit['local_linearization'];names=local['active_parameters']
        point=np.asarray(local['normalized_parameters'],float)
        residual=np.asarray(local['residual'],float);jac=np.asarray(local['jacobian'],float)
    except (KeyError,TypeError,ValueError) as exc:raise ValueError('complete saved linearization required') from exc
    if (not callable(reserve) or not isinstance(names,list) or len(set(names))!=len(names)
            or 'time_offset' not in names or point.shape!=(len(names),) or not 1<=len(names)<=27
            or residual.ndim!=1 or not 1<=len(residual)<=3600 or jac.shape!=(len(residual),len(names))
            or any(not np.all(np.isfinite(v)) for v in (point,residual,jac))
            or np.any(abs(point)>1.) or type(fit.get('converged')) is not bool):
        raise ValueError('finite complete saved columns, normalized bounds and label required')
    reserve()
    correction=lsq_linear(jac,-residual,bounds=(-1-point,1-point),method='bvls',tol=1e-10,max_iter=100)
    predicted=residual+jac@correction.x
    cost=float(residual@residual);predicted_cost=float(predicted@predicted)
    return dict(linear_success=bool(correction.success),linear_message=str(correction.message),
        correction=correction.x.tolist(),active_parameters=list(names),
        normalized_step=float(np.linalg.norm(correction.x)),original_cost=cost,
        predicted_cost=predicted_cost,predicted_cost_change=abs(predicted_cost-cost)/max(cost,predicted_cost,1.),
        converged=fit['converged'],labels_changed=False,linear_solves=1,
        nonlinear_fit_starts=0,native_calls=0,new_noise_draws=0)


def linear_timing_geometry(fit, *, times_s, dt_s, time_offset_scale,
                          expected_dt_sha256, expected_times_sha256, reserve):
    """Interpret a saved linear correction only after its saved metrics replay."""
    import math
    if (type(time_offset_scale) not in (int,float) or not math.isfinite(time_offset_scale)
            or time_offset_scale<=0):raise ValueError('positive saved time-offset scale required')
    hashes=dict(expected_dt_sha256=expected_dt_sha256,expected_times_sha256=expected_times_sha256)
    original=clock_geometry(fit,times_s,dt_s,**hashes)
    try:saved=fit['stability_probe'];expected=[saved['normalized_parameter_step'],saved['predicted_cost_change']]
    except (KeyError,TypeError) as exc:raise ValueError('saved ordinary stability probe required') from exc
    if any(type(v) not in (int,float) or not math.isfinite(v) or v<0 for v in expected):
        raise ValueError('finite saved probe metrics required')
    replay=replay_linear_probe(fit,reserve=reserve)
    matches=replay['linear_success'] and all(math.isclose(a,b,rel_tol=1e-7,abs_tol=1e-12)
        for a,b in zip(expected,[replay['normalized_step'],replay['predicted_cost_change']]))
    result=dict(replay=replay,replay_matches_saved=matches,original_clock=original,
        labels_changed=False,native_calls=0,new_noise_draws=0,nonlinear_fit_starts=0)
    if not matches:return result
    step=replay['correction'][replay['active_parameters'].index('time_offset')]*time_offset_scale
    shifted=dict(parameters=dict(time_offset=fit['parameters']['time_offset']+step))
    moved=clock_geometry(shifted,times_s,dt_s,**hashes)
    crossings=sum(a!=b for a,b in zip(original['interval_indices'],moved['interval_indices']))
    return dict(result,time_offset_step_s=step,proposed_clock=moved,
        queries_crossing_boundaries=crossings,query_count=len(times_s))


def run(root, request_path):
    """Execute the predeclared selection once and preserve an immutable snapshot."""
    from .evidence_snapshot import create, publish, sha
    root = Path(root).resolve(); request_path = Path(request_path)
    request = json.loads((root / request_path).read_bytes())
    for name, expected in request['sources'].items():
        if sha(root / name) != expected:
            raise ValueError('review source changed after selection freeze')
    data = root / request['output']; data.mkdir(parents=True, exist_ok=True)
    # Charge this one review before inspecting any saved fit; no retries.
    with (data / 'review-start.json').open('xb') as f:
        f.write(encoded(dict(request_sha256=sha(root / request_path), reviews_charged=1)))
    study = ClosedStudy(root, request['study'])
    try:
        if (study.completion != request['completion'] or
                identities(study, request['failed_seed']) != request['identities']):
            raise ValueError('closed study or declared selection changed')
        report = read_selected(study, request['identities'])
        inputs = {request_path.as_posix(): sha(root / request_path)}
        for name in ('manifest.json', 'completion.json', 'summary.json', 'stop-request.json'):
            relative = request['study'] + '/' + name
            inputs[relative] = sha(root / relative)
        for name in request['identities']:
            row = study.rows[name]; relative = request['study'] + '/' + row['artifact']
            inputs[relative] = row['artifact_sha256']
            envelope = study.envelope(name)
            fit_path = 'artifacts/' + name + '/fit.json'
            if fit_path in envelope['artifacts']:
                inputs[request['study'] + '/' + fit_path] = envelope['artifacts'][fit_path]
        stream = io.StringIO(newline=''); writer = csv.writer(stream, lineterminator='\n')
        writer.writerow(['identity', 'numerical_pass', 'training_cost', 'error_type'])
        for record in report['records']:
            fit = record['fit'] or {}; result = record['result']
            writer.writerow([record['identity'], fit.get('converged', False),
                             fit.get('residual_sum_squares', ''), result.get('error_type', '')])
        create(root, data, version=report['version'], inputs=inputs, sources=request['sources'],
               outputs={'diagnosis.json': encoded(report), 'results.csv': stream.getvalue().encode(),
                        'review-start.json': (data / 'review-start.json').read_bytes()},
               summary=dict(records=len(report['records']), fitted_records=sum(r['fit'] is not None for r in report['records']),
                            optimizer_starts=0, new_noise_draws=0, native_calls=0, reviews_charged=1))
        publish(data, root / request['publication'])
        return report
    finally:
        study.close()


def publish_phase(root, prefix, *, qualification):
    """Package the unchanged audited phase with the manifest's relative plan key.

    The frozen publisher passes an absolute Path to a packager requiring a
    relative string. This reporting adapter changes no scientific dependency.
    """
    from .prediction_calibration_report import inspect, render, result_csv
    from .prediction_calibration_study import qualification_sources
    from .studies.qualification import checked
    from .studies.artifacts import atomic, safe_path
    from .studies.native_publication import include_native_caches
    from .airquantumgrav_inventory import environment
    from .ilvis0_control_publication import publish as package, check
    root = Path(root).resolve(); data = safe_path(root, prefix)
    request, tests = checked(root, qualification, sources=qualification_sources(root),
        environment=environment(), minimum_tests=62, required_tests=[
            'test_handoff_rejects_unexecuted_calibration_draws',
            'test_calibration_adapter_metadata_loads_in_real_frozen_namespace',
            'test_validation_futility_stops_at_fifth_distinct_family_not_four'])
    report = inspect(root, prefix)
    if report['role'] != 'calibration' or report['calibration'] is not None:
        raise ValueError('this reporting adapter is limited to the stopped calibration')
    public = root / 'docs/prediction-calibration'
    if (public / 'evidence-receipt.json').exists():
        raise ValueError('immutable publication already exists')
    plan = 'docs/prediction-score-qualification/EXECUTION_PLAN.md'
    package(data, public, render(report), plan=plan)
    if report['native_assets']:
        include_native_caches(root, data, public,
            entries=[dict(path=k, sha256=v) for k, v in sorted(report['native_assets'].items())],
            maximum_bytes=64*1024**2)
    extras = {'results.csv': result_csv(report).encode(),
        'artifacts/publication/verified-report.json': encoded(report),
        'artifacts/publication/qualification-request.json': request,
        'artifacts/publication/qualification-report.xml': tests,
        'artifacts/publication/reporting-adapter.py': Path(__file__).read_bytes(),
        'stop-request.json': (data / 'stop-request.json').read_bytes()}
    for name in ('CALIBRATION_PLAN.md', 'CALIBRATION_TARGETS_PLAN.md', 'CAMPAIGN_SIZING.md'):
        extras[name] = f'# Related plan\n\nSee [{name}](../prediction-score-qualification/{name}).\n'.encode()
    receipt = json.loads((public / 'evidence-receipt.json').read_bytes())
    for name, raw in extras.items():
        atomic(public / name, raw); receipt['artifacts'][name] = digest(raw)
    atomic(public / 'evidence-receipt.json', encoded(receipt)); check(data, public)
    if encoded(inspect(root, public.relative_to(root).as_posix())) != encoded(report):
        raise ValueError('published replay differs from closed source')
    return dict(publication=public.relative_to(root).as_posix(),
                artifacts=len(receipt['artifacts']), returned=report['returned_outcomes'],
                numerical_passes=report['numerically_converged'], native_calls=0, optimizer_starts=0)
