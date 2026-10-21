/* SPDX-License-Identifier: AGPL-3.0-or-later
 * Source-only directed interval automatic differentiation. No trajectory fit.
 * Ideal rotations use an explicit series tail, with no libm accuracy premise.
 */
#include "ilvis0_compiled_bounds.cpp"
#include <cstring>
#include <type_traits>

namespace source_derivatives {
constexpr int N=27;
Interval neg(Interval a){return {-a.hi,-a.lo};}
Interval reciprocal(Interval a){
    if(a.lo<=0&&a.hi>=0)throw Unsupported{2};
    auto inverse=[](double v){if(v==1||v==-1)return Interval{v,v};double q=1./v;
        if(!std::isfinite(q))throw Unsupported{3};return Interval{down(q),up(q)};};
    return {inverse(a.hi).lo,inverse(a.lo).hi};
}
double magnitude(Interval a){return std::max(std::fabs(a.lo),std::fabs(a.hi));}
struct Jet {
    Interval v{0.,0.};Interval d[N]{};
    Jet()=default;
    Jet(double x):v{x,x}{}
};
Jet operator+(const Jet&a,const Jet&b){Jet o;o.v=plus(a.v,b.v);for(int j=0;j<N;j++)o.d[j]=plus(a.d[j],b.d[j]);return o;}
Jet operator-(const Jet&a){Jet o;o.v=neg(a.v);for(int j=0;j<N;j++)o.d[j]=neg(a.d[j]);return o;}
Jet operator-(const Jet&a,const Jet&b){return a+(-b);}
Jet operator*(const Jet&a,const Jet&b){
    Jet o;o.v=product(a.v,b.v);
    for(int j=0;j<N;j++)o.d[j]=plus(product(a.d[j],b.v),product(a.v,b.d[j]));
    return o;
}
Jet inverse(const Jet&a){
    Jet o;o.v=reciprocal(a.v);Interval square=product(o.v,o.v);
    for(int j=0;j<N;j++)o.d[j]=neg(product(a.d[j],square));
    return o;
}
Jet operator/(const Jet&a,const Jet&b){return a*inverse(b);}
void widen(Jet &a,double value_error,double derivative_error,const Jet&q){
    a.v=plus(a.v,{-value_error,value_error});
    for(int j=0;j<N;j++){
        double e=mul_up(derivative_error,magnitude(q.d[j]));a.d[j]=plus(a.d[j],{-e,e});
    }
}

void coefficients(const Jet &q,Jet &a,Jet &b){
    double maximum=q.v.hi;if(q.v.lo<0||maximum>81)throw Unsupported{2};
    Jet ta(1.),tb(.5);a=ta;b=tb;
    double ma=1.,mb=.5,da=0.,db=0.;
    for(int k=1;k<=80;k++){
        double ad=(2*k)*(2*k+1),bd=(2*k+1)*(2*k+2);
        ta=-ta*q/Jet(ad);tb=-tb*q/Jet(bd);a=a+ta;b=b+tb;
        double nda=div_up(add_up(mul_up(da,maximum),ma),ad);
        double ndb=div_up(add_up(mul_up(db,maximum),mb),bd);
        ma=div_up(mul_up(ma,maximum),ad);mb=div_up(mul_up(mb,maximum),bd);da=nda;db=ndb;
        int next=k+1;ad=(2*next)*(2*next+1);bd=(2*next+1)*(2*next+2);
        double ea=mul_up(2.,div_up(mul_up(ma,maximum),ad));
        double eb=mul_up(2.,div_up(mul_up(mb,maximum),bd));
        double eja=mul_up(2.,div_up(add_up(mul_up(da,maximum),ma),ad));
        double ejb=mul_up(2.,div_up(add_up(mul_up(db,maximum),mb),bd));
        // After the first omitted term, the absolute derivative-series ratio
        // is at most 2*q / ((2*next+2)*(2*next+3)); value ratios are smaller.
        double ratio=div_up(mul_up(2.,maximum),(2*next+2)*(2*next+3));
        if(ratio<=.5&&std::max({ea,eb,eja,ejb})<1e-32){widen(a,ea,eja,q);widen(b,eb,ejb,q);return;}
    }
    throw Unsupported{3};
}
void multiply(const Jet*a,const Jet*b,Jet*out){
    Jet temporary[9];
    for(int i=0;i<3;i++)for(int j=0;j<3;j++)for(int k=0;k<3;k++)temporary[3*i+j]=temporary[3*i+j]+a[3*i+k]*b[3*k+j];
    std::memcpy(out,temporary,sizeof temporary);
}
void apply(const Jet*a,const Jet*b,Jet*out){
    Jet temporary[3];for(int i=0;i<3;i++)for(int j=0;j<3;j++)temporary[i]=temporary[i]+a[3*i+j]*b[j];
    std::memcpy(out,temporary,sizeof temporary);
}
void rotation(const Jet*angle,Jet*out){
    Jet q;for(int i=0;i<3;i++)q=q+angle[i]*angle[i];q.v.lo=std::max(0.,q.v.lo);
    Jet a,b;coefficients(q,a,b);
    Jet k[9]={Jet(0),-angle[2],angle[1],angle[2],Jet(0),-angle[0],-angle[1],angle[0],Jet(0)},square[9];
    multiply(k,k,square);for(int i=0;i<9;i++)out[i]=Jet(i%4==0)+a*k[i]+b*square[i];
}
Jet clip_fraction(const Jet&query,double start,double period){
    Jet f=(query-Jet(start))/Jet(period);
    if(f.v.hi<=0)return Jet(0);if(f.v.lo>=1)return Jet(1);
    bool crosses=f.v.lo<=0||f.v.hi>=1;
    f.v.lo=std::max(0.,f.v.lo);f.v.hi=std::min(1.,f.v.hi);
    if(crosses)for(int j=0;j<N;j++){f.d[j].lo=std::min(0.,f.d[j].lo);f.d[j].hi=std::max(0.,f.d[j].hi);}
    return f;
}
struct Path {Jet p[N],r[9],body[9],force[3],query;};
struct State {Path point,domain;double elapsed;};
static_assert(std::is_trivially_copyable<State>::value,"fixed state must be copyable");
void initialize(Path&s,const double*initial,const double*limits,const double*z,const double*lo,const double*hi,
    const double*dv,double dt,double time,bool point){
    for(int j=0;j<N;j++){
        Jet x(z[j]);
        if(!point){x.v={std::min(lo[j],z[j]),std::max(hi[j],z[j])};x.d[j]={1.,1.};}
        s.p[j]=x*Jet(limits[j]);
    }
    for(int i=0;i<9;i++){s.r[i]=Jet(initial[i]);s.body[i]=Jet(i%4==0);}
    Jet mount[9];rotation(s.p,mount);multiply(s.r,mount,s.r);
    for(int i=0;i<3;i++)s.force[i]=(Jet(dv[i])-s.p[12+i]*Jet(dt))/(Jet(1)+s.p[18+i])/Jet(dt);
    s.query=Jet(time)+s.p[25];
}
void advance(Path&s,const double*raw,double start,double dt,Jet*out){
    Jet fraction=clip_fraction(s.query,start,dt),corrected[3],a[3];apply(s.r,s.force,a);
    for(int i=0;i<3;i++)corrected[i]=(Jet(raw[i])-s.p[9+i]*Jet(dt))/(Jet(1)+s.p[15+i])*fraction;
    for(int phase=0;phase<2;phase++){
        Jet angle[3],step[9],body[9],departure[9],local[3],b[3];
        for(int i=0;i<3;i++)angle[i]=corrected[i]*Jet(phase?1.:.5);
        rotation(angle,step);multiply(s.body,step,body);
        for(int i=0;i<9;i++)departure[i]=body[i]-Jet(i%4==0);
        apply(departure,s.force,local);apply(s.r,local,b);
        for(int source=0;source<2;source++)for(int axis=0;axis<3;axis++)out[(phase*2+source)*3+axis]=source?b[axis]:a[axis];
        if(phase)std::memcpy(s.body,body,sizeof body);
    }
}
}

