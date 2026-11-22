# Test a different search direction when curvature steps stall

The trial-tangent solver matched its references on the generated specified-field
globe and disc. On the zero-field globe, nine consecutive trials raised the
training cost and the estimate failed the fresh stopping check.
[Previous results](TANGENT_SECANT_GEOMETRY_RESULT.md)

Test one solver change. When the curvature search at the current point runs
out of viable steps, form a bounded Gauss–Newton direction from the tangent
already evaluated there. Try it once with the existing backtracking schedule.
Every trial must still lower the evaluated cost and meet the existing agreement
rule. Keep the fresh end-of-fit check and its reserved evaluations. Test the
fallback on a controlled failure before running any generated flight cases.

Use the same three 24-second generated flights, along with the archived
reference forecasts. Run one new start per geometry with three single-thread
workers, at most 200 training evaluations per fit and a 210-second cooperative
wall limit. Keep the same inputs, physical tolerances, finite technical recovery
rule and split of 15 training and eight withheld receiver reports. Preserve all
fits from the previous studies. No aircraft or reserved flight data enter
the study.

All three pairs must satisfy the original numerical and physical gates, a
training-cost gap no greater than 0.01 and a maximum withheld position
difference no greater than 0.10 m. Require use of secant updates, zero separate
derivative probes and at least one accepted fallback on the zero-field globe.
A pass qualifies these short controls. Longer controls and aircraft data have
separate qualification requirements.
