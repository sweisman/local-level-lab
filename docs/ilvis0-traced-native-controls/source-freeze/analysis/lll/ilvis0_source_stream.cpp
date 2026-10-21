/* SPDX-License-Identifier: AGPL-3.0-or-later
 * Constant-memory body-source references using unchanged native primitives.
 */
#include "ilvis0_tangent.cpp"
#include <type_traits>

struct SourceState {
    Dual p[27],r[9],body[9],force[3];
    double time,elapsed;
};
static_assert(std::is_trivially_copyable<SourceState>::value,"serialized state must be trivially copyable");

extern "C" size_t ilvis0_source_stream_bytes(){return sizeof(SourceState);}

extern "C" int ilvis0_source_stream_init(void *buffer,size_t bytes,
    const double *initial_r,const double *limits,const double *point,
    const double *dv,double dt,double time) {
    if(bytes!=sizeof(SourceState)||!(dt>0.)||!std::isfinite(time))return 1;
    SourceState s;s.time=time;s.elapsed=0.;Dual mount[9];
    for(int j=0;j<27;j++){s.p[j]=point[j]*limits[j];s.p[j].d[j]=limits[j];}
    if(!std::isfinite((time+s.p[25]).v)||(time+s.p[25]).v<0.)return 2;
    for(int i=0;i<9;i++){s.r[i]=initial_r[i];s.body[i]=(i%4==0);}
    exponential(s.p,mount);mul(s.r,mount,s.r);
    for(int i=0;i<3;i++)s.force[i]=(dv[i]-s.p[12+i]*dt)/(1+s.p[18+i])/dt;
    memcpy(buffer,&s,sizeof s);return 0;
}

extern "C" int ilvis0_source_stream_append(void *buffer,size_t bytes,
    const double *raw,double dt,double *out,double *jacobian,double *timing) {
    if(bytes!=sizeof(SourceState)||!(dt>0.)||!std::isfinite(dt))return 1;
    SourceState s;memcpy(&s,buffer,sizeof s);
    double start=s.elapsed,end=start+dt;
    if(!std::isfinite(end)||end<=start)return 2;
    Dual query=s.time+s.p[25],fraction;double slope=0.;
    if((start<query.v&&query.v<=end)||(start==0.&&query.v==0.)) {
        fraction=(query-start)/dt;slope=1./dt;
    } else fraction=(query.v>end)?1.:0.;
    Dual corrected[3],a[3];mv(s.r,s.force,a);
    for(int i=0;i<3;i++)corrected[i]=(raw[i]-s.p[9+i]*dt)/(1+s.p[15+i])*fraction;
    for(int phase=0;phase<2;phase++) {
        Dual angle[3],rotation[9],body[9],departure[9],local[3],b[3];
        for(int i=0;i<3;i++)angle[i]=corrected[i]*(phase?1.:.5);
        exponential(angle,rotation);mul(s.body,rotation,body);
        for(int i=0;i<9;i++)departure[i]=body[i]-(i%4==0);
        mv(departure,s.force,local);mv(s.r,local,b);
        for(int source=0;source<2;source++)for(int axis=0;axis<3;axis++) {
            const Dual &v=source?b[axis]:a[axis];size_t row=(phase*2+source)*3+axis;
            if(!std::isfinite(v.v))return 3;
            out[row]=v.v;for(int j=0;j<27;j++)jacobian[row*27+j]=v.d[j];
        }
        if(phase)memcpy(s.body,body,sizeof body);
    }
    timing[0]=start;timing[1]=end;timing[2]=fraction.v;timing[3]=slope;timing[4]=query.v;
    s.elapsed=end;memcpy(buffer,&s,sizeof s);return 0;
}
