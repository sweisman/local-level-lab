# Linear accumulated inertial error

Write position, velocity and small orientation error as \(p,v,\theta\).
The supplied constant matrix \(G\) maps orientation error to acceleration.
The declared continuous-time model is

\[
\dot p=v,\qquad \dot v=G\theta+n_a,\qquad \dot\theta=n_g.
\]

The independent zero-mean white drives have spectral matrices \(Q_a\) and
\(Q_g\), in \(\mathrm{m^2/s^3}\) and \(\mathrm{rad^2/s}\). These matrices
are supplied assumptions, not estimates or device specifications. The
stochastic state is zero at the declared origin; uncertain constant initial
conditions and calibration remain in the separate shared-parameter treatment.

For elapsed time \(t\), the transition is

\[
F(t)=\begin{pmatrix}I&tI&t^2G/2\\0&I&tG\\0&0&I\end{pmatrix}.
\]

Let \(H=GQ_gG^T\). The integrated process covariance is

\[
Q(t)=\begin{pmatrix}
t^3Q_a/3+t^5H/20&t^2Q_a/2+t^4H/8&t^3GQ_g/6\\
t^2Q_a/2+t^4H/8&tQ_a+t^3H/3&t^2GQ_g/2\\
t^3Q_gG^T/6&t^2Q_gG^T/2&tQ_g
\end{pmatrix}.
\]

This follows by integrating \(F(u)\operatorname{diag}(0,Q_a,Q_g)F(u)^T\).
The software tests calculate that integral separately with matrix exponentials
and numerical quadrature. They also check the composition identity
\(Q(a+b)=F(b)Q(a)F(b)^T+Q(b)\).

For \(t_i\leq t_j\), the cross-covariance is the position block of
\(Q(t_i-t_0)F(t_j-t_i)^T\), where \(t_0\) is the fixed origin. Never
reset \(t_0\) when extracting a training or prediction subset. Add receiver
covariance before conditioning; retain its cross-boundary terms too. Coordinate
transforms act on the complete summed covariance.

The implementation is a small-problem reference capped at 512 epochs. It adds
no jitter or eigenvalue clipping. This exact linear-system calculation does not
establish exact nonlinear inertial uncertainty, the correct noise law for a
recording, a whole-program floating-point enclosure or aircraft coverage.

[Checks and interpretation](INTERPRETATION.md) · [Scope](PLAN.md).
