from types import SimpleNamespace
import pytest

from lll.prediction_phase_review import identities, read_selected


def test_selection_excludes_other_models_laws_and_unexecuted_records():
    tasks = {}
    for seed in (9, 10, 11):
        for law in ('point', 'increment'):
            for model in ('sphere_rotating', 'sphere_still', 'flat_still'):
                for profile in (0, 1):
                    for start in (0, 1):
                        name = f'{seed}-{law}-{model}-{profile}-{start}'
                        tasks[name] = {'payload': dict(draw_seed=seed, case=dict(law=law, model=model, profile=profile, start=start))}
    study = SimpleNamespace(tasks=tasks, rows={k: {} for k in tasks})
    selected = identities(study, 10)
    assert len(selected) == 9
    assert all(k.startswith(('9-increment-', '10-increment-')) for k in selected)
    study.rows.pop(selected[0])
    assert identities(study, 10) == selected[1:]


@pytest.mark.parametrize('selected', [[], ['a', 'a'], list(map(str, range(25)))])
def test_invalid_selection_rejected_before_reading(selected):
    with pytest.raises(ValueError):
        read_selected(None, selected)


def test_preserves_failed_fit_and_interrupted_outcome_without_evaluation():
    failed = dict(converged=False, residual_sum_squares=2.0)
    study = SimpleNamespace(tasks={'a': {'payload': {}}, 'b': {'payload': {}}},
        completion={'manifest_sha256': 'm', 'summary_sha256': 's'},
        envelope=lambda k: {'artifacts': {'artifacts/a/fit.json': 'h'} if k == 'a' else {},
                            'result': {'error_type': 'BudgetStopped'} if k == 'b' else {'converged': False}},
        artifact=lambda k, n: failed)
    report = read_selected(study, ['a', 'b'])
    assert report['records'][0]['fit'] == failed
    assert report['records'][1]['fit'] is None
    assert report['native_calls'] == report['optimizer_starts'] == report['new_noise_draws'] == 0


def test_wall_allowance_cannot_expand():
    with pytest.raises(ValueError):
        read_selected(None, ['a'], maximum_wall_s=601)


def _clock_hash(values):
    import hashlib
    import struct
    return hashlib.sha256(struct.pack('<'+str(len(values))+'d',*values)).hexdigest()


@pytest.mark.parametrize('offset',[-.251,-.25,-.249])
def test_clock_geometry_reports_signed_distance_to_verified_packet_grid(offset):
    from lll.prediction_phase_review import clock_geometry
    times=[.5,1.,1.5];dt=[.25]*8
    result=clock_geometry(dict(parameters=dict(time_offset=offset)),times,dt,
        expected_dt_sha256=_clock_hash(dt),expected_times_sha256=_clock_hash(times))
    expected=offset+.25
    assert result['query_count']==3 and result['packet_count']==8
    assert result['signed_distance_s']==pytest.approx([expected]*3,abs=1e-15)
    assert result['minimum_absolute_distance_s']==pytest.approx(abs(expected),abs=1e-15)
    assert result['numerical_starts']==result['native_calls']==result['new_noise_draws']==0


@pytest.mark.parametrize('change',['dt_hash','times_hash','zero_dt','reversed_queries','nan','bool','outside',
                                 'empty_times','empty_dt','missing_fit','above_support'])
def test_clock_geometry_rejects_unverified_or_invalid_clock_metadata(change):
    from lll.prediction_phase_review import clock_geometry
    times=[.5,1.,1.5];dt=[.25]*8;offset=-.25
    dh=_clock_hash(dt);th=_clock_hash(times)
    if change=='dt_hash':dh='0'*64
    elif change=='times_hash':th='0'*64
    elif change=='zero_dt':dt[0]=0.
    elif change=='reversed_queries':times=times[::-1]
    elif change=='nan':offset=float('nan')
    elif change=='bool':times[0]=True
    elif change=='outside':offset=-1.
    elif change=='empty_times':times=[]
    elif change=='empty_dt':dt=[]
    elif change=='above_support':offset=2.
    fit={} if change=='missing_fit' else dict(parameters=dict(time_offset=offset))
    with pytest.raises(ValueError):
        clock_geometry(fit,times,dt,
            expected_dt_sha256=dh,expected_times_sha256=th)


def test_saved_clock_review_uses_only_declared_records_and_retains_failed_label(monkeypatch):
    from lll import prediction_phase_review as review
    times=[.5,1.,1.5];dt=[(i+1)/300-i/300 for i in range(600)]
    fit=dict(parameters=dict(time_offset=-1/300),converged=False,evaluations=41,
             stability_probe=dict(passed=False))
    class Saved:
        def __init__(self,*a):
            self.tasks={'failed':dict(payload={})};self.completion=dict(manifest_sha256='a'*64,summary_sha256='b'*64)
        def envelope(self,name):
            assert name=='failed'
            return dict(artifacts={'artifacts/failed/fit.json':'c'*64},result=dict(converged=False))
        def artifact(self,name,field):
            assert name=='failed'
            return {'fit.json':fit,'input-binding.json':dict(native_packets=600,
                full_array_sha256=dict(dt=_clock_hash(dt),times=_clock_hash(times))),
                'forecast.json':dict(times_s=times)}[field]
        def input(self,key):
            assert key=='population'
            return dict(descriptor=dict(recipe=dict(rate_hz=300)))
        def close(self):pass
    monkeypatch.setattr(review,'ClosedStudy',Saved)
    result=review.review_clock('.','docs/closed',['failed'])
    row=result['rows'][0]
    assert row['converged'] is False and row['fit_sha256']=='c'*64
    assert row['geometry']['maximum_absolute_distance_s']<1e-15
    assert result['native_calls']==result['optimizer_starts']==result['new_noise_draws']==0


