# Where the saved ranges come from

This diagnosis accounts for all 36 endpoints of the six complete prediction ranges. Every saved certificate is reproduced with exact rational arithmetic. It runs no optimizer, native trajectory calculation or aircraft fit.

| Candidate / removal | Axis | Mount box (m) | Other physical box (m) | Common-error box (m) | Product box (m) |
|---|---|---:|---:|---:|---:|
| Globe with field / zero | north | 0.00068056 | 0.03931 | 0.013066 | 0.0019428 |
| Globe with field / zero | east | 0.0015466 | 0.042528 | 0.010422 | 0.002253 |
| Globe with field / zero | height | 0.020216 | 0.010408 | 0.029517 | 1.1823e-20 |
| Globe with field / profiled | north | 0.00060825 | 0.039327 | 0.012689 | 0.0019451 |
| Globe with field / profiled | east | 0.0012826 | 0.045787 | 0.010423 | 0.0022533 |
| Globe with field / profiled | height | 0.020181 | 0.01034 | 0.029586 | 3.2589e-20 |
| Globe, zero field / zero | north | 0.00019228 | 0.045143 | 0.024947 | 0.00040291 |
| Globe, zero field / zero | east | 0.00082784 | 0.042209 | 0.01043 | 0.0022516 |
| Globe, zero field / zero | height | 0.019219 | 0.010689 | 0.027098 | 1.5357e-10 |
| Globe, zero field / profiled | north | 7.2833e-05 | 0.045224 | 0.02494 | 0.00040334 |
| Globe, zero field / profiled | east | 0.00082266 | 0.045656 | 0.010426 | 0.0022518 |
| Globe, zero field / profiled | height | 0.019966 | 0.010279 | 0.030012 | 1.3155e-10 |
| Flat disc / zero | north | 2.9435e-05 | 0.03695 | 0.021307 | 0.0068933 |
| Flat disc / zero | east | 4.7531e-05 | 0.011821 | 0.005669 | 0.0020067 |
| Flat disc / zero | height | 0.016522 | 0.010695 | 0.037547 | 0 |
| Flat disc / profiled | north | 0.00016308 | 0.038889 | 0.024688 | 0.00021265 |
| Flat disc / profiled | east | 9.2129e-05 | 0.012043 | 0.0036626 | 0.0010398 |
| Flat disc / profiled | height | 0.016516 | 0.010688 | 0.03753 | 1.2304e-05 |

## Training allowances at the difficult endpoints

| Specified-field globe / removal | Axis | Weighted training half-widths (m) | Future remainder allowances (m) |
|---|---|---:|---:|
| Zero | east | 0.8730 | 0.4719 |
| Zero | height | 0.5917 | 0.3470 |
| Profiled | east | 0.9134 | 0.5042 |
| Profiled | height | 0.6402 | 0.3856 |

The training half-width term is the saved dual weight applied to each training interval radius. It includes the method’s nonlinear allowances and declared observation/arithmetic errors. It is not measured aircraft noise. These sizeable contributions support testing tighter propagation allowances on justified smaller domains before adding more mounting-angle cuts. A new bound may change the best certificate, so these numbers are not guaranteed improvements from tightening any one term.

These nonnegative box terms are what remains after applying each saved dual certificate. They are not a decomposition into independent physical errors. The CSV also retains signed constraint terms, endpoint-center separation, remainder allowances and outward rounding. Those terms must all be included to reconstruct a width. A box midpoint can be infeasible, so a constraint contribution may be negative.

Small box terms do not establish accurate calibration: uncertainty may instead enter through the constraints. A large multiplier or contribution is a property of this certificate, not proof of the physically dominant error or of an attainable model fit.

[All endpoint components](endpoint-components.csv) · [Result](INTERPRETATION.md) · [Next step](NEXT_PLAN.md).
