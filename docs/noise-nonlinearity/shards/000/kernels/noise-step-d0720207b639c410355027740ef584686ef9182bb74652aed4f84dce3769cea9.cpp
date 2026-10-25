// Diagnostic internal arithmetic; original equations, ABI and packet clock.
#include <limits>
/* SPDX-License-Identifier: AGPL-3.0-or-later
 * Forward derivatives of native-packet mechanization; separate refinement freeze.
 * Equations copied from ilvis0_native.c, retaining every measured packet.
 */
#include <cmath>
#include <cstddef>
#include <cstring>
#include <array>
#include <algorithm>

struct Dual {
    long double v; std::array<long double,15> d;
    Dual(long double value=0):v(value) { d.fill(0); }
    Dual& operator+=(const Dual& b);
};
static Dual operator+(const Dual& a,const Dual& b) { Dual r(a.v+b.v); for(int i=0;i<15;i++)r.d[i]=a.d[i]+b.d[i]; return r; }
static Dual operator-(const Dual& a,const Dual& b) { Dual r(a.v-b.v); for(int i=0;i<15;i++)r.d[i]=a.d[i]-b.d[i]; return r; }
static Dual operator-(const Dual& a) { Dual r(-a.v); for(int i=0;i<15;i++)r.d[i]=-a.d[i]; return r; }
static Dual operator*(const Dual& a,const Dual& b) { Dual r(a.v*b.v); for(int i=0;i<15;i++)r.d[i]=a.d[i]*b.v+a.v*b.d[i]; return r; }
static Dual operator/(const Dual& a,const Dual& b) { Dual r(a.v/b.v); for(int i=0;i<15;i++)r.d[i]=(a.d[i]-r.v*b.d[i])/b.v; return r; }
Dual& Dual::operator+=(const Dual& b) { *this=*this+b; return *this; }
static Dual sin(const Dual& a) { Dual r(std::sin(a.v)); long double q=std::cos(a.v); for(int i=0;i<15;i++)r.d[i]=q*a.d[i]; return r; }
static Dual cos(const Dual& a) { Dual r(std::cos(a.v)); long double q=-std::sin(a.v); for(int i=0;i<15;i++)r.d[i]=q*a.d[i]; return r; }
static Dual sqrt(const Dual& a) { Dual r(std::sqrt(a.v)); for(int i=0;i<15;i++)r.d[i]=a.d[i]/(2*r.v); return r; }
static Dual pow(const Dual& a,double b) { Dual r(std::pow(a.v,b)); long double q=b*std::pow(a.v,b-1); for(int i=0;i<15;i++)r.d[i]=q*a.d[i]; return r; }
static bool operator<(const Dual&a,double b) {return a.v<b;}

