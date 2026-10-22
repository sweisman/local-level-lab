/* SPDX-License-Identifier: AGPL-3.0-or-later
 * Third-order interval midpoint step, separate from the native fit engine.
 * Stable rotation branches only. This is not native execution-error coverage.
 */
#include "ilvis0_path_arithmetic.cpp"

namespace path_arithmetic {
Jet constant(double x){return {{{{x,x},{0,0},{0,0},{0,0}}}};}
Jet operator+(Jet a,Jet b){return add(a,b);}
Jet operator-(Jet a){for(auto &x:a.d)x=neg(x);return a;}
Jet operator-(Jet a,Jet b){return a+-b;}
Jet operator*(Jet a,Jet b){return mul(a,b);}
Jet operator/(Jet a,Jet b){return mul(a,inverse(b));}
Jet operator*(double a,Jet b){return constant(a)*b;}
Jet operator/(Jet a,double b){return a/constant(b);}
Jet sqr(Jet a){Jet r=a*a;r.d[0]=square(a.d[0]);return r;}
using Vector=std::array<Jet,3>;
using Matrix=std::array<std::array<Jet,3>,3>;
struct State{Vector coordinates,velocity;Matrix attitude;};
Matrix mm(Matrix a,Matrix b){
    Matrix r;for(int i=0;i<3;i++)for(int j=0;j<3;j++){
        r[i][j]=constant(0);for(int k=0;k<3;k++)r[i][j]=r[i][j]+a[i][k]*b[k][j];
    }return r;
}
Vector mv(Matrix a,Vector b){
    Vector r;for(int i=0;i<3;i++){
        r[i]=constant(0);for(int k=0;k<3;k++)r[i]=r[i]+a[i][k]*b[k];
    }return r;
}
Vector cross(Vector a,Vector b){return {a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]};}
Matrix rotation(Vector v){
    Jet q=sqr(v[0])+sqr(v[1])+sqr(v[2]),a,b;
    if(q.d[0].hi<1e-4){
        Jet q2=sqr(q),q3=q2*q;
        a=constant(1)-q/6+q2/120-q3/5040;
        b=constant(.5)-q/24+q2/720-q3/40320;
    }else if(q.d[0].lo>=1e-4){
        Jet length=root(q);a=trig(length,false)/length;b=(constant(1)-trig(length,true))/q;
    }else throw Unsupported{2};
    Jet z=constant(0);Matrix k={{{z,-v[2],v[1]},{v[2],z,-v[0]},{-v[1],v[0],z}}};
    Matrix kk=mm(k,k),out;for(int i=0;i<3;i++)for(int j=0;j<3;j++)
        out[i][j]=constant(i==j)+a*k[i][j]+b*kk[i][j];
    return out;
}
void latitude_domain(int model,Jet phi){
    if(model<0||model>2||phi.d[0].lo< -1.57||phi.d[0].hi>1.57)throw Unsupported{2};
}
std::array<Jet,2> metric(int model,Jet phi,Jet height,Jet radius){
    latitude_domain(model,phi);if(radius.d[0].lo<=0)throw Unsupported{2};
    Jet north,east;
    if(model==2){north=radius;east=radius*(constant(0x1.921fb54442d18p+0)-phi);}
    else{
        Jet sine=trig(phi,false),cosine=trig(phi,true),e2=constant(6.69437999014e-3);
        Jet d=constant(1)-e2*sqr(sine),r=root(d);
        north=6378137*(constant(1)-e2)/(d*r)+height;
        east=(constant(6378137)/r+height)*cosine;
    }
    if(north.d[0].lo<=0||east.d[0].lo<=0)throw Unsupported{2};
    return {north,east};
}
Vector rates(int model,Vector position,Vector velocity,Jet radius){
    auto m=metric(model,position[0],position[2],radius);
    return {velocity[0]/m[0],velocity[1]/m[1],-velocity[2]};
}
std::array<Vector,2> context(int model,Jet phi,Vector rate){
    latitude_domain(model,phi);Jet s=trig(phi,false),c=trig(phi,true),z=constant(0);
    Vector earth=model==0?Vector{7.2921150e-5*c,z,-(7.2921150e-5*s)}:Vector{z,z,z};
    Vector transport=model==2?Vector{z,z,-rate[1]}:Vector{c*rate[1],-rate[0],-s*rate[1]};
    return {earth,transport};
}
struct Local{Matrix attitude;Vector velocity;};
Local local(State state,Vector theta,Vector dv,Jet period,Vector earth,Vector transport,Jet phi,Jet removal,Jet gravity){
    Jet zero=constant(0);Vector standard=context(0,phi,{zero,zero,zero})[0],win,argument,leftarg,rightarg;
    for(int i=0;i<3;i++){
        win[i]=earth[i]+transport[i]-removal*standard[i];
        argument[i]=(2*earth[i]+transport[i])*period/2;
        leftarg[i]=-win[i]*period/2;rightarg[i]=theta[i]/2;
    }
    Matrix middle=mm(mm(rotation(leftarg),state.attitude),rotation(rightarg));
    Vector force=mv(middle,dv);
    for(int i=0;i<3;i++)leftarg[i]=-win[i]*period;
    Matrix attitude=mm(mm(rotation(leftarg),state.attitude),rotation(theta));
    Vector av=cross(argument,state.velocity),rhs;
    for(int i=0;i<3;i++)rhs[i]=state.velocity[i]-av[i]+force[i]+(i==2?gravity*period:zero);
    Vector ar=cross(argument,rhs),velocity;Jet dot=zero,den=constant(1);
    for(int i=0;i<3;i++){dot=dot+argument[i]*rhs[i];den=den+sqr(argument[i]);}
    for(int i=0;i<3;i++)velocity[i]=(rhs[i]-ar[i]+argument[i]*dot)/den;
    return {attitude,velocity};
}
State step(int model,State state,Vector theta,Vector dv,Jet period,Jet gravity,Jet radius,Jet removal){
    if(period.d[0].lo<0||gravity.d[0].lo<=0||removal.d[0].lo<0||removal.d[0].hi>1)throw Unsupported{2};
    Vector rate=rates(model,state.coordinates,state.velocity,radius),middle;
    for(int i=0;i<3;i++)middle[i]=state.coordinates[i]+rate[i]*period/2;
    auto first=context(model,middle[0],rate);
    Vector estimate=local(state,theta,dv,period,first[0],first[1],middle[0],removal,gravity).velocity,average;
    for(int i=0;i<3;i++)average[i]=(state.velocity[i]+estimate[i])/2;
    Vector revised=rates(model,middle,average,radius);auto second=context(model,middle[0],revised);
    Local final=local(state,theta,dv,period,second[0],second[1],middle[0],removal,gravity);
    for(int i=0;i<3;i++)state.coordinates[i]=state.coordinates[i]+revised[i]*period;
    state.attitude=final.attitude;state.velocity=final.velocity;return state;
}
void write(Jet a,double *out){
    for(int n=0;n<4;n++){
        if(!std::isfinite(a.d[n].lo)||!std::isfinite(a.d[n].hi)||a.d[n].lo>a.d[n].hi)throw Unsupported{3};
        out[2*n]=a.d[n].lo;out[2*n+1]=a.d[n].hi;
    }
}
State read_state(const double *a){
    State s;for(int i=0;i<3;i++){s.coordinates[i]=read(a+8*i);s.velocity[i]=read(a+8*(i+3));}
    for(int i=0;i<3;i++)for(int j=0;j<3;j++)s.attitude[i][j]=read(a+8*(6+3*i+j));
    return s;
}
void write_state(State s,double *out){
    for(int i=0;i<3;i++){write(s.coordinates[i],out+8*i);write(s.velocity[i],out+8*(i+3));}
    for(int i=0;i<3;i++)for(int j=0;j<3;j++)write(s.attitude[i][j],out+8*(6+3*i+j));
}
}

extern "C" int ilvis0_path_step(int model,const double *state,const double *input,double *out){
    try{
        if(!runtime_ok())return 1;using namespace path_arithmetic;
        Vector theta,dv;for(int i=0;i<3;i++){theta[i]=read(input+8*i);dv[i]=read(input+8*(i+3));}
        State answer=step(model,read_state(state),theta,dv,read(input+48),read(input+56),read(input+64),read(input+72));
        write_state(answer,out);return 0;
    }catch(Unsupported e){return e.code;}
}
extern "C" int ilvis0_path_rotation(const double *input,double *out){
    try{
        if(!runtime_ok())return 1;using namespace path_arithmetic;
        Matrix answer=rotation({read(input),read(input+8),read(input+16)});
        for(int i=0;i<3;i++)for(int j=0;j<3;j++)write(answer[i][j],out+8*(3*i+j));return 0;
    }catch(Unsupported e){return e.code;}
}
