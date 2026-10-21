# SPDX-License-Identifier: AGPL-3.0-or-later
from fractions import Fraction as F
import pytest


@pytest.mark.parametrize('as_rate',(False,True))
def test_calibration_remainder_contains_exact_bias_gain_law(as_rate):
    from lll.ilvis0_source_remainder import calibration
    raw=F(-3,65536);dt=F(1,256);b0=F(1,16);g0=F(1,8)
    lo,hi=F(-1,8),F(1,4);gl,gh=F(-1,16),F(3,16)
    result=calibration(raw,dt,bias_center=b0,gain_center=g0,
        bias_lower=lo,bias_upper=hi,gain_lower=gl,gain_upper=gh,as_rate=as_rate)
    unit=dt if as_rate else F(1)
    expected=(raw-b0*dt)/(1+g0)/unit
    assert F(result['center'])==expected
    for i in range(7):
        b=lo+(hi-lo)*F(i,6)
        for j in range(7):
            g=gl+(gh-gl)*F(j,6);actual=(raw-b*dt)/(1+g)/unit
            linear=-dt/(1+g0)/unit*(b-b0)-expected/(1+g0)*(g-g0)
            assert F(result['lower'])<=actual<=F(result['upper'])
            assert abs(actual-expected-linear)<=F(result['remainder'])


@pytest.mark.parametrize('q0,start,row',[(F(0),F(0),F(4)),(F(1,4),F(0),F(4)),
    (F(1,4),F(1,4),F(0)),(F(1,8),F(0),F(4))])
def test_clipped_clock_remainder_preserves_both_boundary_sides(q0,start,row):
    from lll.ilvis0_source_remainder import clipped_fraction
    result=clipped_fraction(q0,q0-F(3,8),q0+F(3,8),start=start,period=F(1,4))
    assert F(result['clock_row'])==row
    clip=lambda q:max(F(0),min(F(1),(q-start)*4))
    assert F(result['center'])==clip(q0)
    for i in range(41):
        q=q0-F(3,8)+F(3,4)*F(i,40)
        assert abs(clip(q)-clip(q0)-row*(q-q0))<=F(result['remainder'])


def test_scalar_product_keeps_correlated_calibration_and_clock_errors():
    from lll.ilvis0_source_remainder import calibration,clipped_fraction,multiply
    a=calibration(F(1,512),F(1,256),bias_center=0,gain_center=0,
        bias_lower=F(-1,2),bias_upper=F(1,2),gain_lower=F(-1,4),gain_upper=F(1,4))
    b=clipped_fraction(F(1,4),0,F(1,2),start=0,period=F(1,4));result=multiply(a,b)
    for i in range(-20,21):
        x=F(i,20);bias=x/2;gain=x/4;q=F(1,4)+x/4
        corrected=(F(1,512)-bias/256)/(1+gain)
        fraction=max(F(0),min(F(1),q*4))
        derivative_a=-bias/256-F(1,512)*gain
        derivative_b=4*(q-F(1,4))
        linear=derivative_a+F(1,512)*derivative_b
        assert abs(corrected*fraction-F(result['center'])-linear)<=F(result['remainder'])


@pytest.mark.parametrize('angle',(0.001,.1,.6))
def test_noncommuting_prefix_bound_contains_independent_rotation_values(angle):
    from lll.ilvis0_source_remainder import rotation_prefix
    from lll.ilvis0_rotation_roundoff import enclose
    t=F(angle);bound=rotation_prefix([abs(t),abs(t)],[0,0],[0,0],maximum_packets=2)
    first=enclose([angle,0.,0.],[[1.,0.,0.],[0.,1.,0.],[0.,0.,1.]])
    second=enclose([0.,angle,0.],[[1.,0.,0.],[0.,1.,0.],[0.,0.,1.]])
    intervals=[]
    for i in range(3):
        line=[]
        for j in range(3):
            terms=[]
            for k in range(3):
                corners=[F(first[a][i][k])*F(second[b][k][j]) for a in ('lower','upper') for b in ('lower','upper')]
                terms.append((min(corners),max(corners)))
            line.append((sum(v[0] for v in terms),sum(v[1] for v in terms)))
        intervals.append(line)
    linear=[[F(i==j) for j in range(3)] for i in range(3)]
    for i,j,sign in ((1,2,-1),(2,1,1),(0,2,1),(2,0,-1)):linear[i][j]+=sign*t
    for vector in ((F(1),0,0),(0,F(1),0),(0,0,F(1)),(F(3,5),F(4,5),0)):
        radii=[]
        for i in range(3):
            ends=[]
            for j,v in enumerate(vector):
                lo,hi=intervals[i][j];ends.append(sorted(((lo-linear[i][j])*v,(hi-linear[i][j])*v)))
            radii.append(max(abs(sum(e[0] for e in ends)),abs(sum(e[1] for e in ends))))
        assert sum(r*r for r in radii)<=F(bound['remainder'])**2


