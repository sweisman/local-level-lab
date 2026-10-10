/* SPDX-License-Identifier: AGPL-3.0-or-later
 * Native-packet midpoint mechanization. No fast-math, decimation or smoothing.
 * The Python reference and deterministic tests specify its scientific semantics.
 */
#include <math.h>
#include <stddef.h>
#include <string.h>

static void mul(const double *a,const double *b,double *c) {
    double r[9];
    for(int i=0;i<3;i++) for(int j=0;j<3;j++) {
        r[3*i+j]=0; for(int k=0;k<3;k++) r[3*i+j]+=a[3*i+k]*b[3*k+j];
    }
    memcpy(c,r,sizeof r);
}
static void mv(const double *a,const double *v,double *r) {
    for(int i=0;i<3;i++) r[i]=a[3*i]*v[0]+a[3*i+1]*v[1]+a[3*i+2]*v[2];
}
static void cross(const double *a,const double *v,double *r) {
    r[0]=a[1]*v[2]-a[2]*v[1]; r[1]=a[2]*v[0]-a[0]*v[2]; r[2]=a[0]*v[1]-a[1]*v[0];
}
static void exponential(const double *v,double *r) {
    double q=v[0]*v[0]+v[1]*v[1]+v[2]*v[2],a,b;
    if(q<1e-4) {a=1-q/6+q*q/120-q*q*q/5040; b=.5-q/24+q*q/720-q*q*q/40320;}
    else {double x=sqrt(q); a=sin(x)/x; b=(1-cos(x))/q;}
    double k[9]={0,-v[2],v[1],v[2],0,-v[0],-v[1],v[0],0},kk[9];
    mul(k,k,kk); for(int i=0;i<9;i++) r[i]=(i%4==0)+a*k[i]+b*kk[i];
}
static void metric(int model,double phi,double h,double radius,double *mn,double *me) {
    if(model==2) {*mn=radius; *me=radius*(M_PI/2-phi);}
    else {double d=1-6.69437999014e-3*sin(phi)*sin(phi);
        *mn=6378137.*(1-6.69437999014e-3)/pow(d,1.5)+h;
        *me=(6378137./sqrt(d)+h)*cos(phi);}
}
static void rates(int model,const double *c,const double *v,double radius,double *r) {
    double mn,me; metric(model,c[0],c[2],radius,&mn,&me);
    r[0]=v[0]/mn; r[1]=v[1]/me; r[2]=-v[2];
}
static void context(int model,double phi,const double *rate,double *earth,double *transport) {
    earth[0]=model==0?7.2921150e-5*cos(phi):0; earth[1]=0;
    earth[2]=model==0?-7.2921150e-5*sin(phi):0;
    transport[0]=model==2?0:cos(phi)*rate[1]; transport[1]=model==2?0:-rate[0];
    transport[2]=model==2?-rate[1]:-sin(phi)*rate[1];
}
static void local(const double *r,const double *v,const double *theta,const double *dv,
    double dt,const double *earth,const double *transport,double phi,double removal,
    double gravity,double *rn,double *vn) {
    double win[3],a[3],left[9],right[9],middle[9],half[3],force[3],av[3],rhs[3],ar[3];
    /* Hypothesized removed Earth rate is the SAME conventional Earth vector for
       every candidate, not the candidate's own Earth rate. Coriolis stays physical. */
    for(int i=0;i<3;i++) {double standard=i==0?7.2921150e-5*cos(phi):(i==2?-7.2921150e-5*sin(phi):0);
        win[i]=earth[i]+transport[i]-removal*standard; half[i]=-win[i]*dt/2;
        a[i]=(2*earth[i]+transport[i])*dt/2;}
    exponential(half,left); for(int i=0;i<3;i++) half[i]=theta[i]/2;
    exponential(half,right); mul(left,r,middle); mul(middle,right,middle); mv(middle,dv,force);
    for(int i=0;i<3;i++) half[i]=-win[i]*dt; exponential(half,left);
    exponential(theta,right); mul(left,r,rn); mul(rn,right,rn);
    cross(a,v,av); for(int i=0;i<3;i++) rhs[i]=v[i]-av[i]+force[i]+(i==2?gravity*dt:0);
    cross(a,rhs,ar); double dot=a[0]*rhs[0]+a[1]*rhs[1]+a[2]*rhs[2];
    double den=1+a[0]*a[0]+a[1]*a[1]+a[2]*a[2];
    for(int i=0;i<3;i++) vn[i]=(rhs[i]-ar[i]+a[i]*dot)/den;
}
static void step(int model,double *c,double *v,double *r,const double *theta,const double *dv,
    double dt,double gravity,double radius,double removal) {
    double rate[3],middle[3],earth[3],transport[3],estimate[3],rn[9],vn[3],avg[3];
    rates(model,c,v,radius,rate); for(int i=0;i<3;i++) middle[i]=c[i]+rate[i]*dt/2;
    context(model,middle[0],rate,earth,transport);
    local(r,v,theta,dv,dt,earth,transport,middle[0],removal,gravity,rn,estimate);
    for(int i=0;i<3;i++) avg[i]=(v[i]+estimate[i])/2;
    rates(model,middle,avg,radius,rate); context(model,middle[0],rate,earth,transport);
    local(r,v,theta,dv,dt,earth,transport,middle[0],removal,gravity,rn,vn);
    for(int i=0;i<3;i++) c[i]+=rate[i]*dt;
    memcpy(v,vn,sizeof vn); memcpy(r,rn,sizeof rn);
}
int ilvis0_predict(size_t n,const double *theta,const double *dv,const double *dt,size_t m,
    const double *times,const double *initial_c,const double *initial_v,const double *initial_r,
    const double *lever,int model,double gravity,double radius,double removal,double *out) {
    double c[3],v[3],r[9],start=0; size_t j=0;
    memcpy(c,initial_c,sizeof c); memcpy(v,initial_v,sizeof v); memcpy(r,initial_r,sizeof r);
    for(size_t k=0;k<n;k++) {
        double end=start+dt[k];
        while(j<m && times[j]<=end) {
            double oc[3],ov[3],orr[9],th[3],vel[3],ln[3],offset[3];
            memcpy(oc,c,sizeof c); memcpy(ov,v,sizeof v); memcpy(orr,r,sizeof r);
            double f=fmax(0,fmin(1,(times[j]-start)/dt[k]));
            if(f>0) {for(int i=0;i<3;i++) {th[i]=theta[3*k+i]*f;vel[i]=dv[3*k+i]*f;}
                step(model,oc,ov,orr,th,vel,dt[k]*f,gravity,radius,removal);}
            mv(orr,lever,ln); rates(model,oc,ln,radius,offset);
            for(int i=0;i<3;i++) out[3*j+i]=oc[i]+offset[i]; j++;
        }
        if(j==m) return 0;
        if(!isfinite(c[0]+c[1]+c[2]) || fabs(c[0])>=M_PI/2-1e-6) return 2;
        step(model,c,v,r,theta+3*k,dv+3*k,dt[k],gravity,radius,removal); start=end;
    }
    return 1;
}
