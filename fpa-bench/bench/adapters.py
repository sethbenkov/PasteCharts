"""Model/harness adapters.

Three ways to run a candidate:
  1. AnthropicAdapter  -- Anthropic Messages API (chat mode)
  2. OpenAICompatAdapter -- any OpenAI-compatible endpoint: OpenAI, OpenRouter
     (Gemini/Llama/etc.), local vLLM. Set base_url + api key env var.
  3. CLIAgentAdapter   -- run an agentic harness as a subprocess in the task's
     working directory (e.g. `claude -p`, `codex exec`). This is "agent mode":
     the harness can read the data files and write/execute code.

All adapters return (text, meta) where meta captures tokens/latency/cost when known.
"""

from __future__ import annotations

import json
import os
import shlex
import subprocess
import time
import urllib.request
from dataclasses import dataclass, field


@dataclass
class GenMeta:
    latency_s: float = 0.0
    input_tokens: int | None = None
    output_tokens: int | None = None
    raw: dict = field(default_factory=dict)


class Adapter:
    name: str = "base"

    def generate(self, prompt: str, workdir: str | None = None) -> tuple[str, GenMeta]:
        raise NotImplementedError


def _http_json(url: str, headers: dict, payload: dict, timeout: int = 600) -> dict:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", **headers},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


class AnthropicAdapter(Adapter):
    def __init__(self, model: str, max_tokens: int = 8192, thinking_budget: int | None = None):
        self.model = model
        self.max_tokens = max_tokens
        self.thinking_budget = thinking_budget
        self.name = f"anthropic:{model}"

    def generate(self, prompt: str, workdir: str | None = None) -> tuple[str, GenMeta]:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is not set")
        payload: dict = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        if self.thinking_budget:
            payload["thinking"] = {"type": "enabled", "budget_tokens": self.thinking_budget}
            payload["max_tokens"] = self.max_tokens + self.thinking_budget
        t0 = time.time()
        data = _http_json(
            "https://api.anthropic.com/v1/messages",
            {"x-api-key": api_key, "anthropic-version": "2023-06-01"},
            payload,
        )
        latency = time.time() - t0
        text = "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")
        usage = data.get("usage", {})
        return text, GenMeta(latency, usage.get("input_tokens"), usage.get("output_tokens"), data)


class OpenAICompatAdapter(Adapter):
    def __init__(
        self,
        model: str,
        base_url: str = "https://api.openai.com/v1",
        api_key_env: str = "OPENAI_API_KEY",
        max_tokens: int = 8192,
    ):
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.api_key_env = api_key_env
        self.max_tokens = max_tokens
        self.name = f"openai-compat:{model}"

    def generate(self, prompt: str, workdir: str | None = None) -> tuple[str, GenMeta]:
        api_key = os.environ.get(self.api_key_env)
        if not api_key:
            raise RuntimeError(f"{self.api_key_env} is not set")
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_completion_tokens": self.max_tokens,
        }
        t0 = time.time()
        data = _http_json(
            f"{self.base_url}/chat/completions",
            {"Authorization": f"Bearer {api_key}"},
            payload,
        )
        latency = time.time() - t0
        text = data["choices"][0]["message"]["content"] or ""
        usage = data.get("usage", {})
        return text, GenMeta(latency, usage.get("prompt_tokens"), usage.get("completion_tokens"), data)


class CLIAgentAdapter(Adapter):
    """Run an agentic CLI harness. The prompt is passed on stdin; the harness runs
    inside `workdir`, where the task's data/ files have been copied.

    Example command templates:
      claude -p --permission-mode acceptEdits --output-format text
      codex exec --sandbox workspace-write -
    """

    def __init__(self, command: str, name: str | None = None, timeout: int = 1800):
        self.command = command
        self.timeout = timeout
        self.name = name or f"cli:{command.split()[0]}"

    def generate(self, prompt: str, workdir: str | None = None) -> tuple[str, GenMeta]:
        t0 = time.time()
        proc = subprocess.run(
            shlex.split(self.command),
            input=prompt,
            capture_output=True,
            text=True,
            cwd=workdir,
            timeout=self.timeout,
        )
        latency = time.time() - t0
        out = proc.stdout
        if proc.returncode != 0 and not out.strip():
            out = f"[harness error, exit {proc.returncode}]\n{proc.stderr[-2000:]}"
        return out, GenMeta(latency, raw={"exit_code": proc.returncode})


# ---------------------------------------------------------------------------
# Registry: model spec strings -> adapters.
#   anthropic/<model>              e.g. anthropic/claude-sonnet-5
#   openai/<model>                 e.g. openai/gpt-5.2
#   openrouter/<model>             e.g. openrouter/google/gemini-3-pro
#   cli/<name>                     looks up command in models.json "cli" section
# ---------------------------------------------------------------------------

def make_adapter(spec: str, config: dict | None = None) -> Adapter:
    config = config or {}
    provider, _, model = spec.partition("/")
    if provider == "anthropic":
        return AnthropicAdapter(model, thinking_budget=config.get("thinking_budget"))
    if provider == "openai":
        return OpenAICompatAdapter(model)
    if provider == "openrouter":
        return OpenAICompatAdapter(
            model, base_url="https://openrouter.ai/api/v1", api_key_env="OPENROUTER_API_KEY"
        )
    if provider == "cli":
        cli_cfg = (config.get("cli") or {}).get(model)
        if not cli_cfg:
            raise ValueError(f"No cli config for '{model}' (add it to models.json)")
        return CLIAgentAdapter(cli_cfg["command"], name=f"cli:{model}", timeout=cli_cfg.get("timeout", 1800))
    raise ValueError(f"Unknown provider in spec: {spec}")