def test_force_product_remainder_contains_shared_parameter_polynomials():
    from lll.ilvis0_source_remainder import force_products
    radius=F(1,5);r1,r2=F(1,3),F(1,7);p0,p1,p2=F(1,8),F(-1,4),F(1,11)
    f0,f1,f2=F(10),F(-1,2),F(1,13)
    change=lambda a,b:abs(a)*radius+abs(b)*radius**2
    result=force_products(mount_norm=1,nominal_departure=abs(p0),force_norm=abs(f0),
        mount_change=change(r1,r2),mount_remainder=abs(r2)*radius**2,
        prefix_change=change(p1,p2),prefix_remainder=abs(p2)*radius**2,
        force_change=change(f1,f2),force_remainder=abs(f2)*radius**2)
    for i in range(-20,21):
        x=radius*F(i,20);r=1+r1*x+r2*x*x;p=p0+p1*x+p2*x*x;f=f0+f1*x+f2*x*x
        assert abs(r*f-f0-(r1*f0+f1)*x)<=F(result['a_remainder'])
        assert abs(r*p*f-p0*f0-(r1*p0*f0+p1*f0+p0*f1)*x)<=F(result['b_remainder'])


def test_nonzero_reference_prefix_with_nonlinear_arguments():
    from lll.ilvis0_source_remainder import rotation_prefix
    from lll.ilvis0_exact_scale import sqrt_upper
    from lll.ilvis0_rotation_roundoff import enclose as values
    from lll.ilvis0_rotation_derivative import enclose as derivatives
    nominal=[[F(1,8),F(-1,16),F(1,32)],[F(-1,32),F(3,32),F(1,16)]]
    linear=[[F(1,512),F(-1,1024),F(1,2048)],[F(-1,1024),F(1,512),F(1,1024)]]
    quadratic=[[F(1,8192),F(1,16384),F(0)],[F(0),F(-1,8192),F(1,16384)]]
    norm=lambda v:F(sqrt_upper(sum(x*x for x in v)))
    d=[norm(a)+norm(b) for a,b in zip(linear,quadratic)]
    bound=rotation_prefix(d,list(map(norm,quadratic)),list(map(norm,nominal)),maximum_packets=2)
    identity=[[float(i==j) for j in range(3)] for i in range(3)]
    def interval_matrix(proof):
        return [[(F(proof['lower'][i][j]),F(proof['upper'][i][j])) for j in range(3)] for i in range(3)]
    def add(a,b):return [[(a[i][j][0]+b[i][j][0],a[i][j][1]+b[i][j][1]) for j in range(3)] for i in range(3)]
    def scale(a,x):return [[tuple(sorted((lo*x,hi*x))) for lo,hi in row] for row in a]
    def product(a,b):
        result=[]
        for i in range(3):
            row=[]
            for j in range(3):
                terms=[sorted(x*y for x in a[i][k] for y in b[k][j]) for k in range(3)]
                row.append((sum(t[0] for t in terms),sum(t[-1] for t in terms)))
            result.append(row)
        return result
    base=[];jac=[]
    for angle,direction in zip(nominal,linear):
        argument=list(map(float,angle));base.append(interval_matrix(values(argument,identity)))
        derivative=derivatives(argument);terms=[]
        for axis,component in enumerate(direction):
            matrix=[[(F(derivative['lower'][axis][i][j]),F(derivative['upper'][axis][i][j])) for j in range(3)] for i in range(3)]
            terms.append(scale(matrix,component))
        jac.append(add(add(terms[0],terms[1]),terms[2]))
    center=product(*base);row=add(product(jac[0],base[1]),product(base[0],jac[1]))
    for u in (F(-1),F(-1,2),F(0),F(1,2),F(1)):
        rotations=[]
        for a,b,c in zip(nominal,linear,quadratic):
            angle=[x+u*y+u*u*z for x,y,z in zip(a,b,c)]
            assert all(F(float(x))==x for x in angle)
            rotations.append(interval_matrix(values(list(map(float,angle)),identity)))
        error=add(add(product(*rotations),scale(center,-1)),scale(row,-u))
        for vector in ((F(1),0,0),(0,F(1),0),(0,0,F(1)),(F(3,5),F(4,5),0)):
            radii=[]
            for i in range(3):
                ends=[sorted((lo*v,hi*v)) for (lo,hi),v in zip(error[i],vector)]
                radii.append(max(abs(sum(e[0] for e in ends)),abs(sum(e[1] for e in ends))))
            assert sum(r*r for r in radii)<=F(bound['remainder'])**2


def test_invalid_denominators_and_finite_work_limits_are_rejected():
    from lll.ilvis0_source_remainder import calibration,rotation_prefix
    with pytest.raises(ValueError):calibration(0,0,bias_center=0,gain_center=0,bias_lower=0,bias_upper=0,gain_lower=0,gain_upper=0)
    with pytest.raises(ValueError):calibration(0,1,bias_center=0,gain_center=0,bias_lower=0,bias_upper=0,gain_lower=-1,gain_upper=0)
    with pytest.raises(ValueError):rotation_prefix([1,1],[0,0],[0,0],maximum_packets=1)
    with pytest.raises(ValueError):rotation_prefix([-1],[0],[0],maximum_packets=1)
