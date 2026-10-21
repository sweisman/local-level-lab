# Where the available fresh prediction ranges come from

This diagnosis accounts for all 18 fresh endpoints of the three complete groups; the other groups remain incomplete. Every selected certificate is reproduced with exact rational arithmetic. These are fresh ranges, before intersection with the older complete comparison. It runs no optimizer, native trajectory calculation or aircraft fit.

| Candidate / removal | Axis | Mount box (m) | Other physical box (m) | Common-error box (m) | Product box (m) |
|---|---|---:|---:|---:|---:|
| Globe with field / zero | north | 0.0027992 | 0.045407 | 0.012116 | 0.026497 |
| Globe with field / zero | east | 0.0029748 | 0.043467 | 0.010819 | 0.01153 |
| Globe with field / zero | height | 0.035679 | 0.010624 | 0.033069 | 5.3678e-10 |
| Globe with field / profiled | north | 0.0024072 | 0.042221 | 0.013731 | 0.026315 |
| Globe with field / profiled | east | 0.002415 | 0.046735 | 0.01082 | 0.01153 |
| Globe with field / profiled | height | 0.036195 | 0.010531 | 0.032824 | 4.7431e-10 |
| Globe, zero field / zero | north | 0.00045214 | 0.044415 | 0.011489 | 0.021529 |
| Globe, zero field / zero | east | 0.001825 | 0.043198 | 0.010831 | 0.01153 |
| Globe, zero field / zero | height | 0.038651 | 0.010023 | 0.031602 | 8.0065e-08 |

## Training allowances at the difficult endpoints

| Specified-field globe / removal | Axis | Weighted training half-widths (m) | Future remainder allowances (m) |
|---|---|---:|---:|
| Zero | east | 0.8523 | 0.5920 |
| Zero | height | 0.4248 | 0.2579 |
| Profiled | east | 0.8856 | 0.5913 |
| Profiled | height | 0.4448 | 0.2682 |

The training half-width term is the saved dual weight applied to each training interval radius. It includes the method’s nonlinear allowances and declared observation/arithmetic errors. It is not measured aircraft noise. These sizeable contributions support testing tighter propagation allowances on justified smaller domains before adding more mounting-angle cuts. A new bound may change the best certificate, so these numbers are not guaranteed improvements from tightening any one term.

The CSV separates original and recomputed training contributions, including every epoch. These are certificate weights on approximation and observation allowances, not an independent count of calibration errors.

These nonnegative box terms are what remains after applying each saved dual certificate. They are not a decomposition into independent physical errors. The CSV also retains signed constraint terms, endpoint-center separation, remainder allowances and outward rounding. Those terms must all be included to reconstruct a width. A box midpoint can be infeasible, so a constraint contribution may be negative.

Small box terms do not establish accurate calibration: uncertainty may instead enter through the constraints. A large multiplier or contribution is a property of this certificate, not proof of the physically dominant error or of an attainable model fit.

[All endpoint components](endpoint-components.csv) · [Study outcome](INTERPRETATION.md) · [Next step](NEXT_PLAN.md).
