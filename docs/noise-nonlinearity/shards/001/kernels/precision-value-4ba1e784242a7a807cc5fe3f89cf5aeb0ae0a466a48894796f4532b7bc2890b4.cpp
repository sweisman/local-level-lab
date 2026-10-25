// Derived scalar diagnostics; mechanization comes from the bound tangent source.
#include <cmath>
#include <cstddef>
#include <cstring>
#include <limits>
using Real=long double;
struct Dual {
    Real v;
    Dual(Real value=0):v(value) {}
    Dual& operator+=(const Dual& b) {v+=b.v;return *this;}
};
static Dual operator+(const Dual&a,const Dual&b){return a.v+b.v;}
static Dual operator-(const Dual&a,const Dual&b){return a.v-b.v;}
static Dual operator-(const Dual&a){return -a.v;}
static Dual operator*(const Dual&a,const Dual&b){return a.v*b.v;}
static Dual operator/(const Dual&a,const Dual&b){return a.v/b.v;}
static Dual sin(const Dual&a){return std::sin(a.v);}
static Dual cos(const Dual&a){return std::cos(a.v);}
static Dual sqrt(const Dual&a){return std::sqrt(a.v);}
static Dual pow(const Dual&a,double b){return std::pow(a.v,Real(b));}
static bool operator<(const Dual&a,double b){return a.v<b;}
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
static int precision_value(size_t n,const double *theta,const double *dv,const double *dt,
    size_t m,const double *times,const double *initial_c,const double *initial_v,
    const double *initial_r,const double *limits,const double *point,int model,int profile,
    double gravity,double radius,double *out,const double *observations,double *difference,int *boundaries,
    int height_gravity,double anchor_height) {
    if(height_gravity && (!std::isfinite(anchor_height) || anchor_height<=-6371000.))return 4;
    Dual p[27],c[3],v[3],r[9],lever[3],offset[3],rot[9];
    for(int i=0;i<27;i++) {p[i]=point[i]*limits[i];}
    if(profile) {p[26]=(static_cast<double>(p[26].v)+1)/2;} else {p[26]=0;}
    for(int i=0;i<3;i++) {c[i]=initial_c[i];v[i]=initial_v[i]+p[3+i];lever[i]=p[21+i];}
    rates(model,c,p+6,radius,offset);for(int i=0;i<3;i++)c[i]+=offset[i];
    for(int i=0;i<9;i++)r[i]=initial_r[i];
    exponential(p,rot);mul(r,rot,r);
    double start=0;size_t j=0;*boundaries=0;
    for(size_t k=0;k<n;k++) {
        double end=start+dt[k];Dual th[3],vel[3];
        for(int i=0;i<3;i++) {
            th[i]=(theta[3*k+i]-p[9+i]*dt[k])/(1+p[15+i]);
            vel[i]=(dv[3*k+i]-p[12+i]*dt[k])/(1+p[18+i]);
        }
        while(j<m && times[j]+static_cast<double>(p[25].v)<=end) {
            Dual oc[3],ov[3],orr[9],fraction=(times[j]+static_cast<double>(p[25].v)-start)/dt[k];
            if(fraction.v < -1e-10 || fraction.v > 1+1e-10)return 3;
            if(fraction.v < 1e-8 || fraction.v > 1-1e-8)(*boundaries)++;
            memcpy(oc,c,sizeof c);memcpy(ov,v,sizeof v);memcpy(orr,r,sizeof r);
            Dual partial_th[3],partial_dv[3],ln[3];
            for(int i=0;i<3;i++) {partial_th[i]=th[i]*fraction;partial_dv[i]=vel[i]*fraction;}
            step_gravity(model,oc,ov,orr,partial_th,partial_dv,dt[k]*fraction,gravity+p[24],radius,p[26],height_gravity,anchor_height);
            mv(orr,lever,ln);rates(model,oc,ln,radius,offset);
            for(int i=0;i<3;i++) {
                Dual value=oc[i]+offset[i];
                if(!std::isfinite(value.v))return 2;
                out[3*j+i]=value.v;
                difference[3*j+i]=static_cast<double>(value.v-Real(observations[3*j+i]));
            }
            j++;
        }
        if(j==m)return 0;
        if(!std::isfinite(c[0].v+c[1].v+c[2].v) || std::fabs(c[0].v)>=M_PI/2-1e-6)return 2;
        step_gravity(model,c,v,r,th,vel,dt[k],gravity+p[24],radius,p[26],height_gravity,anchor_height);start=end;
    }
    return 1;
}

extern "C" int ilvis0_precision_value(size_t n,const double *theta,const double *dv,const double *dt,
    size_t m,const double *times,const double *initial_c,const double *initial_v,
    const double *initial_r,const double *limits,const double *point,int model,int profile,
    double gravity,double radius,double *out,const double *observations,double *difference,
    int *boundaries,int height_gravity,double anchor_height) {
    return precision_value(n,theta,dv,dt,m,times,initial_c,initial_v,initial_r,limits,point,
        model,profile,gravity,radius,out,observations,difference,boundaries,height_gravity,anchor_height);
}
extern "C" int ilvis0_precision_bits(){return std::numeric_limits<Real>::digits;}
