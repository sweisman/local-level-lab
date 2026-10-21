# What makes the saved prediction ranges wide

This audit reads the 32 passing regions only. It exactly reconstructs each saved axis width from its affine support range and twice its unshared error allowance, checking the final outward-rounding padding. No integration, fitting or new support solve runs.

| Candidate / removal | Passing regions | Axis | Median affine width (m) | Median unshared width (m) | Median unshared share |
|---|---:|---|---:|---:|---:|
| Specified-field globe / zero | 8/8 | North | 0.65505 | 0.38019 | 37.1% |
| Specified-field globe / zero | 8/8 | East | 0.901 | 0.5425 | 37.7% |
| Specified-field globe / zero | 8/8 | Height | 0.50632 | 0.25216 | 33.2% |
| Specified-field globe / profiled | 8/8 | North | 0.6796 | 0.39074 | 36.9% |
| Specified-field globe / profiled | 8/8 | East | 0.9254 | 0.54053 | 37.1% |
| Specified-field globe / profiled | 8/8 | Height | 0.52696 | 0.26383 | 33.3% |
| Zero-field globe / zero | 8/8 | North | 0.50259 | 0.30788 | 37.7% |
| Zero-field globe / zero | 8/8 | East | 0.54045 | 0.3207 | 37.6% |
| Zero-field globe / zero | 8/8 | Height | 0.38514 | 0.16843 | 30.3% |
| Zero-field globe / profiled | 2/8 | North | 0.55082 | 0.31608 | 36.1% |
| Zero-field globe / profiled | 2/8 | East | 0.5889 | 0.33702 | 36.0% |
| Zero-field globe / profiled | 2/8 | Height | 0.43277 | 0.19772 | 31.4% |
| Flat disc / zero | 4/8 | North | 0.36656 | 0.25982 | 40.6% |
| Flat disc / zero | 4/8 | East | 0.11622 | 0.078115 | 40.0% |
| Flat disc / zero | 4/8 | Height | 0.28189 | 0.098044 | 25.8% |
| Flat disc / profiled | 2/8 | North | 0.45409 | 0.26945 | 36.6% |
| Flat disc / profiled | 2/8 | East | 0.14889 | 0.087517 | 36.8% |
| Flat disc / profiled | 2/8 | Height | 0.33829 | 0.13437 | 28.4% |

These are **per-region medians**, not a decomposition of the combined union. The affine range includes physical calibration and shared-error uncertainty under training constraints. The unshared allowance bounds the remaining approximation error; it is not observed sensor noise. Nested force, position and lever allowances must not be added as independent contributions.

Missing regions remain missing. The audit cannot qualify an incomplete group, turn numerical allowances into statistical uncertainty or change aircraft findings.

[Study outcome](INTERPRETATION.md) · [Next work](NEXT_PLAN.md).
