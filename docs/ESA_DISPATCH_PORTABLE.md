# Portable evidence for the ESA method comparison

The [sealed runtime study](esa-observed-model-dispatch-runtime/README.md)
contains 576 artifacts: frozen inputs and source, task charges, fits and
forecasts. The [portable index](esa-observed-model-dispatch-runtime/portable-evidence/index.json)
and its nine adjacent ZIP parts copy all of them, including a large artifact
split across parts. Every part is below 32 MiB. Verify the parts and reconstruct
each artifact's original SHA-256 against the publication receipt with:

`~/venv/bin/python -m lll.studies.portable verify-parts docs/esa-observed-model-dispatch-runtime/portable-evidence`

To inspect the restored files without changing the checkout, extract them to
an empty directory, for example:

`~/venv/bin/python -m lll.studies.portable extract-parts docs/esa-observed-model-dispatch-runtime/portable-evidence /tmp/esa-dispatch-evidence`

This export is a copy of a completed software-method study. The faster method
still fails its frozen observed-data qualification rule; the scientific decision
remains abstain.
