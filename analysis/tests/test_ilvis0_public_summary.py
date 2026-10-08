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
