# Accounting audit of the partial timing diagnostic

**Eight saved checks verify intact: both controls, four passing endpoints and two unresolved endpoints.** A ninth identity was interrupted; twelve never started. No original journal or saved result was changed.

The journal contains 162 valid call charges and an incomplete 163rd entry. All nine started identities keep their complete allowance reserved. A separate continuation may use only the twelve unstarted identities, at 26 calls each (312 maximum); the original combined ceiling remains 546.

| Endpoint | Diagnostic passed | Outcome |
|---|---|---|
| `0e73879f98c3b701fd7c42df::bias1_profiled_removal::sphere_still::primary` | True | two_sided_boundary_stability |
| `0e73879f98c3b701fd7c42df::bias1_profiled_removal::sphere_still::repeat` | True | two_sided_boundary_stability |
| `0e73879f98c3b701fd7c42df::bias1_unsubtracted::sphere_still::primary` | False | side_geometry_unsupported |
| `233183f67270980491416678::bias1_unsubtracted::sphere_rotating::control` | True | fresh_position_stability_verified |
| `31d7e5019dfdc9e2e6387206::bias1_profiled_removal::sphere_rotating::control` | True | fresh_position_stability_verified |
| `370cec66878c4c1cf84b4ceb::bias1_profiled_removal::sphere_rotating::primary` | False | boundary_check_unresolved |
| `370cec66878c4c1cf84b4ceb::bias1_unsubtracted::sphere_rotating::primary` | True | two_sided_boundary_stability |
| `370cec66878c4c1cf84b4ceb::bias1_unsubtracted::sphere_rotating::repeat` | True | two_sided_boundary_stability |

The two unresolved endpoints respectively lack supported side geometry and fail right-side stationarity. Passing local checks cannot replace complete model/case and repeat comparisons. Findings remain 47 globe / zero flat / six unresolved.

Fault injection reproduces the incomplete-append failure mode. The trigger for the observed truncation is not recoverable from the saved traceback; the original exception was masked by another accounting read. A new receipt ledger is software-qualified separately, leaving the stopped study unchanged.
