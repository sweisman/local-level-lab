# Compact inputs reproduce all six calibration references

All six full static references match their saved originals exactly, including source bindings, coefficients and normalization caps. The worker needs only the verified configuration, first velocity increment and first sample interval.

The six compact bundles total 249,591 bytes. No packet history was copied into them or loaded by the worker. Reconstructing the references took 1.61 seconds on one numerical thread, with six charged reconstructions and no retries.

This establishes input compatibility for the next static coupling diagnostic. It does not qualify trajectory prediction ranges, aircraft error assumptions or a scientific detection. No aircraft measurements, integration or model fits were used.

[Method and limits](PLAN.md) · [Next diagnostic](../ilvis0-calibration-box-audit-v2/NEXT_PLAN.md) · [Shared reference reconstruction](../../analysis/lll/ilvis0_coupled_map.py) · [Reproduce the evidence](../REPRODUCIBILITY.md).
