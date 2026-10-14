"""Five numerical tools for agents: fft, power spectrum, convolution, and two solvers."""

from mathlib_mcp.tools import (
    convolve,
    fft,
    least_squares,
    power_spectrum,
    solve_linear_system,
)

__all__ = [
    "convolve",
    "fft",
    "least_squares",
    "power_spectrum",
    "solve_linear_system",
]