def test_linear_probe_replays_known_bounded_optimum_and_charges_before_solving():
    from lll.prediction_phase_review import replay_linear_probe
    fit=dict(local_linearization=dict(normalized_parameters=[.5,0.],
        active_parameters=['time_offset','nuisance'],residual=[2.,-3.,4.],
        jacobian=[[2.,0.],[0.,1.],[0.,0.]]),converged=False)
    charged=[]
    result=replay_linear_probe(fit,reserve=lambda:charged.append('solve'))
    assert charged==['solve']
    assert result['correction']==pytest.approx([-1.,1.])
    assert result['original_cost']==29. and result['predicted_cost']==20.
    assert result['converged'] is False and result['nonlinear_fit_starts']==0


def test_linear_probe_cannot_execute_when_reservation_fails(monkeypatch):
    from lll.prediction_phase_review import replay_linear_probe
    import scipy.optimize
    fit=dict(local_linearization=dict(normalized_parameters=[0.],active_parameters=['time_offset'],
        residual=[1.],jacobian=[[1.]]),converged=False)
    def exhausted():raise RuntimeError('all four solves charged')
    def forbidden(*a,**k):raise AssertionError('solver ran before reservation')
    monkeypatch.setattr(scipy.optimize,'lsq_linear',forbidden)
    with pytest.raises(RuntimeError,match='all four'):
        replay_linear_probe(fit,reserve=exhausted)


def test_linear_probe_preserves_unidentified_columns_in_known_bounded_solution():
    from lll.prediction_phase_review import replay_linear_probe
    fit=dict(local_linearization=dict(normalized_parameters=[0.,0.,0.],
        active_parameters=['time_offset','same_effect','unidentified'],residual=[3.,4.],
        jacobian=[[1.,1.,0.],[0.,0.,0.]]),converged=True)
    result=replay_linear_probe(fit,reserve=lambda:None)
    assert result['linear_success'] and len(result['correction'])==3
    assert result['predicted_cost']==pytest.approx(17.)
    assert result['converged'] is True and result['labels_changed'] is False


def test_linear_timing_review_checks_saved_probe_before_interpreting_crossings():
    from lll.prediction_phase_review import linear_timing_geometry
    dt=[.25]*8;times=[.5,1.,1.5]
    fit=dict(parameters=dict(time_offset=-.249),converged=False,
        local_linearization=dict(normalized_parameters=[0.],active_parameters=['time_offset'],
            residual=[.002],jacobian=[[1.]]),
        stability_probe=dict(normalized_parameter_step=.002,predicted_cost_change=.002**2))
    args=dict(times_s=times,dt_s=dt,time_offset_scale=1.,expected_dt_sha256=_clock_hash(dt),
              expected_times_sha256=_clock_hash(times),reserve=lambda:None)
    result=linear_timing_geometry(fit,**args)
    assert result['replay_matches_saved'] and result['queries_crossing_boundaries']==3
    assert result['time_offset_step_s']==pytest.approx(-.002)
    fit['stability_probe']['normalized_parameter_step']=.5
    mismatch=linear_timing_geometry(fit,**args)
    assert mismatch['replay_matches_saved'] is False
    assert 'queries_crossing_boundaries' not in mismatch


def test_publication_passes_frozen_relative_string_to_packager(tmp_path, monkeypatch):
    from lll.prediction_phase_review import publish_phase
    from lll import prediction_calibration_report, prediction_calibration_study
    from lll import airquantumgrav_inventory, ilvis0_control_publication
    from lll.studies import qualification
    monkeypatch.setattr(qualification, 'checked', lambda *a, **k: (b'request', b'tests'))
    monkeypatch.setattr(prediction_calibration_study, 'qualification_sources', lambda r: {})
    monkeypatch.setattr(airquantumgrav_inventory, 'environment', lambda: {})
    monkeypatch.setattr(prediction_calibration_report, 'inspect', lambda *a: dict(role='calibration', calibration=None))
    monkeypatch.setattr(prediction_calibration_report, 'render', lambda r: 'Stopped calibration')
    class CheckedPlan(Exception):
        pass
    def package(data, public, text, *, plan):
        assert type(plan) is str
        assert plan == 'docs/prediction-score-qualification/EXECUTION_PLAN.md'
        raise CheckedPlan
    monkeypatch.setattr(ilvis0_control_publication, 'publish', package)
    with pytest.raises(CheckedPlan):
        publish_phase(tmp_path, 'data/closed', qualification='request.json')
