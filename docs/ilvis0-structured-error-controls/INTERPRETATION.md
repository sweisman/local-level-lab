# Covariance operations at long-record scale

**The structured covariance benchmark passes at 64,080 receiver epochs**, with
27 residual/Jacobian columns. It uses generated software inputs with the same
epoch count as the inspected ESA recording, without reading that recording or
running a physical-model fit.

The declared error model is unchanged: white error, up to two exponential
correlation components, a constant offset and a full-record-normalized drift.
All three-axis covariance and coordinate transforms are retained. The new
implementation carries a small latent error state instead of a whole-record
covariance matrix.

## Verified behavior

Twenty mathematical checks cover irregular timestamps, different coordinate
units, cross-axis correlation, semidefinite latent components, all 27 Jacobian
columns, coordinate-subset marginalization and block continuation. Small dense
references agree at approximately 10⁻¹⁵ for the frozen benchmark; log determinants
agree within 1.5×10⁻¹⁴. Difficult cross-unit tests separately check backward error.

The three frozen software identities all pass. At long-record scale:

| Operation or storage | Measured result |
|---|---:|
| Filter setup | 8.59 s |
| Whole-record whitening, 27 columns | 2.17 s |
| Block whitening plus inverse | 2.98 s |
| Filter cache | 23.96 MiB |
| Generated input and whitened matrices together | 79.20 MiB |
| Whole-process peak resident memory | 177.16 MiB |
| Block versus whole whitening discrepancy | Zero in this benchmark |
| Largest inverse reconstruction error | 6.7×10⁻¹⁶ |

Cache storage is 392 bytes per epoch in both tested sizes. One dense covariance
alone at the large size would need about 275 GiB, before its factor and working
storage. The structured implementation constructs none of those large matrices.

## Continuity and interpretation

Each block carries its state forward explicitly. A missing state, different
covariance/axis configuration, changed column count, reordered block or switch
between whitening and inverse is rejected. No jitter, eigenvalue clipping or
dropped nuisance column supplies a hidden numerical fix. Coordinate-subset
projection also uses structured operators rather than a dense projection matrix.

This qualifies operations for a **supplied covariance**. It does not estimate
that covariance, establish its physical adequacy, include bounded nonlinear
calibration uncertainty or calibrate a scientific decision. Native trajectory
integration must still preserve its own state across blocks. No ESA protected
outcomes, archive fits or main findings changed.

The next uncertainty work must retain one shared error specification for all
physical candidates and account for uncertainty in its estimation. Fitting a
different error scale to rescue each candidate would change the comparison.

[Benchmark results](README.md) · [Method](PLAN.md) ·
[Finite limits](BENCHMARK_PLAN.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
