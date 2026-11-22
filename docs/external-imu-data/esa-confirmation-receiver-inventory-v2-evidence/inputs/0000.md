# Screen the reserved ESA flight groups using receiver data

The published reservation permits receiver-only eligibility checks on seven
protected groups. Screen the primary AIR1 receiver position exports in the
saved archive listing. Keep both files for the split 178 recording in one
group. Do not read inertial observations, use fused attitude or fit a model.

| Receiver export | Archived byte size |
| --- | ---: |
| `178a_air1_ppp_2Hz_final.txt` | 9,017,739 |
| `178b_air1_ppp_2Hz_final.txt` | 5,751,474 |
| `179_air1_ppp_2Hz_final.txt` | 18,638,557 |
| `180_air1_ppp_2Hz_final.txt` | 15,811,636 |
| `182_air1_ppp_2Hz_final.txt` | 28,871,950 |
| `183_air1_ppp_2Hz_final.txt` | 15,131,602 |
| `184_air1_ppp_2Hz_final.txt` | 14,129,857 |
| `186_air1_ppp_2Hz_final.txt` | 14,682,088 |

The acquisition uses the configured authenticated ESA FTPS connection with
certificate verification. Download only these eight named files, keep
partial downloads for restart, and verify exact size and record SHA-256
before moving any file into the completed inventory.

Use the receiver part of the frozen [full-motion policy](ESA_SELECTION_V2.md).
Keep its gap, quality, covariance, speed, duration and distance rules. Report
provisional windows and exclusions by group. No window can pass the complete
eligibility gate in this check because independent IMU support and the
complete frozen confirmation protocol are separate requirements. Retain a
record for each declared file even if it cannot be screened.

Use one numerical thread and one task per file. Allow at most 100,001
charged receiver decoder calls and one selection per file. Use the checked
task-level technical recovery before launch. Publish only the provenance,
receiver-derived summaries and verification reports. Keep the original
receiver files available through their acquired hashes.
