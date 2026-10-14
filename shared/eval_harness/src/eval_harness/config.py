"""Load the flat eval_config.yaml used by the CLI."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class EvalConfig:
    provider: str = "openai"
    model: str | None = None
    model_env: str | None = "EVAL_MODEL"
    trials: int = 3
    max_tool_calls: int = 8
    seed: int = 0
    timeout_s: float = 20
    model_tier: str | None = None


def load_config(path: Path) -> EvalConfig:
    values = _read_flat_yaml(path)
    return EvalConfig(
        provider=str(values.get("provider", "openai")),
        model=_optional_str(values.get("model")),
        model_env=_optional_str(values.get("model_env", "EVAL_MODEL")),
        trials=int(values.get("trials", 3)),
        max_tool_calls=int(values.get("max_tool_calls", 8)),
        seed=int(values.get("seed", 0)),
        timeout_s=float(values.get("timeout_s", 20)),
        model_tier=_optional_str(values.get("model_tier")),
    )


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _read_flat_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(path)
    values: dict[str, Any] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or ":" not in stripped:
            continue
        key, raw = stripped.split(":", 1)
        values[key.strip()] = _parse_scalar(raw.strip())
    return values


def _parse_scalar(raw: str) -> Any:
    if raw in {"", "null", "~"}:
        return None
    if raw in {"true", "false"}:
        return raw == "true"
    try:
        return int(raw)
    except ValueError:
        pass
    try:
        return float(raw)
    except ValueError:
        return raw.strip("\"'")