extern "C" size_t ilvis0_source_intervals_bytes(){return sizeof(source_derivatives::State);}
extern "C" int ilvis0_source_intervals_rotation(const double*angle,double*value,double*jac){
    using namespace source_derivatives;
    try{
        if(!runtime_ok())return 1;check(angle,3);Jet x[3],r[9];
        for(int i=0;i<3;i++){x[i]=Jet(angle[i]);x[i].d[i]={1,1};}rotation(x,r);
        for(int i=0;i<9;i++){
            value[2*i]=r[i].v.lo;value[2*i+1]=r[i].v.hi;
            for(int j=0;j<3;j++){jac[(i*3+j)*2]=r[i].d[j].lo;jac[(i*3+j)*2+1]=r[i].d[j].hi;}
        }return 0;
    }catch(Unsupported e){return e.code;}
}
extern "C" int ilvis0_source_intervals_init(void*buffer,size_t bytes,const double*initial,const double*limits,
    const double*z,const double*lo,const double*hi,const double*dv,double dt,double time){
    using namespace source_derivatives;
    try{
        if(!runtime_ok())return 1;if(bytes!=sizeof(State)||!(dt>0.)||!std::isfinite(dt)||!std::isfinite(time))return 2;
        check(initial,9);check(limits,N,true);check(z,N);check(lo,N);check(hi,N);check(dv,3);
        for(int j=0;j<N;j++)if(lo[j]>hi[j])return 2;
        State s;s.elapsed=0.;initialize(s.point,initial,limits,z,lo,hi,dv,dt,time,true);
        initialize(s.domain,initial,limits,z,lo,hi,dv,dt,time,false);std::memcpy(buffer,&s,sizeof s);return 0;
    }catch(Unsupported e){return e.code;}
}
extern "C" int ilvis0_source_intervals_append(void*buffer,size_t bytes,const double*raw,double dt,
    double*point,double*values,double*jac){
    using namespace source_derivatives;
    try{
        if(!runtime_ok())return 1;if(bytes!=sizeof(State)||!(dt>0.)||!std::isfinite(dt))return 2;check(raw,3);
        State s;std::memcpy(&s,buffer,sizeof s);double end=s.elapsed+dt;
        if(!std::isfinite(end)||end<=s.elapsed)return 2;
        Jet p[12],v[12];advance(s.point,raw,s.elapsed,dt,p);advance(s.domain,raw,s.elapsed,dt,v);
        for(int i=0;i<12;i++){
            point[2*i]=p[i].v.lo;point[2*i+1]=p[i].v.hi;values[2*i]=v[i].v.lo;values[2*i+1]=v[i].v.hi;
            for(int j=0;j<N;j++){jac[(i*N+j)*2]=v[i].d[j].lo;jac[(i*N+j)*2+1]=v[i].d[j].hi;}
        }
        s.elapsed=end;std::memcpy(buffer,&s,sizeof s);return 0;
    }catch(Unsupported e){return e.code;}
}
