/* SPDX-License-Identifier: AGPL-3.0-or-later
 * Point-value and one-sided derivative enclosures for the ideal source law.
 * Existing domain-derivative kernel remains unchanged. No geographic solver.
 */
#include "ilvis0_source_derivative_intervals.cpp"

namespace source_point {
using namespace source_derivatives;
struct State {Path point;double elapsed;};
static_assert(std::is_trivially_copyable<State>::value,"fixed state must be copyable");

Jet fraction(const Jet&query,double start,double period){
    Jet f=(query-Jet(start))/Jet(period);
    // At either knot include both one-sided derivatives. In particular retain
    // the native preceding-packet derivative at an exact packet endpoint.
    if(f.v.hi<0)return Jet(0);if(f.v.lo>1)return Jet(1);
    bool knot=f.v.lo<=0||f.v.hi>=1;
    f.v.lo=std::max(0.,f.v.lo);f.v.hi=std::min(1.,f.v.hi);
    if(knot)for(int j=0;j<N;j++){
        f.d[j].lo=std::min(0.,f.d[j].lo);f.d[j].hi=std::max(0.,f.d[j].hi);
    }
    return f;
}
void advance_point(Path&s,const double*raw,double start,double dt,Jet*out){
    Jet portion=fraction(s.query,start,dt),corrected[3],a[3];apply(s.r,s.force,a);
    for(int i=0;i<3;i++)corrected[i]=(Jet(raw[i])-s.p[9+i]*Jet(dt))/(Jet(1)+s.p[15+i])*portion;
    for(int phase=0;phase<2;phase++){
        Jet angle[3],step[9],body[9],departure[9],local[3],b[3];
        for(int i=0;i<3;i++)angle[i]=corrected[i]*Jet(phase?1.:.5);
        rotation(angle,step);multiply(s.body,step,body);
        for(int i=0;i<9;i++)departure[i]=body[i]-Jet(i%4==0);
        apply(departure,s.force,local);apply(s.r,local,b);
        for(int source=0;source<2;source++)for(int axis=0;axis<3;axis++)
            out[(phase*2+source)*3+axis]=source?b[axis]:a[axis];
        if(phase)std::memcpy(s.body,body,sizeof body);
    }
}
}

extern "C" size_t ilvis0_source_point_bytes(){return sizeof(source_point::State);}
extern "C" int ilvis0_source_point_init(void*buffer,size_t bytes,const double*initial,const double*limits,
    const double*z,const double*dv,double dt,double time){
    using namespace source_derivatives;
    try{
        if(!runtime_ok())return 1;
        if(bytes!=sizeof(source_point::State)||!(dt>0.)||!std::isfinite(dt)||!std::isfinite(time))return 2;
        check(initial,9);check(limits,N,true);check(z,N);check(dv,3);
        source_point::State s;s.elapsed=0.;
        initialize(s.point,initial,limits,z,z,z,dv,dt,time,false);
        std::memcpy(buffer,&s,sizeof s);return 0;
    }catch(Unsupported e){return e.code;}
}
extern "C" int ilvis0_source_point_append(void*buffer,size_t bytes,const double*raw,double dt,
    double*values,double*jac){
    using namespace source_derivatives;
    try{
        if(!runtime_ok())return 1;
        if(bytes!=sizeof(source_point::State)||!(dt>0.)||!std::isfinite(dt))return 2;check(raw,3);
        source_point::State s;std::memcpy(&s,buffer,sizeof s);double end=s.elapsed+dt;
        if(!std::isfinite(end)||end<=s.elapsed)return 2;
        Jet v[12];source_point::advance_point(s.point,raw,s.elapsed,dt,v);
        for(int i=0;i<12;i++){
            values[2*i]=v[i].v.lo;values[2*i+1]=v[i].v.hi;
            for(int j=0;j<N;j++){jac[(i*N+j)*2]=v[i].d[j].lo;jac[(i*N+j)*2+1]=v[i].d[j].hi;}
        }
        s.elapsed=end;std::memcpy(buffer,&s,sizeof s);return 0;
    }catch(Unsupported e){return e.code;}
}
