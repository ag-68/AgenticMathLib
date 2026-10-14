"""JSON arrays in, NumPy arrays inside, JSON arrays out.

Real data is a list. Complex data is {"re": ..., "im": ...} with the same shape.
At most 4096 elements are accepted. Larger arrays are rejected.
"""

import numpy as np

from mathlib_mcp.errors import ToolError

MAX_ELEMENTS = 4096


def parse_array(value: object, *, ndim: int, complex_ok: bool = True) -> np.ndarray:
    if isinstance(value, dict):
        if not complex_ok:
            raise ToolError(
                "expected_real",
                "This tool accepts a real list, not a complex object.",
                "Pass a list of real numbers.",
            )
        if set(value) != {"re", "im"}:
            raise ToolError(
                "invalid_array",
                "A complex array must contain only re and im.",
                'Use {"re": [...], "im": [...]} with the same shape.',
            )
        real = np.asarray(value["re"], dtype=float)
        imag = np.asarray(value["im"], dtype=float)
        if real.shape != imag.shape:
            raise ToolError(
                "shape_mismatch",
                f"re shape {list(real.shape)} does not match im shape {list(imag.shape)}.",
                "Give re and im the same length and the same nesting.",
            )
        array = real + 1j * imag
    elif isinstance(value, list):
        array = np.asarray(value, dtype=float)
    else:
        raise ToolError(
            "invalid_array",
            "The value is not a list or a complex object.",
            'Pass a list of numbers, or {"re": [...], "im": [...]}.',
        )
    if array.dtype == object:
        raise ToolError(
            "invalid_array",
            "The array is ragged or contains non-numbers.",
            "Use a rectangular list of numbers.",
        )
    if array.ndim != ndim:
        raise ToolError(
            "bad_rank",
            f"Expected {ndim} dimensions, got {array.ndim}.",
            "Use a flat list for a vector and a list of lists for a matrix.",
        )
    if array.size == 0:
        raise ToolError(
            "empty_array",
            "The array has no elements.",
            "Pass at least one number.",
        )
    if int(array.size) > MAX_ELEMENTS:
        raise ToolError(
            "too_large",
            f"The array has {array.size} elements. The limit is {MAX_ELEMENTS}.",
            f"Send at most {MAX_ELEMENTS} elements.",
        )
    return array


def pack(array: np.ndarray) -> dict[str, object]:
    if np.iscomplexobj(array):
        data: dict[str, object] = {
            "re": np.real(array).tolist(),
            "im": np.imag(array).tolist(),
        }
        dtype = "complex128"
    else:
        data = {"values": np.asarray(array, dtype=float).tolist()}
        dtype = "float64"
    return {"shape": list(array.shape), "dtype": dtype, **data}