static void mul(const Dual *a,const Dual *b,Dual *c) {
    Dual r[9];
    for(int i=0;i<3;i++) for(int j=0;j<3;j++) {
        r[3*i+j]=0; for(int k=0;k<3;k++) r[3*i+j]+=a[3*i+k]*b[3*k+j];
    }
    memcpy(c,r,sizeof r);
}
static void mv(const Dual *a,const Dual *v,Dual *r) {
    for(int i=0;i<3;i++) r[i]=a[3*i]*v[0]+a[3*i+1]*v[1]+a[3*i+2]*v[2];
}
static void cross(const Dual *a,const Dual *v,Dual *r) {
    r[0]=a[1]*v[2]-a[2]*v[1]; r[1]=a[2]*v[0]-a[0]*v[2]; r[2]=a[0]*v[1]-a[1]*v[0];
}
static void exponential(const Dual *v,Dual *r) {
    Dual q=v[0]*v[0]+v[1]*v[1]+v[2]*v[2],a,b;
    if(q<1e-4) {a=1-q/6+q*q/120-q*q*q/5040; b=.5-q/24+q*q/720-q*q*q/40320;}
    else {Dual x=sqrt(q); a=sin(x)/x; b=(1-cos(x))/q;}
    Dual k[9]={0,-v[2],v[1],v[2],0,-v[0],-v[1],v[0],0},kk[9];
    mul(k,k,kk); for(int i=0;i<9;i++) r[i]=(i%4==0)+a*k[i]+b*kk[i];
}
static void metric(int model,Dual phi,Dual h,Dual radius,Dual *mn,Dual *me) {
    if(model==2) {*mn=radius; *me=radius*(M_PI/2-phi);}
    else {Dual d=1-6.69437999014e-3*sin(phi)*sin(phi);
        *mn=6378137.*(1-6.69437999014e-3)/pow(d,1.5)+h;
        *me=(6378137./sqrt(d)+h)*cos(phi);}
}
static void rates(int model,const Dual *c,const Dual *v,Dual radius,Dual *r) {
    Dual mn,me; metric(model,c[0],c[2],radius,&mn,&me);
    r[0]=v[0]/mn; r[1]=v[1]/me; r[2]=-v[2];
}
static void context(int model,Dual phi,const Dual *rate,Dual *earth,Dual *transport) {
    earth[0]=model==0?7.2921150e-5*cos(phi):0; earth[1]=0;
    earth[2]=model==0?-7.2921150e-5*sin(phi):0;
    transport[0]=model==2?0:cos(phi)*rate[1]; transport[1]=model==2?0:-rate[0];
    transport[2]=model==2?-rate[1]:-sin(phi)*rate[1];
}
static void local(const Dual *r,const Dual *v,const Dual *theta,const Dual *dv,
    Dual dt,const Dual *earth,const Dual *transport,Dual phi,Dual removal,
    Dual gravity,Dual *rn,Dual *vn) {
    Dual win[3],a[3],left[9],right[9],middle[9],half[3],force[3],av[3],rhs[3],ar[3];
    /* Hypothesized removed Earth rate is the SAME conventional Earth vector for
       every candidate, not the candidate's own Earth rate. Coriolis stays physical. */
    for(int i=0;i<3;i++) {Dual standard=i==0?7.2921150e-5*cos(phi):(i==2?-7.2921150e-5*sin(phi):0);
        win[i]=earth[i]+transport[i]-removal*standard; half[i]=-win[i]*dt/2;
        a[i]=(2*earth[i]+transport[i])*dt/2;}
    exponential(half,left); for(int i=0;i<3;i++) half[i]=theta[i]/2;
    exponential(half,right); mul(left,r,middle); mul(middle,right,middle); mv(middle,dv,force);
    for(int i=0;i<3;i++) half[i]=-win[i]*dt; exponential(half,left);
    exponential(theta,right); mul(left,r,rn); mul(rn,right,rn);
    cross(a,v,av); for(int i=0;i<3;i++) rhs[i]=v[i]-av[i]+force[i]+(i==2?gravity*dt:0);
    cross(a,rhs,ar); Dual dot=a[0]*rhs[0]+a[1]*rhs[1]+a[2]*rhs[2];
    Dual den=1+a[0]*a[0]+a[1]*a[1]+a[2]*a[2];
    for(int i=0;i<3;i++) vn[i]=(rhs[i]-ar[i]+a[i]*dot)/den;
}
static void step_gravity(int model,Dual *c,Dual *v,Dual *r,const Dual *theta,const Dual *dv,
    Dual dt,Dual gravity,Dual radius,Dual removal,int height_gravity,double anchor_height) {
    Dual rate[3],middle[3],earth[3],transport[3],estimate[3],rn[9],vn[3],avg[3];
    rates(model,c,v,radius,rate); for(int i=0;i<3;i++) middle[i]=c[i]+rate[i]*dt/2;
    if(height_gravity) {
        Dual q=(6371000.+anchor_height)/(6371000.+middle[2]);
        gravity=middle[2].v>-6371000.?gravity*q*q:Dual(NAN);
    }
    context(model,middle[0],rate,earth,transport);
    local(r,v,theta,dv,dt,earth,transport,middle[0],removal,gravity,rn,estimate);
    for(int i=0;i<3;i++) avg[i]=(v[i]+estimate[i])/2;
    rates(model,middle,avg,radius,rate); context(model,middle[0],rate,earth,transport);
    local(r,v,theta,dv,dt,earth,transport,middle[0],removal,gravity,rn,vn);
    for(int i=0;i<3;i++) c[i]+=rate[i]*dt;
    memcpy(v,vn,sizeof vn); memcpy(r,rn,sizeof rn);
}
static void step(int model,Dual *c,Dual *v,Dual *r,const Dual *theta,const Dual *dv,
    Dual dt,Dual gravity,Dual radius,Dual removal) {
    step_gravity(model,c,v,r,theta,dv,dt,gravity,radius,removal,0,0.);
}
/* SPDX-License-Identifier: AGPL-3.0-or-later
 * Appended to a source-bound wider header; scientific motion helpers reused.
 */
