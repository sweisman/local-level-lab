# Connect bounded uncertainty to native forecasts

The [bounded state-space adapter](bounded-state-qualification/README.md) has
passed 58 software checks. The next connection must preserve the existing
native forecast, its before-cast earlier residuals, fitted-point identity and
every calibration column.

Use a separate diagnostic provider; keep the current provider and historical
results unchanged. Extend the fixed earlier error law once, then reuse that
same operator for the original diagnostic and the bounded envelope. Coefficient
bounds are the complete normalized calibration box translated relative to the
saved fitted point. Do not clip unknown directions or give boundary parameters
zero uncertainty.

The caller must supply a scale assumption and training/future approximation-error
allowances. Missing allowances remain unsupported. Zero allowances check only
the local linear mathematical problem; they cannot certify the nonlinear native
map. No failed numerical fit becomes qualified through this diagnostic.

First run at most 20 deterministic interface checks plus affected regressions,
one numerical thread, zero native calls/builds and zero optimizer starts. Test
exact-bound points, missing allowances, corrupted fitted-point/configuration
bindings, earlier-residual sign and full column order. The provider must perform
one operator extension and accept no later receiver observations.

Only after that interface gate passes, freeze separate short native controls
covering both recorded-increment and sampled-rate error laws, all three
candidates and both processing assumptions. Their exact sources, construction,
native-operation and compiler allowances must be recorded before execution.
They may evaluate supplied calibration points, not refit completed studies.

No observed or protected recordings enter this gate. Nonlinear remainder and
coverage qualification remain required before further aircraft fitting.
