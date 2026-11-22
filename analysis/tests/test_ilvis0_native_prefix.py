# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest

from native_prefix_reference import original
from test_ilvis0_height_gravity_bounds import native as height_gravity_kernel  # noqa: F401


def case(model,profile):
    from test_ilvis0_native_box_bounds import configuration
    from lll.ilvis0_transform_native import make_reference
    from lll.ilvis0_directional_acceleration import DirectionalAcceleration
    config=configuration();config.update(model=model,profile=profile)
    config['limits'][25]=1/1024
    dt=np.resize([.004,.006,.005,.007],13);theta=np.tile([1e-5,-2e-5,3e-6],(13,1))
    dv=np.c_[1e-5*np.sin(np.arange(13)),2e-5*np.cos(np.arange(13)),-9.81*dt]
    center=np.full(27,.1);center[25]=.125;lo=np.full(27,-.2);hi=np.full(27,.5)
    lo[25]=-.3;hi[25]=.7
    ref=make_reference(config,theta,dv,dt,lower=lo,upper=hi,center=center)
    proof=DirectionalAcceleration(ref,lo,hi)
    tags=[0.]
    for t in dt:tags.append(tags[-1]+float(t))
    knot=tags[6]-config['limits'][25]*center[25]
    times=[knot,float(np.nextafter(knot,np.inf)),tags[10]-config['limits'][25]*center[25]]
    return config,theta,dv,dt,lo,hi,ref,proof,times


@pytest.fixture(scope='module')
def kernels(tmp_path_factory):
    from lll.ilvis0_source_prefix import load_kernels
    from lll.ilvis0_source_stream import load_stream
    from lll.ilvis0_source_derivative_intervals import load_kernel as interval
    from lll.ilvis0_source_point_derivatives import load_kernel as point
    directory=tmp_path_factory.mktemp('native-prefix')
    return load_kernels(directory)[0],dict(source_kernel=load_stream(directory)[0],
        derivative_kernel=interval(directory)[0],point_kernel=point(directory)[0])


@pytest.mark.parametrize('model,profile',[(m,p) for m in range(3) for p in (False,True)])
def test_cold_and_batched_complete_reports_match_sealed_original(model,profile,kernels):
    from lll import ilvis0_remainder_native as current
    from lll.ilvis0_native_prefix import enclose_many
    config,theta,dv,dt,lo,hi,ref,proof,times=case(model,profile)
    common=dict(lower=lo,upper=hi,reference=ref,conditioning=proof,maximum_seconds=120.)
    expected=[original()[0].enclose(config,theta,dv,dt,time=t,**common,**kernels[1]).report() for t in times]
    cold=[current.enclose(config,theta,dv,dt,time=t,**common,**kernels[1]).report() for t in times]
    calls=[]
    result=enclose_many(config,theta,dv,dt,times=times,prefix_kernels=kernels[0],
        maximum_packet_steps=3*len(dt),reserve=lambda **v:calls.append(v),**common)
    assert cold==expected and [r.report() for r in result['bounds']]==expected
    assert result['work']['prefix_packet_steps']>0 and result['work']['cursor_copies']==3
    assert result['work']['prefix_packet_steps']+result['work']['tail_packet_steps']<3*len(dt)
    assert result['work']['force_profile_packets']==3*len(dt)
    assert sum(v.get('packet_steps',0) for v in calls)==result['work']['prefix_packet_steps']+result['work']['tail_packet_steps']
    assert result['observational_coverage_qualified'] is False


@pytest.mark.parametrize('change',['unsorted','outside','allowance','proof'])
def test_batch_rejects_changed_scopes_and_missing_finite_allowances(change,kernels):
    from lll.ilvis0_native_prefix import enclose_many
    config,theta,dv,dt,lo,hi,ref,proof,times=case(0,False)
    maximum=39
    if change=='unsorted':times=times[::-1]
    elif change=='outside':times[-1]=1.
    elif change=='allowance':maximum=0
    else:proof=None
    with pytest.raises(ValueError):enclose_many(config,theta,dv,dt,times=times,lower=lo,upper=hi,
        reference=ref,conditioning=proof,prefix_kernels=kernels[0],maximum_packet_steps=maximum,
        maximum_seconds=120.,reserve=lambda **v:None)


