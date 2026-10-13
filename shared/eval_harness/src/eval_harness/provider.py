"""A real model client. Tests inject a transport so they never open a network connection."""

import json
import os
import urllib.request
from typing import Any

from eval_harness.models import ModelResponse, ToolCall

_PROVIDER_URLS = {
    "openai": "https://api.openai.com/v1/chat/completions",
}


def _post_json(url: str, api_key: str, payload: dict[str, Any]) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def _openai_tool(tool: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": tool["name"],
            "description": tool.get("description", ""),
            "parameters": tool.get("parameters", {"type": "object", "properties": {}}),
        },
    }


def _parse_arguments(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    if not isinstance(raw, str):
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return {"_raw": raw}
    if isinstance(parsed, dict):
        return parsed
    return {"_raw": raw}


class ProviderClient:
    def __init__(
        self,
        provider: str,
        *,
        model: str | None = None,
        model_env: str | None = None,
        api_key_env: str = "OPENAI_API_KEY",
        base_url: str | None = None,
        transport: Any = None,
    ) -> None:
        if model:
            self.model = model
        elif model_env:
            value = os.environ.get(model_env)
            if not value:
                raise RuntimeError(f"{model_env} is not set")
            self.model = value
        else:
            raise RuntimeError("model must come from config or an environment variable")
        self.provider = provider
        self._api_key_env = api_key_env
        self._url = base_url or _PROVIDER_URLS.get(provider)
        if self._url is None:
            raise RuntimeError(f"No URL is configured for provider {provider!r}. Pass base_url.")
        self._transport = transport or _post_json

    def complete(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None,
    ) -> ModelResponse:
        payload: dict[str, Any] = {"model": self.model, "messages": messages}
        if tools:
            payload["tools"] = [_openai_tool(tool) for tool in tools]
        api_key = ""
        if self._transport is _post_json:
            api_key = os.environ.get(self._api_key_env, "")
            if not api_key:
                raise RuntimeError(f"{self._api_key_env} is not set")
        body = self._transport(self._url, api_key, payload)
        return _parse_response(body)


def _parse_response(body: dict[str, Any]) -> ModelResponse:
    choice = body["choices"][0]["message"]
    tool_calls: list[ToolCall] = []
    for call in choice.get("tool_calls") or []:
        function = call.get("function", {})
        tool_calls.append(
            ToolCall(
                id=str(call.get("id", "")),
                name=str(function.get("name", "")),
                arguments=_parse_arguments(function.get("arguments", {})),
            )
        )
    usage = body.get("usage") or {}
    return ModelResponse(
        content=choice.get("content"),
        tool_calls=tool_calls,
        input_tokens=int(usage.get("prompt_tokens") or 0),
        output_tokens=int(usage.get("completion_tokens") or 0),
    )
