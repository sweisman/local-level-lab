/* SPDX-License-Identifier: AGPL-3.0-or-later
 * Separate candidate. The original source is included without changing it.
 * Modes: 0 baseline, 1 linear partials, 2 coning, 3 sculling, 4 combined.
 */
#define ilvis0_tangent ilvis0_uncompensated_tangent
#include "ilvis0_tangent.cpp"
#undef ilvis0_tangent
#include <vector>

static void calibrated_rates(size_t k,const double *theta,const double *dv,const double *dt,
    const Dual *p,Dual *w,Dual *f) {
    for(int i=0;i<3;i++) {
        w[i]=(theta[3*k+i]/dt[k]-p[9+i])/(1+p[15+i]);
        f[i]=(dv[3*k+i]/dt[k]-p[12+i])/(1+p[18+i]);
    }
}
static void slopes(size_t k,size_t n,const double *theta,const double *dv,const double *dt,
    const std::vector<double>& centers,const Dual *p,Dual *alpha,Dual *beta) {
    size_t first=k==0?0:k==n-1?n-3:k-1;
    double h1=centers[first+1]-centers[first],h2=centers[first+2]-centers[first+1],a,b,c;
    if(k==0) {a=-(2*h1+h2)/(h1*(h1+h2));b=(h1+h2)/(h1*h2);c=-h1/(h2*(h1+h2));}
    else if(k==n-1) {a=h2/(h1*(h1+h2));b=-(h1+h2)/(h1*h2);c=(h1+2*h2)/(h2*(h1+h2));}
    else {a=-h2/(h1*(h1+h2));b=(h2-h1)/(h1*h2);c=h1/(h2*(h1+h2));}
    Dual wa[3],wb[3],wc[3],fa[3],fb[3],fc[3];
    calibrated_rates(first,theta,dv,dt,p,wa,fa);
    calibrated_rates(first+1,theta,dv,dt,p,wb,fb);
    calibrated_rates(first+2,theta,dv,dt,p,wc,fc);
    for(int i=0;i<3;i++) {alpha[i]=a*wa[i]+b*wb[i]+c*wc[i];beta[i]=a*fa[i]+b*fb[i]+c*fc[i];}
}
static void increments(const Dual *w,const Dual *f,const Dual *alpha,const Dual *beta,
    double h,Dual fraction,int mode,Dual *theta,Dual *dv) {
    Dual t=h*fraction,wm[3],fm[3],wa[3],wf[3],wwf[3],wb[3],af[3];
    for(int i=0;i<3;i++) {wm[i]=w[i]+alpha[i]*(t-h)/2;fm[i]=f[i]+beta[i]*(t-h)/2;
        theta[i]=wm[i]*t;dv[i]=fm[i]*t;}
    if(mode==2 || mode==4) {cross(wm,alpha,wa);for(int i=0;i<3;i++)theta[i]+=t*t*t*wa[i]/12;}
    if(mode==3 || mode==4) {
        cross(wm,fm,wf);cross(wm,wf,wwf);cross(wm,beta,wb);cross(alpha,fm,af);
        for(int i=0;i<3;i++)dv[i]+=t*t*t*(wwf[i]/24+(wb[i]-af[i])/12);
    }
}
extern "C" int ilvis0_compensated_tangent(size_t n,const double *theta,const double *dv,const double *dt,
    size_t m,const double *times,const double *initial_c,const double *initial_v,const double *initial_r,
    const double *limits,const double *point,int model,int profile,int mode,double gravity,double radius,
    double *out,double *jacobian,int *boundaries) {
    if(mode==0)return ilvis0_uncompensated_tangent(n,theta,dv,dt,m,times,initial_c,initial_v,
        initial_r,limits,point,model,profile,gravity,radius,out,jacobian,boundaries);
    if(n<3 || mode<1 || mode>4)return 4;
    std::vector<double> centers(n);double elapsed=0;
    for(size_t k=0;k<n;k++) {if(!std::isfinite(dt[k]) || dt[k]<=0)return 4;
        centers[k]=elapsed+dt[k]/2;elapsed+=dt[k];}
    Dual p[27],c[3],v[3],r[9],lever[3],offset[3],rot[9];
    for(int i=0;i<27;i++) {p[i]=point[i]*limits[i];p[i].d[i]=limits[i];}
    if(profile)p[26]=(p[26]+1)/2;else p[26]=0;
    for(int i=0;i<3;i++) {c[i]=initial_c[i];v[i]=initial_v[i]+p[3+i];lever[i]=p[21+i];}
    rates(model,c,p+6,radius,offset);for(int i=0;i<3;i++)c[i]+=offset[i];
    for(int i=0;i<9;i++)r[i]=initial_r[i];exponential(p,rot);mul(r,rot,r);
    double start=0;size_t j=0;*boundaries=0;
    for(size_t k=0;k<n;k++) {
        double end=start+dt[k];Dual w[3],f[3],alpha[3],beta[3],th[3],vel[3];
        calibrated_rates(k,theta,dv,dt,p,w,f);slopes(k,n,theta,dv,dt,centers,p,alpha,beta);
        while(j<m && times[j]+p[25].v<=end) {
            Dual oc[3],ov[3],orr[9],fraction=(times[j]+p[25]-start)/dt[k];
            if(fraction.v < -1e-10 || fraction.v > 1+1e-10)return 3;
            if(fraction.v < 1e-8 || fraction.v > 1-1e-8)(*boundaries)++;
            memcpy(oc,c,sizeof c);memcpy(ov,v,sizeof v);memcpy(orr,r,sizeof r);
            Dual partial_th[3],partial_dv[3],ln[3];
            increments(w,f,alpha,beta,dt[k],fraction,mode,partial_th,partial_dv);
            step(model,oc,ov,orr,partial_th,partial_dv,dt[k]*fraction,gravity+p[24],radius,p[26]);
            mv(orr,lever,ln);rates(model,oc,ln,radius,offset);
            for(int i=0;i<3;i++) {Dual value=oc[i]+offset[i];if(!std::isfinite(value.v))return 2;
                out[3*j+i]=value.v;for(int h=0;h<27;h++)jacobian[(3*j+i)*27+h]=value.d[h];}
            j++;
        }
        if(j==m)return 0;
        if(!std::isfinite(c[0].v+c[1].v+c[2].v) || std::fabs(c[0].v)>=M_PI/2-1e-6)return 2;
        increments(w,f,alpha,beta,dt[k],1.,mode,th,vel);
        step(model,c,v,r,th,vel,dt[k],gravity+p[24],radius,p[26]);start=end;
    }
    return 1;
}
