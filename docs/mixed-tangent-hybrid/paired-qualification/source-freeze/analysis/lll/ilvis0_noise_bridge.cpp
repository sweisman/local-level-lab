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