extern "C" int lll_noise_step_bits(){return std::numeric_limits<long double>::digits;}
extern "C" int lll_noise_step_size(){return sizeof(long double);}
extern "C" int lll_noise_step(const long double *c0,const long double *v0,
    const long double *r0,const long double *theta,const long double *dv,
    const long double *scalars,int model,int height_gravity,double anchor,
    const long double *lever,int seed,long double *state,double *jacobian,
    long double *observation,double *observation_jacobian) {
    if(model<0 || model>2 || (seed!=0 && seed!=1))return 4;
    Dual c[3],v[3],r[9],th[3],vel[3];
    for(int i=0;i<3;i++){
        c[i]=c0[i];v[i]=v0[i];th[i]=theta[i];vel[i]=dv[i];
        if(seed){c[i].d[6+i]=1;v[i].d[3+i]=1;th[i].d[9+i]=1;vel[i].d[12+i]=1;}
    }
    for(int i=0;i<9;i++)r[i]=r0[i];
    if(seed)for(int row=0;row<3;row++){
        r[3*row+1].d[0]=r0[3*row+2];r[3*row+2].d[0]=-r0[3*row+1];
        r[3*row].d[1]=-r0[3*row+2];r[3*row+2].d[1]=r0[3*row];
        r[3*row].d[2]=r0[3*row+1];r[3*row+1].d[2]=-r0[3*row];
    }
    step_gravity(model,c,v,r,th,vel,Dual(scalars[0]),Dual(scalars[1]),
        Dual(scalars[2]),Dual(scalars[3]),height_gravity,anchor);
    for(int i=0;i<3;i++){state[i]=c[i].v;state[3+i]=v[i].v;}
    for(int i=0;i<9;i++)state[6+i]=r[i].v;
    long double a[9];for(int i=0;i<9;i++)a[i]=r[i].v;
    long double inverse[9]={a[4]*a[8]-a[5]*a[7],a[2]*a[7]-a[1]*a[8],a[1]*a[5]-a[2]*a[4],
        a[5]*a[6]-a[3]*a[8],a[0]*a[8]-a[2]*a[6],a[2]*a[3]-a[0]*a[5],
        a[3]*a[7]-a[4]*a[6],a[1]*a[6]-a[0]*a[7],a[0]*a[4]-a[1]*a[3]};
    long double determinant=a[0]*inverse[0]+a[1]*inverse[3]+a[2]*inverse[6];
    if(!std::isfinite(determinant) || std::fabs(determinant)<1e-12L)return 2;
    for(int i=0;i<9;i++)inverse[i]/=determinant;
    for(int h=0;h<15;h++){
        long double s[9]={};
        for(int i=0;i<3;i++)for(int j=0;j<3;j++)for(int k=0;k<3;k++)
            s[3*i+j]+=inverse[3*i+k]*r[3*k+j].d[h];
        jacobian[h]=(s[7]-s[5])/2;
        jacobian[15+h]=(s[2]-s[6])/2;
        jacobian[30+h]=(s[3]-s[1])/2;
        for(int i=0;i<3;i++){jacobian[(3+i)*15+h]=v[i].d[h];jacobian[(6+i)*15+h]=c[i].d[h];}
    }
    Dual body_lever[3],nav_lever[3],offset[3];for(int i=0;i<3;i++)body_lever[i]=lever[i];
    mv(r,body_lever,nav_lever);rates(model,c,nav_lever,Dual(scalars[2]),offset);
    for(int i=0;i<3;i++){
        Dual value=c[i]+offset[i];observation[i]=value.v;
        if(!std::isfinite(value.v))return 2;
        for(int h=0;h<15;h++)observation_jacobian[15*i+h]=value.d[h];
    }
    for(int i=0;i<15;i++)if(!std::isfinite(state[i]))return 2;
    for(int i=0;i<135;i++)if(!std::isfinite(jacobian[i]))return 2;
    for(int i=0;i<45;i++)if(!std::isfinite(observation_jacobian[i]))return 2;
    return 0;
}