def test_zero_clock_and_adjacent_exact_packet_boundaries_keep_original_reports(kernels):
    from lll.ilvis0_native_prefix import enclose_many
    from lll.ilvis0_transform_native import make_reference
    from lll.ilvis0_directional_acceleration import DirectionalAcceleration
    config,theta,dv,dt,lo,hi,ref,_,_=case(0,False)
    center=ref.parent.center.copy();center[25]=lo[25]=hi[25]=0.
    ref=make_reference(config,theta,dv,dt,lower=lo,upper=hi,center=center)
    proof=DirectionalAcceleration(ref,lo,hi)
    times=[0.,.01,float(np.nextafter(.01,np.inf)),.032]
    common=dict(lower=lo,upper=hi,reference=ref,conditioning=proof,maximum_seconds=120.)
    expected=[original()[0].enclose(config,theta,dv,dt,time=t,**common,**kernels[1]).report() for t in times]
    result=enclose_many(config,theta,dv,dt,times=times,prefix_kernels=kernels[0],
        maximum_packet_steps=4*len(dt),reserve=lambda **v:None,**common)
    assert [r.report() for r in result['bounds']]==expected


def test_report_observer_is_isolated_and_keeps_completed_prefix_on_failure(kernels,tmp_path):
    from lll.ilvis0_native_prefix import enclose_many
    from lll.studies.series import ReportStream,read_reports
    config,theta,dv,dt,lo,hi,ref,proof,times=case(0,False)
    common=dict(times=times,lower=lo,upper=hi,reference=ref,conditioning=proof,
        maximum_seconds=120.,prefix_kernels=kernels[0],maximum_packet_steps=3*len(dt),reserve=lambda **v:None)
    plain=enclose_many(config,theta,dv,dt,**common)
    def mutate(index,report):
        report['time_s']=-1.;report['lower'][0]=999.
    observed=enclose_many(config,theta,dv,dt,on_report=mutate,**common)
    assert [r.report() for r in observed['bounds']]==[r.report() for r in plain['bounds']]
    assert observed['work']==plain['work']
    path=tmp_path/'reports.jsonl'
    with ReportStream(path,binding='fixed',maximum_records=3,maximum_record_bytes=1048576) as stream:
        def stop(index,report):
            stream.append(index,report)
            if index==1:raise RuntimeError('caller interrupted')
        with pytest.raises(RuntimeError,match='caller interrupted'):
            enclose_many(config,theta,dv,dt,on_report=stop,**common)
    saved=read_reports(path,binding='fixed',maximum_records=3,maximum_record_bytes=1048576)
    from lll.studies.artifacts import reports_equal
    assert reports_equal(saved,[r.report() for r in plain['bounds'][:2]])


