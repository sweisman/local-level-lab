# SPDX-License-Identifier: AGPL-3.0-or-later
"""Capture fixed native arithmetic; assertion outcomes remain diagnostic data."""
import pytest
from test_native_structured_training import training_kernels,native_training_case

DEFINITION=dict(additional_sources=['analysis/tests/test_native_bounded_numerics.py',
    'analysis/tests/test_native_bounded_controls.py','analysis/lll/ilvis0_bounded_error_forecast.py',
    'analysis/lll/bounded_state_prediction.py','docs/integrated-noise-covariance/BOUNDED_NUMERICS_PLAN.md',
    'data/ilvis0-source-point-development/native-bounded-controls-20261025-request.json',
    'data/ilvis0-source-point-development/native-bounded-controls-20261025.xml'],
    allowances={'builds':dict(builds=2),
        'point:2:1:0':dict(native_calls=450,packet_steps=15000,packet_query_visits=300000),
        'point:2:0:1':dict(native_calls=450,packet_steps=15000,packet_query_visits=300000)},maximum_wall_s=180.)


@pytest.mark.parametrize('training_kernels',[DEFINITION],indirect=True)
@pytest.mark.parametrize('law',['point'])
@pytest.mark.parametrize('model',[2])
@pytest.mark.parametrize('profile,height',[(True,False),(False,True)])
def test_capture_bounded_native_numerical_state(native_training_case,monkeypatch,law,model,profile,height):
    import io,json
    from pathlib import Path
    import numpy as np
    from lll.studies.artifacts import digest,encoded,atomic
    from lll.studies.closed import load_python_reference
    from lll import ilvis0_bounded_prediction as bounded
    from lll.ilvis0_native_error_training import ErrorTrainingFactory
    from lll.ilvis0_bounded_error_forecast import BoundedForecastErrorDiagnostic
    k=native_training_case;root=Path.cwd();arrays={};regions=[];capture={}
    old=root/'data/ilvis0-source-point-development/native-bounded-controls-20261025-request.json'
    parent=json.loads(old.read_bytes());name='analysis/tests/test_native_bounded_controls.py'
    raw=(root/name).read_bytes();assert digest(raw)==parent['sources'][name]
    frozen=load_python_reference(raw,name='lll._bounded_native_parent_'+digest(raw),sha256=digest(raw))
    original_region=bounded.Region
    class CapturedRegion(original_region):
        def __init__(self,values,design,bounds,**kwargs):
            self.capture_index=len(regions);regions.append(self)
            for key,value in (('values',values),('design',design),('bounds',bounds)):
                arrays[f'region_{self.capture_index}_{key}']=np.array(value,copy=True)
            super().__init__(values,design,bounds,**kwargs)
            for key in ('basis','singular','center'):
                if hasattr(self,key):arrays[f'region_{self.capture_index}_{key}']=getattr(self,key).copy()
        def support(self,directions):
            result=super().support(directions);prefix=f'region_{self.capture_index}_'
            arrays[prefix+'contrasts']=np.array(directions,copy=True)
            for key in ('lower','upper'):
                if key in result:arrays[prefix+'support_'+key]=result[key].copy()
            return result
    original_extend=ErrorTrainingFactory.extend
    def extend(factory,*args,**kwargs):
        result=original_extend(factory,*args,**kwargs);op=result[0]
        arrays['innovation_factor']=op.unwhiten(np.eye(3*op.epoch_count))
        capture['operator_configuration']=op.configuration
        return result
    original_call=BoundedForecastErrorDiagnostic.__call__
    def diagnostic(provider,problem,point,forecast,**kwargs):
        result=original_call(provider,problem,point,forecast,**kwargs)
        arrays['forecast_jacobian']=forecast['jacobian'].copy()
        arrays['forecast_coordinates']=forecast['coordinates'].copy()
        arrays['earlier_residual']=-forecast['training_coordinate_difference'].ravel().copy()
        for key in ('lower','upper','conditional_noise_half_width','deterministic_remainder_half_width'):
            arrays['structured_'+key]=result['bounded_calibration'][key].copy()
        capture['training_epochs']=len(problem.gps);capture['normalized_point']=point.tolist()
        return result
    monkeypatch.setattr(bounded,'Region',CapturedRegion)
    monkeypatch.setattr(ErrorTrainingFactory,'extend',extend)
    monkeypatch.setattr(BoundedForecastErrorDiagnostic,'__call__',diagnostic)
    error=None
    try:
        frozen.test_bounded_native_connection_matches_dense_linear_envelope(k,law,model,profile,height)
    except AssertionError as exc:error=str(exc)
    assert len(regions)>=2 and {'forecast_jacobian','earlier_residual','innovation_factor'}<=arrays.keys()
    assert sum(v.nbytes for v in arrays.values())<=1024**2
    identity=f'{law}-{model}-{int(profile)}-{int(height)}'
    buffer=io.BytesIO();np.savez_compressed(buffer,**arrays);path=k['path'].with_name(k['path'].stem+'.'+identity+'.npz')
    atomic(path,buffer.getvalue())
    report=dict(law=law,model=model,profile=profile,height=height,**capture,
        original_test_source_sha256=digest(raw),original_assertion_failed=error is not None,
        original_assertion_message=error,qualification_promoted=False,arrays_file=path.name,
        arrays_sha256=digest(buffer.getvalue()),array_bytes=sum(v.nbytes for v in arrays.values()),
        region_count=len(regions),nonlinear_coverage_established=False)
    atomic(path.with_suffix('.json'),encoded(report));k['results'].append(report)
