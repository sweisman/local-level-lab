# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
from pathlib import Path
import pytest


def reporter():
    p=Path(__file__).resolve().parents[2]/'docs/ilvis0-highspeed-segments-20261008/summarize_results.py'
    spec=importlib.util.spec_from_file_location('public_summary',p)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def fit(model,converged=True,**kwargs):
    return dict(model=model,converged=converged,exact_projected_gradient_relative=1e-6,
        evaluations=20,residual_rms_neu_m=[1.,2.,3.],active_bounds=[],**kwargs)


def test_categories_preserve_unfinished_and_failed_fits():
    r=reporter()
    assert r.fit_status(fit('sphere_still'))=='converged'
    assert r.fit_status(fit('sphere_still',False))=='unresolved'
    f=fit('sphere_still');f['exact_projected_gradient_relative']=.01
    assert r.fit_status(f)=='unresolved'
    assert r.fit_status(dict(model='flat_still',error='invalid timing'))=='failed'


def test_all_required_fits_define_stretch_categories_and_processing_counts():
    r=reporter();models=['sphere_rotating','sphere_still','flat_still']
    def result(sid,good):
        return dict(segment_id=sid,filename=sid+'.013',state='fitted',
            cases=[dict(case_id=c,fits=[fit(m,good or m!='flat_still') for m in models])
                for c in ['bias1_unsubtracted','bias1_profiled_removal']],
            profile=dict(conditional_shape_preference='globe' if good else 'unresolved',
                rotation_diagnostics=[] if good else None))
    selection=dict(selected=[dict(segment=dict(segment_id=s,duration_s=d,
        median_receiver_ground_speed_kmh=v,imu_type=t))
        for s,d,v,t in [('a',240.,700.,6),('b',600.,800.,8)]])
    summary=dict(results=[result('a',True),result('b',False)])
    out=r.tabulate(summary,selection)
    assert out['fit_counts']==dict(converged=10,unresolved=2,failed=0)
    assert out['group_stats']['fully converged']['median_duration_min']==4.
    assert out['group_stats']['unresolved']['median_duration_min']==10.
    assert out['by_case_model']['bias1_unsubtracted']['flat_still']['unresolved']==1
    text=r.render(out,dict(starts=12,maximum_starts=16))
    assert '10' in text and 'Unknown' in text and 'not independent flights' in text


def test_public_summary_rejects_missing_or_duplicate_stretch_results():
    r=reporter();s=dict(selected=[dict(segment=dict(segment_id='a'))])
    with pytest.raises(ValueError,match='identity'):r.tabulate(dict(results=[]),s)


def test_unpublished_run_cannot_generate_a_final_summary(tmp_path):
    with pytest.raises(ValueError,match='audited publication'):
        reporter().load_evidence(tmp_path)


def test_partial_shape_leans_use_only_converged_matched_pairs():
    r=reporter()
    a=fit('sphere_rotating',False,residual_sum_squares=0.)
    b=fit('sphere_still',residual_sum_squares=10.)
    c=fit('flat_still',residual_sum_squares=30.)
    out=r.partial_shape([a,b,c])
    assert out['sphere_still_disc_minus_globe_cost']==20.
    assert out['sphere_rotating_disc_minus_globe_cost'] is None
    assert out['available_lean']=='Still globe fits better than flat'
    b['residual_sum_squares']=40.
    assert r.partial_shape([a,b,c])['available_lean']=='Flat fits better than still globe'
    c['converged']=False
    assert r.partial_shape([a,b,c])['available_lean']=='No converged shape pair'


def test_track_context_preserves_source_identity_time_speed_and_record_type():
    r=reporter();chosen=dict(filename='sample.013',task='t',segment=dict(imu_type=8,
        time_types=2,start_s=172810.,end_s=173050.,duration_s=240.,
        minimum_receiver_ground_speed_kmh=700.,median_receiver_ground_speed_kmh=710.,
        receiver_fixes=[dict(time_s=172810.,latitude_rad=0.,longitude_rad=0.,height_m=10.),
                        dict(time_s=173050.,latitude_rad=0.,longitude_rad=0.017453292519943295,height_m=10.)]))
    record=dict(source_sha256='a'*64,source_bytes=1234,timing=dict(dates=['2009-04-14']))
    out=r.track_context(chosen,record)
    assert out['source_sha256']=='a'*64 and out['filename']=='sample.013'
    assert out['start_utc']=='2009-04-14T00:00:10Z' and out['end_utc']=='2009-04-14T00:04:10Z'
    assert out['record_type']=='Applanix Group 4' and out['imu_type']==8
    assert out['minimum_speed_kmh']==700. and out['median_speed_kmh']==710.
    assert out['duration_min']==4.
    assert out['gps_track_km']==pytest.approx(111.19492664455873)
