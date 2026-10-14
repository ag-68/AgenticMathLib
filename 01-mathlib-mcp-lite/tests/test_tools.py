"""M1: the five tools match SciPy, and bad inputs return a teaching error."""

import json
import sys

import numpy as np
import pytest
import scipy.fft
import scipy.linalg
import scipy.signal

from mathlib_mcp.arrays import MAX_ELEMENTS
from mathlib_mcp.errors import ToolError
from mathlib_mcp.tools import convolve, fft, least_squares, power_spectrum, solve_linear_system


def test_fft_matches_scipy_and_round_trips() -> None:
    samples = [1.0, 2.0, 3.0, 4.0]
    forward = fft(samples, direction="forward", norm="ortho")
    expected = scipy.fft.fft(np.asarray(samples), norm="ortho")
    assert np.allclose(forward["re"], expected.real)
    assert np.allclose(forward["im"], expected.imag)
    assert forward["dtype"] == "complex128"
    restored = fft({"re": forward["re"], "im": forward["im"]}, direction="inverse", norm="ortho")
    assert np.allclose(restored["re"], samples)
    assert np.allclose(restored["im"], 0.0)


def test_power_spectrum_matches_the_stated_formula() -> None:
    samples = [1.0, 0.0, -1.0, 0.0]
    result = power_spectrum(samples, sample_rate_hz=8.0)
    spectrum = scipy.fft.rfft(np.asarray(samples))
    power = (np.abs(spectrum) ** 2) / len(samples)
    frequencies = scipy.fft.rfftfreq(len(samples), d=1.0 / 8.0)
    assert np.allclose(result["power"], power)
    assert np.allclose(result["frequencies_hz"], frequencies)


def test_convolve_matches_scipy_for_each_mode() -> None:
    left = [1.0, 2.0, 3.0]
    right = [0.0, 1.0, 0.5]
    for mode in ("full", "same", "valid"):
        result = convolve(left, right, mode=mode)
        expected = scipy.signal.convolve(left, right, mode=mode)
        assert np.allclose(result["values"], expected)


def test_solve_matches_scipy_for_complex_data() -> None:
    matrix = {"re": [[1.0, 0.0], [0.0, 2.0]], "im": [[1.0, 0.0], [0.0, 0.0]]}
    vector = {"re": [1.0, 0.0], "im": [0.0, 1.0]}
    result = solve_linear_system(matrix, vector)
    dense = np.array(matrix["re"]) + 1j * np.array(matrix["im"])
    target = np.array(vector["re"]) + 1j * np.array(vector["im"])
    expected = scipy.linalg.solve(dense, target)
    assert np.allclose(result["re"], expected.real)
    assert np.allclose(result["im"], expected.imag)
    assert result["residual_norm"] < 1e-8


def test_least_squares_matches_scipy_rank_and_residual() -> None:
    matrix = [[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]]
    vector = [1.0, 2.0, 3.0]
    result = least_squares(matrix, vector)
    solution, _residuals, rank, _singular = scipy.linalg.lstsq(
        np.asarray(matrix), np.asarray(vector)
    )
    assert np.allclose(result["values"], solution)
    assert result["rank"] == int(rank)
    residual = np.linalg.norm(np.asarray(matrix) @ solution - np.asarray(vector))
    assert result["residual_norm"] == pytest.approx(residual)


def test_structured_errors_name_the_fix() -> None:
    cases = [
        (lambda: fft([1.0, 2.0], direction="sideways"), "bad_direction"),
        (lambda: fft([1.0, 2.0], norm="fancy"), "bad_norm"),
        (lambda: power_spectrum([1.0, 2.0], sample_rate_hz=0), "bad_sample_rate"),
        (lambda: convolve([1.0], [1.0], mode="circular"), "bad_mode"),
        (lambda: solve_linear_system([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]], [1.0, 2.0]), "not_square"),
        (lambda: fft([0.0] * (MAX_ELEMENTS + 1)), "too_large"),
        (lambda: fft({"re": [1.0, 2.0], "im": [0.0]}), "shape_mismatch"),
        (lambda: solve_linear_system([[0.0, 0.0], [0.0, 0.0]], [1.0, 1.0]), "singular"),
    ]
    for call, code in cases:
        try:
            call()
        except ToolError as exc:
            assert exc.error_code == code
            assert exc.fix_hint
        else:
            raise AssertionError(f"{code} was not raised")
    square_hint = _hint(
        lambda: solve_linear_system([[1.0, 0.0], [0.0, 1.0], [1.0, 0.0]], [1.0, 2.0, 3.0])
    )
    assert "least_squares" in square_hint


def test_server_lists_five_tools_and_runs_fft() -> None:
    from eval_harness import McpExecutor, ToolCall

    with McpExecutor(sys.executable, ["-m", "mathlib_mcp.server"]) as executor:
        listed = executor.list_tools()
        names = sorted(tool["name"] for tool in listed)
        described = {tool["name"]: tool["description"] for tool in listed}
        raw = executor.execute(ToolCall("c1", "fft", {"x": [1.0, 0.0, 0.0, 0.0]}))
    assert names == ["convolve", "fft", "least_squares", "power_spectrum", "solve_linear_system"]
    assert "When not to use" in described["fft"]
    assert "least_squares" in described["solve_linear_system"]
    payload = json.loads(raw)
    assert len(payload["re"]) == 4


def _hint(call: object) -> str:
    try:
        call()  # type: ignore[operator]
    except ToolError as exc:
        return exc.fix_hint
    raise AssertionError("expected ToolError")