@pytest.mark.parametrize('model,profile',[(0,True),(1,False),(2,False)])
def test_shared_prefix_bounds_use_native_midpoint_gravity(model,profile,kernels,height_gravity_kernel):
    import ctypes
    from lll.ilvis0_native_prefix import enclose_many
    from lll.ilvis0_remainder_native import enclose

    config,theta,dv,dt,lo,hi,ref,proof,times=case(model,profile)
    anchor=1482.531
    center=ref.parent.center
    common=dict(lower=lo,upper=hi,reference=ref,conditioning=proof,maximum_seconds=30.)
    options=dict(times=times,prefix_kernels=kernels[0],
        maximum_packet_steps=3*len(dt),reserve=lambda **v:None,**common)
    result=enclose_many(config,theta,dv,dt,gravity_anchor_height_m=anchor,reuse_force_profiles=True,**options)
    constant=enclose_many(config,theta,dv,dt,**options)
    assert result['binding']!=constant['binding']
    assert result['work']==dict(constant['work'],force_profile_packets=len(dt))
    assert result['work']['prefix_packet_steps']>0
    assert result['observational_coverage_qualified'] is False
    assert abs(result['bounds'][-1].center[2]-constant['bounds'][-1].center[2])>1e-5

    def native(point):
        out=np.empty((len(times),3));jac=np.empty((3*len(times),27))
        assert height_gravity_kernel(len(dt),theta,dv,dt,len(times),np.array(times),
            config['initial_c'],config['initial_v'],config['initial_r'],config['limits'],
            point,model,int(profile),config['gravity'],config['radius'],out,jac,
            ctypes.byref(ctypes.c_int()))==0
        return out,jac.reshape(len(times),3,27)

    coordinates,jacobians=native(center)
    probes=[(point,native(point)[0]) for point in (lo,hi,lo+.63*(hi-lo))]
    scale=np.array([6371000.,6371000.,1.])
    for i,bound in enumerate(result['bounds']):
        cold=enclose(config,theta,dv,dt,time=times[i],gravity_anchor_height_m=anchor,**common,**kernels[1])
        assert bound.report()==cold.report()
        assert bound.report()['gravity_anchor_height_m']==anchor
        assert np.max(np.abs(bound.center-coordinates[i])*scale)<1e-6
        with pytest.raises(ValueError,match='gravity anchor'):
            bound.design(jacobians[i],ref)
        design=bound.design(jacobians[i],ref,gravity_anchor_height_m=anchor)
        assert np.array_equal(design[:,:27],jacobians[i])
        assert design.shape==(3,51)
        for point,forecast in probes:
            delta=np.r_[point-center,ref.normalized_values_at(point)]
            remainder=np.abs(forecast[i]-coordinates[i]-design@delta)
            assert np.all(remainder*scale<=bound.unshared_remainder*scale+1e-6)

    with pytest.raises(ValueError,match='gravity anchor'):
        enclose_many(config,theta,dv,dt,gravity_anchor_height_m=-6371000.,**options)


def test_optional_extensions_preserve_the_qualified_prefix_orchestration():
    import ast
    from pathlib import Path
    from lll.studies.closed import ClosedStudy
    root=Path(__file__).resolve().parents[2]
    study=ClosedStudy(root,'docs/ilvis0-native-prefix-format-recovery')
    try:
        original_source=study.read('source-freeze/analysis/lll/ilvis0_native_prefix.py',
            study.manifest['sources']['analysis/lll/ilvis0_native_prefix.py'],raw=True)
    finally:study.close()
    tree=ast.parse((root/'analysis/lll/ilvis0_native_prefix.py').read_bytes())
    function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='enclose_many')
    assert function.args.kwonlyargs.pop().arg=='reuse_force_profiles'
    assert function.args.kw_defaults.pop().value is False
    for name in ('gravity_anchor_height_m','on_report'):
        assert function.args.kwonlyargs.pop().arg==name
        default=function.args.kw_defaults.pop()
        assert isinstance(default,ast.Constant) and default.value is None
    # Height-dependent arithmetic lives inside these functions. The generated
    # comparisons above test both their constant and height-dependent outputs.
    dynamics={'_prepare','_advance','_finish','_cold_enclose','_force_clock','_force_profile'}
    historical=ast.parse(original_source)
    for module in (tree,historical):
        module.body=[n for n in module.body
                     if not isinstance(n,ast.FunctionDef) or n.name not in dynamics]
    removed=[]
    class RemoveObserver(ast.NodeTransformer):
        def visit_Call(self,node):
            if isinstance(node.func,ast.Name) and node.func.id=='_prepare':
                anchor=node.keywords.pop()
                assert ast.unparse(anchor)=='gravity_anchor_height_m=gravity_anchor_height_m'
            return self.generic_visit(node)

        def visit_If(self,node):
            if ast.unparse(node.test)=='reuse_force_profiles':
                assert not node.orelse
                assert ast.unparse(node.body[-1])=='c.force_profiles = dict(zip(times, profiles, strict=True))'
                return None
            if ast.unparse(node.test)=='on_report is not None':
                assert len(node.body)==1 and not node.orelse
                assert ast.unparse(node.body[0])=='on_report(len(bounds) - 1, deepcopy(bounds[-1].report()))'
                removed.append(node);return None
            if ast.unparse(node.test)=='on_report is not None and (not callable(on_report))':
                assert len(node.body)==1 and isinstance(node.body[0],ast.Raise) and not node.orelse
                removed.append(node);return None
            return self.generic_visit(node)
    tree=RemoveObserver().visit(tree)
    assert len(removed)==2
    assert ast.dump(tree,include_attributes=False)==ast.dump(historical,include_attributes=False)
