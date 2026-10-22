# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite full-history staged feasibility controls, with no aircraft inputs.

The fixed metre allowances are software assumptions, not device performance.
Future truth is evaluated only after the prediction has been saved.
"""
from fractions import Fraction as F


def recipe():
    return dict(packets=96000, clock_limit_s=1., training_s=[2., 10., 30., 180., 290.],
        stage_sizes=[3, 2], future_s=438., center=[0.] * 27, lower=[-1.] * 27, upper=[1.] * 27,
        noise_allowance_m=1., width_target_m=[20., 20., 50.], maximum_bound_seconds=7200.,
        truth=[.25 if i == 25 else .05 * (i % 3 - 1) for i in range(27)])


def validate_recipe(value):
    if value != recipe():
        raise ValueError('unchanged complete-history recipe, domain and acceptance required')


def limits():
    n = recipe()['packets']; count = 6
    return dict(reference_setups=1, physical_proofs=1, training_proofs=2, lp_proposals=18,
        exact_supports=66, source_setups=count, source_steps=count*n, source_body_bounds=count*n,
        source_derivative_setups=count, source_derivative_steps=count*n, source_point_setups=count,
        source_point_steps=count*n, source_direct_steps=count*n, truth_audits=1)


def audit_truth(regions, witness, future, future_truth, targets):
    from lll.ilvis0_saved_prediction_audit import endpoint
    witness = list(map(F, witness)); slacks = []
    for region in regions:
        if len(witness) != len(region['lower']) or any(
            not F(a) <= v <= F(b) for a, v, b in zip(region['lower'], witness, region['upper'], strict=True)
        ):
            raise ValueError('known training witness outside declared box')
        for row, right in zip(region['inequality_design'], region['inequality_upper'], strict=True):
            slacks.append(sum((F(a)*v for a, v in zip(row, witness, strict=True)), F(0)) - F(right))
    if not slacks or max(slacks) > 0:
        raise ValueError('known training witness excluded by a retained constraint')
    if len(future_truth) != 3 or any(not F(a) <= F(v) <= F(b) for a, v, b in
        zip(future['lower'], future_truth, future['upper'], strict=True)):
        raise ValueError('known future truth excluded by prediction')
    widths = [endpoint(F(b)-F(a), True) for a, b in zip(future['lower'], future['upper'], strict=True)]
    if len(widths) != 3 or len(targets) != 3 or any(w < 0 for w in widths):
        raise ValueError('three ordered prediction ranges and fixed width targets required')
    return dict(known_truth_retained=True, future_truth_contained=True,
        maximum_exact_training_slack=str(max(slacks)), width_m=widths,
        useful=all(F(w) <= F(t) for w, t in zip(widths, targets, strict=True)))


class Runtime:
    def __init__(self, context, spec):
        from lll.ilvis0_coupled_map_controls import Allowance
        from lll.ilvis0_control_shards import _check_continue
        self.context=context; self.spec=spec; self.events=0; self.native_calls=0; self.bounds=0; self.saved={}
        if spec['limits'] != limits():
            raise ValueError('complete finite auxiliary allowance required')
        def persist(event):
            _check_continue(context.root, context.manifest); self.events += 1
            context.save(f'reservation-{self.events:03d}.json', event)
        self.budget=Allowance(limits(), persist)

    def reserve(self, **values):
        self.budget.reserve(values)

    def save(self, name, value):
        from lll.ilvis0_sharded_native import plain
        value=plain(value)
        if name == 'compilation.json':
            for kind, metadata in value.items():
                if metadata['compiler'] != self.spec['compiler']:
                    raise ValueError('compiler changed')
                expected=self.context.manifest['sources']
                if kind == 'native':
                    if metadata['source_sha256'] != expected['analysis/lll/ilvis0_tangent.cpp']:
                        raise ValueError('native source changed')
                else:
                    for source, digest in metadata['sources'].items():
                        if digest != expected['analysis/lll/'+source]:
                            raise ValueError('bound source changed')
        self.context.save(name, value); self.saved[name]=value

    def before_bound(self, n):
        if n != 96000 or self.bounds >= 6:
            raise ValueError('six complete-history bounds per identity required')
        self.reserve(source_setups=1, source_steps=n, source_body_bounds=n, source_derivative_setups=1,
            source_derivative_steps=n, source_point_setups=1, source_point_steps=n, source_direct_steps=n)
        self.context.charge(bound_calls=1, bound_steps=9*n); self.bounds += 1

    def native(self, kernel, config, theta, dv, dt, time_s, parameters):
        import ctypes
        import numpy as np
        n=len(dt)
        if n != 96000 or self.native_calls >= 12:
            raise ValueError('twelve complete-history native queries per identity required')
        self.context.charge(native_calls=1, packet_visits=n); self.native_calls += 1
        out=np.empty((1, 3)); jac=np.empty((3, 27)); flag=ctypes.c_int()
        code=kernel(n, theta, dv, dt, 1, np.array([time_s]), config['initial_c'], config['initial_v'],
            config['initial_r'], config['limits'], np.ascontiguousarray(parameters, float), config['model'],
            int(config['profile']), config['gravity'], config['radius'], out, jac, ctypes.byref(flag))
        record=dict(time_s=time_s, point=parameters, status=int(code), warning=flag.value)
        if not code:
            record.update(prediction=out[0], jacobian=jac)
        self.save(f'native-{self.native_calls:02d}.json', record)
        if code or flag.value:
            raise ValueError('native query failed or reported unsupported motion')
        return out[0], jac


def evaluate(task, context):
    import time
    import numpy as np
    from lll.ilvis0_sharded_native import read, plain
    from lll.ilvis0_shape import load_tangent
    from lll.ilvis0_batched_transport import configure_backend
    from lll.ilvis0_source_stream import load_stream
    from lll.ilvis0_source_derivative_intervals import load_kernel
    from lll.ilvis0_source_point_derivatives import load_kernel as load_point
    from lll.ilvis0_staged_native import predict
    from lll import ilvis0_direct_native as candidate
    spec=task['payload']; settings=read(context.input_path()); validate_recipe(settings)
    case=read(context.input_path(spec['case_key'])); config=case['configuration']; n=len(case['dt'])
    if (n != settings['packets'] or config['model'] != spec['model'] or config['profile'] != spec['profile']
            or config['limits'][25] != settings['clock_limit_s'] or case['center'] != settings['center']
            or settings['future_s']+settings['clock_limit_s'] > case['provenance']['sequential_endpoint_s']):
        raise ValueError('qualified complete input, declared clock support and candidate required')
    config={k:np.ascontiguousarray(v, float) if k in ('initial_c','initial_v','initial_r','limits') else v
            for k, v in config.items()}
    theta, dv, dt=(np.ascontiguousarray(case[k], float) for k in ('theta','dv','dt'))
    lo=np.array(settings['lower']); hi=np.array(settings['upper']); center=np.array(settings['center'])
    runtime=Runtime(context, spec); runtime.reserve(reference_setups=1)
    reference=candidate.make_reference(config, theta, dv, dt, lower=lo, upper=hi, center=center)
    runtime.save('reference.json', reference.report())
    directory=context.root/'shards'/f'{context.shard:03d}'/'kernels'
    directory.mkdir(parents=True, exist_ok=True); sources=context.root/'source-freeze/analysis/lll'
    arithmetic=configure_backend(directory, source_directory=sources)
    source, source_meta=load_stream(directory, source_directory=sources)
    derivative, derivative_meta=load_kernel(directory, source_directory=sources)
    point, point_meta=load_point(directory, source_directory=sources)
    kernel, native_meta=load_tangent(directory)
    runtime.save('compilation.json', dict(arithmetic=arithmetic, source=source_meta,
        derivative=derivative_meta, point=point_meta, native=native_meta))
    def native(time_s, parameters):
        return runtime.native(kernel, config, theta, dv, dt, time_s, parameters)
    scale=spec['coordinate_scale']; origin=config['initial_c']; truth=np.array(settings['truth'])
    times=settings['training_s']; observed=[]; errors=[]
    for ordinal, time_s in enumerate(times):
        value, _=native(time_s, truth)
        noise=np.array([.25*((ordinal+2*axis)%3-1) for axis in range(3)])
        measured=value+noise/np.array(scale); observed.append(measured)
        # Record the actual represented perturbation, not just the requested one.
        actual=[(F(float(a))-F(float(b)))*F(float(s)) for a,b,s in zip(measured,value,scale,strict=True)]
        if any(abs(v)>F(settings['noise_allowance_m']) for v in actual):
            raise ValueError('generated observation error exceeds its declared allowance')
        errors.append(list(map(str, actual)))
    runtime.save('training-observations.json', dict(times_s=times, observations=observed,
        actual_errors_m=errors, allowance_m=settings['noise_allowance_m'], future_observations_used=False))
    def bound(time_s, proof):
        runtime.before_bound(n); started=time.monotonic()
        result=candidate.enclose(config, theta, dv, dt, time=time_s, lower=lo, upper=hi, reference=reference,
            conditioning=proof, source_kernel=source, derivative_kernel=derivative, point_kernel=point,
            maximum_seconds=settings['maximum_bound_seconds'])
        raw=result.report()
        runtime.save(f'raw-bound-{runtime.bounds:02d}.json', dict(report=raw, elapsed_s=time.monotonic()-started))
        if any(result.metadata[k]>n for k in ('source_reference_steps','source_derivative_steps',
                                             'source_direct_steps','rounded_source_prefixes')):
            raise ValueError('source work exceeds its complete-history reservation')
        return result
    result=predict(training_times=times, observations=observed,
        noise_allowance=np.full((len(times),3), settings['noise_allowance_m']), stage_sizes=settings['stage_sizes'],
        future_time=settings['future_s'], reference=reference, lower=lo, upper=hi, coordinate_scale=scale,
        origin=origin, native=native, bound=bound, reserve=runtime.reserve, save=runtime.save)
    runtime.reserve(truth_audits=1)
    future_value, _=native(settings['future_s'], truth)  # Prediction is already saved.
    future_truth=[(F(float(v))-F(float(o)))*F(float(s)) for v,o,s in zip(future_value,origin,scale,strict=True)]
    witness=list(truth)+list(reference.normalized_values_at(truth))
    regions=[runtime.saved[f'stage-{i:02d}-region.json'] for i in (1,2)]
    audit=audit_truth(regions, witness, result['future'], future_truth, settings['width_target_m'])
    runtime.save('truth-audit.json', dict(audit, evaluated_after_prediction=True,
        future_truth_m=list(map(str,future_truth))))
    if (runtime.native_calls!=12 or runtime.bounds!=6 or runtime.budget.counts!=limits()
            or regions[-1]['times_s']!=times or len(regions[-1]['inequality_design'])!=30
            or regions[-1]['inequality_design'][:18]!=regions[0]['inequality_design']):
        raise ValueError('complete finite calls, retained training rows and directions required')
    runtime.save('accounting.json', runtime.budget.counts)
    return plain(dict(identity=task['identity'], passed=audit['useful'], numerical_checks_passed=True,
        useful=audit['useful'], model=spec['model'], profile=spec['profile'], packets=n,
        native_evaluations=12, bound_evaluations=6, work=runtime.budget.counts,
        physical_parameter_count=27, parameter_count=51, training_epochs=5, stages=2, inequalities=30,
        future_width_m=audit['width_m'], width_target_m=settings['width_target_m'],
        known_truth_retained=True, future_truth_contained=True, future_observations_used=False,
        original_reads=0, optimizer_starts=0, recording_length_usefulness_qualified=audit['useful'],
        observational_coverage_qualified=False, whole_program_roundoff_qualified=False,
        scientific_decision='abstain'))
