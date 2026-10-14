"""The text an agent reads. docgen turns this into pages. The math stays in tools.py."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from mathlib_mcp.tools import convolve, fft, least_squares, power_spectrum, solve_linear_system

COMPLEX = 'Complex values are {"re": [...], "im": [...]} with matching shapes.'
REAL = "A real array is a list of numbers."
SIZE = "At most 4096 elements are accepted. One complex number counts as one element."


@dataclass(frozen=True)
class Parameter:
    name: str
    type_name: str
    description: str
    default: str | None = None
    allowed: str | None = None


@dataclass(frozen=True)
class ToolDoc:
    name: str
    function: Callable[..., dict[str, Any]]
    one_sentence: str
    purpose: str
    when_to_use: str
    when_not: str
    parameters: tuple[Parameter, ...]
    returns: str
    conventions: tuple[str, ...]
    common_mistakes: tuple[str, ...]
    example_arguments: dict[str, Any]
    related: tuple[str, ...]


CATALOG: tuple[ToolDoc, ...] = (
    ToolDoc(
        name="fft",
        function=fft,
        one_sentence="Compute a one-dimensional discrete Fourier transform.",
        purpose="Transform a 1-D sequence into frequency bins, or restore the sequence.",
        when_to_use="You need the forward or inverse discrete Fourier transform of one sequence.",
        when_not="You want the one-sided power of a real recording. Use power_spectrum.",
        parameters=(
            Parameter(
                "x",
                "list or object",
                f"The 1-D sequence. {REAL} {COMPLEX}",
            ),
            Parameter(
                "direction",
                "string",
                "Which transform to apply.",
                default='"forward"',
                allowed="forward, inverse",
            ),
            Parameter(
                "norm",
                "string",
                "Scaling. backward is NumPy's usual unnormalized forward transform.",
                default='"backward"',
                allowed="backward, forward, ortho",
            ),
        ),
        returns=(
            "A complex sequence of the same length, with shape, dtype, re, and im. "
            "The inverse of a forward transform uses the same norm and restores the input."
        ),
        conventions=(
            REAL,
            COMPLEX,
            SIZE,
            "The default norm is backward, not ortho. An inverse call must use the same norm.",
            "Bins follow SciPy's fft order: the zero frequency is first.",
        ),
        common_mistakes=(
            "Assuming the default scaling is orthonormal.",
            "Inverting with a different norm than the forward call.",
            "Asking fft for a one-sided power spectrum.",
        ),
        example_arguments={
            "x": [1.0, 0.0, 0.0, 0.0],
            "direction": "forward",
            "norm": "backward",
        },
        related=(
            "power_spectrum returns frequencies in hertz and one-sided power for a real signal.",
            "convolve is linear convolution, not multiplication of Fourier transforms.",
        ),
    ),
    ToolDoc(
        name="power_spectrum",
        function=power_spectrum,
        one_sentence="Compute the one-sided power spectrum of a real signal.",
        purpose="Report frequency bins in hertz and the one-sided power of a real sequence.",
        when_to_use="You have real samples and a sample rate, and you want power per frequency.",
        when_not="The series is complex, or you need a transform you can invert. Use fft.",
        parameters=(
            Parameter("samples", "list", "A 1-D list of real samples."),
            Parameter(
                "sample_rate_hz",
                "number",
                "Sample rate in hertz. Must be positive.",
            ),
        ),
        returns=(
            "frequencies_hz from rfftfreq, power equal to abs(rfft)^2 / n, "
            "plus shape and dtype. This is not a power spectral density."
        ),
        conventions=(
            "Input is real. A complex object is rejected.",
            SIZE,
            "frequencies_hz[0] is 0 Hz. The last bin is the Nyquist frequency when n is even.",
            "power is abs(rfft(samples))^2 divided by the number of samples.",
        ),
        common_mistakes=(
            "Treating power as a density in units of power per hertz.",
            "Ignoring frequencies_hz and assuming a bin index is already in hertz.",
            "Passing a complex series.",
        ),
        example_arguments={"samples": [1.0, 0.0, -1.0, 0.0], "sample_rate_hz": 8.0},
        related=("fft is the transform to use when you will invert it or the input is complex.",),
    ),
    ToolDoc(
        name="convolve",
        function=convolve,
        one_sentence="Convolve two one-dimensional sequences.",
        purpose="Compute the linear convolution of two 1-D sequences.",
        when_to_use="You want linear convolution in full, same, or valid mode.",
        when_not="You want circular convolution. This tool does not wrap the edges.",
        parameters=(
            Parameter("a", "list or object", f"The first 1-D sequence. {REAL} {COMPLEX}"),
            Parameter("b", "list or object", f"The second 1-D sequence. {REAL} {COMPLEX}"),
            Parameter(
                "mode",
                "string",
                "Which part of the full convolution to keep.",
                default='"full"',
                allowed="full, same, valid",
            ),
        ),
        returns=(
            "The convolved sequence, with shape, dtype, and either values or re and im. "
            "same has the length of a. valid keeps only complete overlaps."
        ),
        conventions=(
            REAL,
            COMPLEX,
            SIZE,
            "full returns every overlap, including partial ones at the ends.",
            "same returns the central part and has the same length as a.",
            "valid returns only positions where b lies entirely inside a.",
        ),
        common_mistakes=(
            "Using valid when the requested length is the length of a. That is same.",
            "Expecting the edges to wrap. This is linear convolution.",
        ),
        example_arguments={"a": [1.0, 2.0, 3.0], "b": [1.0, 1.0], "mode": "full"},
        related=(
            "fft does not replace this tool. This tool is linear convolution.",
        ),
    ),
    ToolDoc(
        name="solve_linear_system",
        function=solve_linear_system,
        one_sentence="Solve a square linear system.",
        purpose="Solve A x = b when A is square.",
        when_to_use="A is square and you want the direct solution plus a residual.",
        when_not="A is rectangular or singular. Use least_squares.",
        parameters=(
            Parameter(
                "a",
                "list of lists or object",
                f"The matrix A. It must be square. {REAL} {COMPLEX}",
            ),
            Parameter(
                "b",
                "list or object",
                "The right-hand side, one value per row of A.",
            ),
        ),
        returns=(
            "The solution vector, with shape, dtype, and residual_norm, the 2-norm of A x - b."
        ),
        conventions=(
            REAL,
            COMPLEX,
            SIZE,
            "A must have the same number of rows and columns.",
            "b has one entry per row.",
            "residual_norm near zero means the solution fits A x = b.",
        ),
        common_mistakes=(
            "Passing a rectangular matrix. The error tells you to use least_squares.",
            "Ignoring a singular error and treating a failure as a numeric answer.",
        ),
        example_arguments={"a": [[1.0, 0.0], [0.0, 1.0]], "b": [3.0, 4.0]},
        related=("least_squares minimizes ||A x - b|| when A is not square or not invertible.",),
    ),
    ToolDoc(
        name="least_squares",
        function=least_squares,
        one_sentence="Solve a linear least-squares problem.",
        purpose="Find x that minimizes the 2-norm of A x - b.",
        when_to_use="A is rectangular, or a square system may be singular.",
        when_not="A is square and invertible. Use solve_linear_system for that case.",
        parameters=(
            Parameter(
                "a",
                "list of lists or object",
                f"The matrix A, square or rectangular. {REAL} {COMPLEX}",
            ),
            Parameter("b", "list or object", "The right-hand side, one value per row of A."),
        ),
        returns="The solution vector, residual_norm (the 2-norm of A x - b), and rank.",
        conventions=(
            REAL,
            COMPLEX,
            SIZE,
            "b has one entry per row of A, not per column.",
            "rank below the number of columns means the solution is not unique.",
        ),
        common_mistakes=(
            "Reading residual_norm as zero when the system is only approximately consistent.",
            "Ignoring rank when several solutions fit equally well.",
        ),
        example_arguments={
            "a": [[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]],
            "b": [1.0, 2.0, 3.0],
        },
        related=("solve_linear_system is the direct solver for a square invertible matrix.",),
    ),
)


def by_name(name: str) -> ToolDoc:
    for doc in CATALOG:
        if doc.name == name:
            return doc
    raise KeyError(name)
