"""Five numerical tools. The math is SciPy. The wrappers exist so an agent can call them safely."""

from typing import Any

import numpy as np
import scipy.fft
import scipy.linalg
import scipy.signal

from mathlib_mcp.arrays import pack, parse_array
from mathlib_mcp.errors import ToolError

_FFT_NORMS = {"backward", "forward", "ortho"}
_DIRECTIONS = {"forward", "inverse"}
_MODES = {"full", "same", "valid"}


def fft(x: Any, direction: str = "forward", norm: str = "backward") -> dict[str, Any]:
    """1-D discrete Fourier transform.

    direction is "forward" or "inverse". norm is "backward" (default, NumPy's usual
    scaling), "forward", or "ortho". Complex input is {"re": [...], "im": [...]}.
    Output is complex, same length as the input. Prefer power_spectrum for the
    one-sided power of a real signal. Prefer the inverse direction to undo a forward
    transform that used the same norm.
    """
    if direction not in _DIRECTIONS:
        raise ToolError(
            "bad_direction",
            f"direction must be one of {sorted(_DIRECTIONS)}.",
            "Use direction 'forward' or 'inverse'.",
        )
    if norm not in _FFT_NORMS:
        raise ToolError(
            "bad_norm",
            f"norm must be one of {sorted(_FFT_NORMS)}.",
            "Use norm 'backward', 'forward', or 'ortho'.",
        )
    samples = parse_array(x, ndim=1)
    transform = scipy.fft.fft if direction == "forward" else scipy.fft.ifft
    return pack(transform(samples, norm=norm))


def power_spectrum(samples: Any, sample_rate_hz: float) -> dict[str, Any]:
    """One-sided power spectrum of a real signal.

    sample_rate_hz is in hertz and must be positive. frequencies_hz come from
    rfftfreq. power is abs(rfft)^2 / n, not a power spectral density. For a
    complex series, or for a transform you will invert, use fft instead.
    """
    if sample_rate_hz <= 0:
        raise ToolError(
            "bad_sample_rate",
            "sample_rate_hz must be a positive number of hertz.",
            "Pass the sample rate in Hz, for example 1000.",
        )
    signal = parse_array(samples, ndim=1, complex_ok=False)
    spectrum = scipy.fft.rfft(signal)
    power = (np.abs(spectrum) ** 2) / signal.size
    frequencies = scipy.fft.rfftfreq(signal.size, d=1.0 / float(sample_rate_hz))
    return {
        "frequencies_hz": frequencies.tolist(),
        "power": power.tolist(),
        "shape": [int(frequencies.size)],
        "dtype": "float64",
    }


def convolve(a: Any, b: Any, mode: str = "full") -> dict[str, Any]:
    """Linear convolution of two 1-D sequences.

    mode is "full" (default), "same", or "valid". "same" returns the central part,
    the same length as a. "valid" returns only positions where the sequences overlap
    completely. This is not circular convolution; use fft products for that.
    """
    if mode not in _MODES:
        raise ToolError(
            "bad_mode",
            f"mode must be one of {sorted(_MODES)}.",
            "Use mode 'full', 'same', or 'valid'.",
        )
    left = parse_array(a, ndim=1)
    right = parse_array(b, ndim=1)
    return pack(scipy.signal.convolve(left, right, mode=mode))


def solve_linear_system(a: Any, b: Any) -> dict[str, Any]:
    """Solve A x = b for a square matrix.

    A is a list of lists, or {"re", "im"} with that shape. b is a vector with one
    entry per row. The result includes residual_norm, the 2-norm of A x - b.
    A non-square matrix is rejected; use least_squares for that case.
    """
    matrix = parse_array(a, ndim=2)
    vector = parse_array(b, ndim=1)
    if matrix.shape[0] != matrix.shape[1]:
        raise ToolError(
            "not_square",
            f"A has shape {list(matrix.shape)}, which is not square.",
            "Use least_squares when A is not square.",
        )
    if vector.shape[0] != matrix.shape[0]:
        raise ToolError(
            "shape_mismatch",
            f"b has length {vector.shape[0]} but A has {matrix.shape[0]} rows.",
            "Give b one value per row of A.",
        )
    try:
        solution = scipy.linalg.solve(matrix, vector)
    except scipy.linalg.LinAlgError as exc:
        raise ToolError(
            "singular",
            f"The square system could not be solved ({exc}).",
            "Use least_squares, or change A so that it is invertible.",
        ) from exc
    packed = pack(solution)
    packed["residual_norm"] = float(np.linalg.norm(matrix @ solution - vector))
    return packed


def least_squares(a: Any, b: Any) -> dict[str, Any]:
    """Minimize the 2-norm of A x - b.

    A may be square or rectangular. The result includes residual_norm and rank.
    For a square invertible system, solve_linear_system is the direct solver.
    """
    matrix = parse_array(a, ndim=2)
    vector = parse_array(b, ndim=1)
    if vector.shape[0] != matrix.shape[0]:
        raise ToolError(
            "shape_mismatch",
            f"b has length {vector.shape[0]} but A has {matrix.shape[0]} rows.",
            "Give b one value per row of A.",
        )
    solution, _residuals, rank, _singular = scipy.linalg.lstsq(matrix, vector)
    packed = pack(np.asarray(solution).reshape(-1))
    packed["residual_norm"] = float(np.linalg.norm(matrix @ solution - vector))
    packed["rank"] = int(rank)
    return packed


TOOLS = {
    "fft": fft,
    "power_spectrum": power_spectrum,
    "convolve": convolve,
    "solve_linear_system": solve_linear_system,
    "least_squares": least_squares,
}
