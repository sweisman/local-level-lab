# Linked calibration bound accounting correction

The [first frozen run](ESA_LINKED_FLOOR_SUPPORT_PLAN.md) ended after one
recorded skip and ten technical failures. The launcher rejected a subdivision
derivative reservation made without a bound-operation count. Its 20 charged
operations and all outcomes are retained. No range completed a floor test.

Run a separate, identical calculation with the derivative reserved together
with the whole-box bound. Count three steps for that operation, including
one step reserved for a derivative that may be unused. Retain both score
floors, all boxes, the original 0.01 earlier loss increase and every input
hash. The two one-thread workers have a fresh 180-second cooperative limit,
with the same 132 operation and 264 step caps. Check an actual subdivision
path under the runner's complete-operation accounting convention.
