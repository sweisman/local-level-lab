/* SPDX-License-Identifier: AGPL-3.0-or-later
 * State transport only. Equations come from the included unchanged kernel.
 * Keep the preceding packet for left-interval latency derivatives at a restart.
 */
typedef struct {
    SCALAR p[27], c[3], v[3], r[9];
    SCALAR previous_c[3], previous_v[3], previous_r[9], th[3], dv[3];
    double elapsed, previous_start, previous_dt, gravity, radius;
    size_t count;
    int model;
} StreamState;

EXPORT size_t ilvis0_stream_size(void) { return sizeof(StreamState); }
EXPORT double ilvis0_stream_clock(const void *memory) { return ((const StreamState*)memory)->elapsed; }
EXPORT size_t ilvis0_stream_count(const void *memory) { return ((const StreamState*)memory)->count; }

EXPORT void ilvis0_stream_init(void *memory, const double *c,const double *v,const double *r,
    const double *limits,const double *point,int model,int profile,double gravity,double radius) {
#if IS_TANGENT
    StreamState *s=new(memory) StreamState{};
#else
    StreamState *s=(StreamState*)memory;
    memset(s,0,sizeof(*s));
#endif
    SCALAR offset[3],rot[9];
    s->gravity=gravity;s->radius=radius;s->model=model;
    for(int i=0;i<27;i++) {
        s->p[i]=point[i]*limits[i];
        SET_DERIVATIVE(s->p[i],i,limits[i]);
    }
    if(profile) s->p[26]=(s->p[26]+1)/2; else s->p[26]=0;
    for(int i=0;i<3;i++) { s->c[i]=c[i];s->v[i]=v[i]+s->p[3+i]; }
    rates(model,s->c,s->p+6,radius,offset);
    for(int i=0;i<3;i++) s->c[i]+=offset[i];
    for(int i=0;i<9;i++) s->r[i]=r[i];
    exponential(s->p,rot);mul(s->r,rot,s->r);
}

static int stream_observe(const StreamState *s,double time,double *out,double *jac,int *boundaries,
    const SCALAR *c,const SCALAR *v,const SCALAR *r,const SCALAR *th,const SCALAR *dv,
    double start,double duration) {
    SCALAR oc[3],ov[3],orr[9],offset[3],ln[3],pt[3],pd[3];
    SCALAR fraction=(time+s->p[25]-start)/duration;
    if(NUMBER(fraction)<-1e-10 || NUMBER(fraction)>1+1e-10)return 3;
    if(NUMBER(fraction)<1e-8 || NUMBER(fraction)>1-1e-8)(*boundaries)++;
    memcpy(oc,c,sizeof oc);memcpy(ov,v,sizeof ov);memcpy(orr,r,sizeof orr);
    for(int i=0;i<3;i++) {pt[i]=th[i]*fraction;pd[i]=dv[i]*fraction;}
#if IS_TANGENT
    step(s->model,oc,ov,orr,pt,pd,duration*fraction,s->gravity+s->p[24],s->radius,s->p[26]);
#else
    if(fraction>0)step(s->model,oc,ov,orr,pt,pd,duration*fraction,s->gravity+s->p[24],s->radius,s->p[26]);
#endif
    mv(orr,s->p+21,ln);rates(s->model,oc,ln,s->radius,offset);
    for(int i=0;i<3;i++) {
        SCALAR value=oc[i]+offset[i];out[i]=NUMBER(value);
        if(!isfinite(out[i]))return 2;
#if IS_TANGENT
        for(int h=0;h<27;h++)jac[27*i+h]=value.d[h];
#endif
    }
    return 0;
}

EXPORT int ilvis0_stream_push(void *memory,size_t n,const double *theta,const double *dv,
    const double *dt,size_t m,const double *times,double *out,double *jac,int *boundaries) {
    StreamState *s=(StreamState*)memory;size_t j=0;int code;*boundaries=0;
    /* A deferred query exactly at the new block's start belongs to the old
       packet. Using fraction zero in the next packet changes tangent lane 25. */
    while(s->count && j<m && times[j]+NUMBER(s->p[25])==s->elapsed) {
        code=stream_observe(s,times[j],out+3*j,IS_TANGENT ? jac+81*j : jac,boundaries,
            s->previous_c,s->previous_v,s->previous_r,s->th,s->dv,s->previous_start,s->previous_dt);
        if(code)return code;j++;
    }
    for(size_t k=0;k<n;k++) {
        double end=s->elapsed+dt[k];SCALAR th[3],vel[3];
        if(!isfinite(NUMBER(s->c[0])+NUMBER(s->c[1])+NUMBER(s->c[2])) ||
            fabs(NUMBER(s->c[0]))>=M_PI/2-1e-6)return 2;
        for(int i=0;i<3;i++) {
            th[i]=(theta[3*k+i]-s->p[9+i]*dt[k])/(1+s->p[15+i]);
            vel[i]=(dv[3*k+i]-s->p[12+i]*dt[k])/(1+s->p[18+i]);
        }
        while(j<m && times[j]+NUMBER(s->p[25])<=end) {
            code=stream_observe(s,times[j],out+3*j,IS_TANGENT ? jac+81*j : jac,boundaries,
                s->c,s->v,s->r,th,vel,s->elapsed,dt[k]);
            if(code)return code;j++;
        }
        memcpy(s->previous_c,s->c,sizeof s->c);memcpy(s->previous_v,s->v,sizeof s->v);
        memcpy(s->previous_r,s->r,sizeof s->r);memcpy(s->th,th,sizeof th);memcpy(s->dv,vel,sizeof vel);
        s->previous_start=s->elapsed;s->previous_dt=dt[k];
        step(s->model,s->c,s->v,s->r,th,vel,dt[k],s->gravity+s->p[24],s->radius,s->p[26]);
        s->elapsed=end;s->count++;
        for(int i=0;i<3;i++) if(!isfinite(NUMBER(s->c[i])) || !isfinite(NUMBER(s->v[i])))return 2;
        if(fabs(NUMBER(s->c[0]))>=M_PI/2-1e-6)return 2;
    }
    return j==m ? 0 : 1;
}
