"""Run model-written Python in a short-lived subprocess.

This limits runaway code. It does not contain hostile code. Callers should
execute output only from trusted runs.
"""

import json
import os
import subprocess
import sys
import tempfile
from typing import Any

_KEEP_ENV = {
    "PATH",
    "PATHEXT",
    "SYSTEMROOT",
    "WINDIR",
    "COMSPEC",
    "TEMP",
    "TMP",
    "TMPDIR",
    "HOME",
    "USERPROFILE",
    "LANG",
    "LC_ALL",
}


def _child_env() -> dict[str, str]:
    env = {key: value for key, value in os.environ.items() if key in _KEEP_ENV}
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    return env


def _memory_limiter(memory_mb: int) -> Any:
    if os.name == "nt":
        return None

    def _limit() -> None:
        import resource

        limit = memory_mb * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_AS, (limit, limit))

    return _limit


def run_python(code: str, *, timeout_s: float = 20.0, memory_mb: int = 512) -> str:
    """Return a JSON object with stdout, stderr, and exit_code, or a structured error."""
    with tempfile.TemporaryDirectory(prefix="eval-sandbox-") as directory:
        script = os.path.join(directory, "main.py")
        with open(script, "w", encoding="utf-8") as handle:
            handle.write(code)
        try:
            completed = subprocess.run(
                [sys.executable, script],
                cwd=directory,
                env=_child_env(),
                capture_output=True,
                text=True,
                timeout=timeout_s,
                preexec_fn=_memory_limiter(memory_mb),
                check=False,
            )
        except subprocess.TimeoutExpired:
            return json.dumps(
                {
                    "error_code": "timeout",
                    "message": f"The program ran longer than {timeout_s} seconds.",
                    "fix_hint": "Shorten the computation or remove an infinite loop.",
                }
            )
        except OSError as exc:
            return json.dumps(
                {
                    "error_code": "sandbox_failed",
                    "message": str(exc),
                    "fix_hint": "Check that Python can start a subprocess.",
                }
            )
    return json.dumps(
        {
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "exit_code": completed.returncode,
        }
    )
