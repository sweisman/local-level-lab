# SPDX-License-Identifier: AGPL-3.0-or-later
"""Apply all frozen candidate controls privately to the scaled affine solver."""
from pathlib import Path

_reference=Path(__file__).with_name('test_ilvis0_representable_boundary.py')
_source=_reference.read_text()
_old='from lll import ilvis0_representable_boundary\n    return ilvis0_representable_boundary'
_new='from lll import ilvis0_scaled_branch\n    return ilvis0_scaled_branch'
assert _source.count(_old)==1
exec(compile(_source.replace(_old,_new),str(_reference),'exec'),globals())


def test_scaled_affine_recovers_known_optimum_with_tiny_timing_box():
    from lll.ilvis0_scaled_branch import scaled_lsq
    a=np.eye(3);b=np.array([0.,.5,-3.])
    result=scaled_lsq(a,b,bounds=(np.array([0.,-1.,-1.]),np.array([1e-12,1.,1.])),method='bvls',tol=1e-10,max_iter=100)
    assert result.success and result.x==pytest.approx([0.,.5,-1.],abs=1e-9)
    assert np.linalg.norm(a@result.x-b)**2==pytest.approx(4.)
    assert result.affine_reference_passed and result.affine_stationarity<=1e-8


@pytest.mark.parametrize('bad',['nonfinite','shape','bounds','method','budget'])
def test_scaled_affine_rejects_invalid_problem(bad):
    from lll.ilvis0_scaled_branch import scaled_lsq
    a=np.eye(2);b=np.ones(2);lower=np.array([-1.,0.]);upper=np.ones(2);method='bvls';budget=100
    if bad=='nonfinite':a[0,0]=np.nan
    if bad=='shape':b=np.ones(3)
    if bad=='bounds':upper[0]=lower[0]
    if bad=='method':method='other'
    if bad=='budget':budget=101
    with pytest.raises(ValueError):scaled_lsq(a,b,bounds=(lower,upper),method=method,tol=1e-10,max_iter=budget)


@pytest.mark.parametrize('role',['primary','repeat'])
def test_scaled_affine_saved_problem_beats_feasible_reference(role):
    import gzip
    import json
    from lll.ilvis0_scaled_branch import scaled_lsq
    root=Path(__file__).resolve().parents[2]
    study=root/'docs/ilvis0-final-pair-boundary-v2-20261018'
    rows=json.loads((study/'summary.json').read_text())['results']
    row=next(r for r in rows if r['source_role']=='bias1_profiled_removal/'+role)
    with gzip.open(study/row['linearization_file'],'rt') as stream:saved=json.load(stream)
    point=np.array(saved['normalized_parameters']);a=np.array(saved['jacobian']);b=-np.array(saved['residual'])
    index=saved['active_parameters'].index('time_offset');lower=-1-point;upper=1-point
    lower[index]=0.;upper[index]=row['boundary_check']['neighbor_edges'][1]-point[index]
    result=scaled_lsq(a,b,bounds=(lower,upper),method='bvls',tol=1e-10,max_iter=100)
    assert result.success and np.all(result.x>=lower) and np.all(result.x<=upper)
    assert np.linalg.norm(a@result.x-b)**2<=np.linalg.norm(b)**2+1e-12
    assert result.affine_reference_passed and result.affine_stationarity<=1e-8
    assert np.max(abs(result.x))<.01


def test_scaled_affine_preserves_rank_deficient_directions_and_bound_optimum():
    from lll.ilvis0_scaled_branch import scaled_lsq
    a=np.array([[1.,1.,0.],[0.,0.,1.],[0.,0.,0.]]);b=np.array([-1.,2.,0.])
    result=scaled_lsq(a,b,bounds=(np.array([0.,-1.,-1.]),np.array([1e-12,1.,1.])),method='bvls',tol=1e-10,max_iter=100)
    assert result.success and result.x[2]==pytest.approx(1.)
    assert np.linalg.norm(a@result.x-b)**2==pytest.approx(1.)
