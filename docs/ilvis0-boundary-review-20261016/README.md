# Timing-boundary recovery review

**One additional complete comparison favors globe; five of the six reviewed stretches remain unresolved.** The recovered comparison also favors the specified background field under both processing cases. Its cause and a solar-versus-sidereal distinction are not determined.

The numerical check now verifies both sides of a timing boundary with all nuisance directions included. Original measurements, physical bounds, receiver weights and clock remain unchanged. Earlier stopping labels are preserved.

| Stretch | Shape result | Passing primary fits | Passing required repeat pairs |
|---|---|---:|---:|
| `0e73879f98c3b701fd7c42df` | unresolved | 5/6 | 0/2 |
| `370cec66878c4c1cf84b4ceb` | unresolved | 5/6 | 1/2 |
| `50f24131843071ae9312c082` | unresolved | 6/6 | 0/1 |
| `b4e44ddc0f130ecd45674c78` | unresolved | 2/6 | 0/4 |
| `bb8061a43b4f14b6262ceda1` | unresolved | 5/6 | 0/1 |
| `fd7b81e48a4122b149c4925b` | globe | 6/6 | 1/1 |

## Recovered comparison

| Processing case | Globe with field cost | Zero-field globe cost | Flat-disc cost |
|---|---:|---:|---:|
| bias1_profiled_removal | 1.589206 | 1566.079512 | 8469.224293 |
| bias1_unsubtracted | 1.590937 | 1566.154340 | 8469.224293 |

The required repeat agrees in relative cost to about 8.4 × 10⁻¹² and in track RMS to at most 1.1 micrometres per axis. These are numerical repeatability measures, not instrument accuracy.

## Remaining checks

| Endpoint | Outcome |
|---|---|
| `0e73879f98c3b701fd7c42df::bias1_unsubtracted::sphere_still::primary` | side_geometry_unsupported |
| `370cec66878c4c1cf84b4ceb::bias1_profiled_removal::sphere_rotating::primary` | boundary_check_unresolved |
| `370cec66878c4c1cf84b4ceb::bias1_profiled_removal::sphere_rotating::repeat` | interrupted; original allowance reserved |
| `50f24131843071ae9312c082::bias1_unsubtracted::sphere_still::repeat` | no transition in search window; output reporting error |
| `b4e44ddc0f130ecd45674c78::bias1_unsubtracted::sphere_rotating::primary` | boundary_check_unresolved |
| `b4e44ddc0f130ecd45674c78::bias1_unsubtracted::sphere_still::primary` | side_geometry_unsupported |
| `b4e44ddc0f130ecd45674c78::bias1_profiled_removal::sphere_rotating::primary` | boundary_check_unresolved |
| `b4e44ddc0f130ecd45674c78::bias1_profiled_removal::sphere_rotating::repeat` | boundary_check_unresolved |
| `b4e44ddc0f130ecd45674c78::bias1_profiled_removal::sphere_still::primary` | side_geometry_unsupported |
| `bb8061a43b4f14b6262ceda1::bias1_unsubtracted::sphere_still::primary` | boundary_check_unresolved |
| `bb8061a43b4f14b6262ceda1::bias1_unsubtracted::sphere_still::repeat` | boundary_check_unresolved |

The interrupted identity remains unresolved. Its journal is retained unchanged; the continuation ran only previously unstarted identities. The reporting error occurred before any native evaluation and supplies no numerical result.

[Current status](../CURRENT_STATUS.md) · [All stretches](../ilvis0-current-findings-20261015/STRETCHES.md) · [Next steps](../NEXT_STEPS.md). This review reads saved outputs only and performs no new fits or predictions.
