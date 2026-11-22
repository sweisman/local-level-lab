# Why the longer-flight rule found few candidates

All 232 strict file scans completed. Five files yielded a candidate; 227 did not. The following are saved screening tallies, not independent flight counts or unique explanations. A sample can trigger several flags.

| Flag | Tally | Files with flag |
|---|---:|---:|
| `incomplete_alignment` | 3,088,600 | 153 |
| `excessive_course_rate` | 1,481,410 | 232 |
| `below_ground_speed` | 414,760 | 25 |
| `short_after_buffers_or_raw_intersection` | 6,431 | 94 |
| `below_sampled_receiver_distance` | 0 | 0 |

Alignment, speed and course-rate flags count screened motion samples. Short-after-buffer and distance flags count candidate spans. Their tallies have different units and cannot be added. The [complete rejection table](rejection-counts.csv) preserves every recorded flag.

The large alignment tally is a warning about depending on the instrument’s fused navigation status for screening. It does not prove that otherwise excluded raw IMU and receiver data can distinguish Earth models. A separately fixed receiver-only candidate inventory would be required to test that question. The original 53-stretch study remains unchanged.
