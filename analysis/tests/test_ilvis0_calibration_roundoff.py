# SPDX-License-Identifier: AGPL-3.0-or-later
from fractions import Fraction as F
import importlib,importlib.util
import itertools
import pytest


def implementation():
    name='lll.ilvis0_calibration_roundoff'
    assert importlib.util.find_spec(name) is not None,'exact calibration enclosure is not implemented'
    return importlib.import_module(name)


@pytest.mark.parametrize('as_rate',[False,True])
def test_exact_corners_and_affine_errors_include_supplied_center_and_row_rounding(as_rate):
    module=implementation();dt=.005;raw=[.001,-.002,-.04905]
    bias=[F(3,10000),F(-2,10000),F(1,10000)];gain=[F(1,1000),F(-2,1000),F(1,2000)]
    bl=[v-F(1,10000) for v in bias];bu=[v+F(1,10000) for v in bias]
    gl=[v-F(1,10000) for v in gain];gu=[v+F(1,10000) for v in gain]
    factor=F(dt) if as_rate else F(1)
    center=[float((F(r)-b*F(dt))/(1+g)/factor) for r,b,g in zip(raw,bias,gain,strict=True)]
    # Explicit supplied rows need not be exact: discrepancy must enter R.
    jb=[float(-F(dt)/(1+g)/factor)+1e-8 for g in gain]
    jg=[float(-(F(r)-b*F(dt))/(1+g)**2/factor)-1e-8 for r,b,g in zip(raw,bias,gain,strict=True)]
    result=module.enclose(raw,dt,bias_center=bias,gain_center=gain,bias_lower=bl,bias_upper=bu,
        gain_lower=gl,gain_upper=gu,center=center,bias_row=jb,gain_row=jg,as_rate=as_rate)
    assert result['center']==center
    for axis in range(3):
        for sb,sg in itertools.product((-1,0,1),repeat=2):
            b=bias[axis]+F(sb,10000);g=gain[axis]+F(sg,10000)
            actual=(F(raw[axis])-b*F(dt))/(1+g)/factor
            linear=F(jb[axis])*(b-bias[axis])+F(jg[axis])*(g-gain[axis])
            assert F(result['lower'][axis])<=actual<=F(result['upper'][axis])
            assert abs(actual-F(center[axis]))<=F(result['component_change'][axis])
            assert abs(actual-F(center[axis])-linear)<=F(result['component_remainder'][axis])


def test_point_domain_reports_nonzero_arithmetic_error():
    module=implementation();raw=[.1,.2,.3];dt=.005;bias=[.01,.02,.03];gain=[.1,-.2,.3]
    center=[(r-b*dt)/(1+g) for r,b,g in zip(raw,bias,gain,strict=True)]
    result=module.enclose(raw,dt,bias_center=bias,gain_center=gain,bias_lower=bias,bias_upper=bias,
        gain_lower=gain,gain_upper=gain,center=center)
    exact=[(F(r)-F(b)*F(dt))/(1+F(g)) for r,b,g in zip(raw,bias,gain,strict=True)]
    errors=[abs(value-F(c)) for value,c in zip(exact,center,strict=True)]
    assert any(errors)
    assert all(F(v)>=e for v,e in zip(result['component_change'],errors,strict=True))
    assert all(F(v)>=e for v,e in zip(result['component_remainder'],errors,strict=True))
    assert not result['whole_source_rounding_qualified']


def test_bad_calibration_domain_is_rejected():
    module=implementation();zero=[0.]*3
    kwargs=dict(bias_center=zero,gain_center=zero,bias_lower=zero,bias_upper=zero,
        gain_lower=zero,gain_upper=zero,center=zero)
    for changes in (dict(gain_lower=[-1.,0.,0.]),dict(bias_lower=[1.,0.,0.]),dict(center=[float('nan'),0.,0.])):
        with pytest.raises(ValueError):module.enclose(zero,.005,**dict(kwargs,**changes))


def test_nonbinary_supplied_rows_are_bounded_about_the_reported_float_rows():
    module=implementation();zero=[0.]*3;row=[-F(1,3)]*3
    result=module.enclose(zero,F(1,3),bias_center=zero,gain_center=zero,
        bias_lower=[-1.]*3,bias_upper=[1.]*3,gain_lower=zero,gain_upper=zero,
        center=zero,bias_row=row,gain_row=zero)
    for axis in range(3):
        assert abs(-F(1,3)-F(result['bias_row'][axis]))<=F(result['component_remainder'][axis])
