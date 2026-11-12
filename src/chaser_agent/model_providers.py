"""The AI providers Chaser can think with, and each one's key, saved encrypted for this Windows account.

ChaseOS Cloud comes first and is recommended, the way other harnesses lead with their own service,
but any provider here works, and so does any other OpenAI-compatible endpoint. Keys are kept like
the ChaseOS Cloud key (DPAPI, never printed or returned), one file per provider. A key in the
provider's usual environment variable wins, so a vault that injects it keeps working.

Checking a key costs nothing: it lists the provider's models, which also offers them to choose from.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from chaser_agent import chaser_home, cloud_key


@dataclass(frozen=True)
class Provider:
    id: str
    label: str
    blurb: str
    kind: str              # chaseos | openai (any OpenAI-compatible API) | claude-cli | bridge
    base_url: str = ""     # up to and including the version, e.g. https://api.openai.com/v1
    key_env: str = ""      # the environment variable a vault would set
    keys_page: str = ""    # where to get a key
    needs_key: bool = True
    model: str = ""        # a sensible default, where the provider has a stable alias


CATALOGUE: tuple[Provider, ...] = (
    Provider("chaseos-cloud", "ChaseOS Cloud", "Recommended. Built for Chaser: one key, credits, pricing tuned for agent work.",
             "chaseos", "https://chaseos.ai/api/cloud/v1", "CHASEOS_CLOUD_KEY", "https://chaseos.ai", model="chaseos/balanced"),
    Provider("claude-cli", "Claude (Claude Code sign-in)", "Uses this computer's Claude Code sign-in. No key here.", "claude-cli",
             needs_key=False),
    Provider("openrouter", "OpenRouter", "Hundreds of models behind one key.", "openai", "https://openrouter.ai/api/v1",
             "OPENROUTER_API_KEY", "https://openrouter.ai/keys", model="openrouter/auto"),
    Provider("openai", "OpenAI", "OpenAI's API on your own key.", "openai", "https://api.openai.com/v1", "OPENAI_API_KEY",
             "https://platform.openai.com/api-keys"),
    Provider("gemini", "Google Gemini", "Gemini through Google's OpenAI-compatible API.", "openai",
             "https://generativelanguage.googleapis.com/v1beta/openai", "GEMINI_API_KEY", "https://aistudio.google.com/apikey"),
    Provider("xai", "xAI (Grok)", "Grok models on your own key.", "openai", "https://api.x.ai/v1", "XAI_API_KEY", "https://console.x.ai"),
    Provider("deepseek", "DeepSeek", "DeepSeek's own API.", "openai", "https://api.deepseek.com/v1", "DEEPSEEK_API_KEY",
             "https://platform.deepseek.com/api_keys"),
    Provider("mistral", "Mistral", "Mistral's own API.", "openai", "https://api.mistral.ai/v1", "MISTRAL_API_KEY",
             "https://console.mistral.ai/api-keys"),
    Provider("groq", "Groq", "Open models served very fast.", "openai", "https://api.groq.com/openai/v1", "GROQ_API_KEY",
             "https://console.groq.com/keys"),
    Provider("together", "Together AI", "Open models on Together's API.", "openai", "https://api.together.xyz/v1", "TOGETHER_API_KEY",
             "https://api.together.ai/settings/api-keys"),
    Provider("fireworks", "Fireworks AI", "Open models on Fireworks' API.", "openai", "https://api.fireworks.ai/inference/v1",
             "FIREWORKS_API_KEY", "https://fireworks.ai/account/api-keys"),
    Provider("ollama", "Ollama (on this computer)", "Local models. Nothing leaves this computer; no key.", "openai",
             "http://127.0.0.1:11434/v1", needs_key=False),
    Provider("lmstudio", "LM Studio (on this computer)", "Local models from LM Studio's server; no key.", "openai",
             "http://127.0.0.1:1234/v1", needs_key=False),
    Provider("custom", "Another OpenAI-compatible endpoint", "vLLM, LiteLLM, a company gateway: give its address.", "openai",
             key_env="CHASER_CUSTOM_API_KEY"),
    Provider("bridge", "Another agent harness", "Hermes or any harness answers over Chaser's local API.", "bridge", needs_key=False),
)
BY_ID = {provider.id: provider for provider in CATALOGUE}
DEFAULT = "chaseos-cloud"


def get(provider_id: str | None) -> Provider:
    return BY_ID.get(provider_id or DEFAULT, BY_ID[DEFAULT])


def chosen(settings: dict[str, Any]) -> tuple[Provider, str, str]:
    """The provider, model and address these settings pick."""
    provider = get(settings.get("provider"))
    model = settings.get("model") or provider.model
    base_url = (settings.get("base_url") or provider.base_url).rstrip("/")
    return provider, model, base_url


def describe(settings: dict[str, Any]) -> str:
    """'OpenRouter · openrouter/auto' for menus and status lines."""
    provider, model, _ = chosen(settings)
    return f"{provider.label} · {model}" if model and provider.kind in {"openai", "chaseos"} else provider.label


# --- Keys ---------------------------------------------------------------------

def _path(provider_id: str) -> Path:
    return chaser_home.home() / "keys" / f"{provider_id}.dpapi"


def save_key(provider_id: str, key: str) -> None:
    if provider_id == "chaseos-cloud":
        cloud_key.save(key)
        return
    key = cloud_key.validate(key)
    target = _path(provider_id)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(".partial")
    temporary.write_text(cloud_key._dpapi(key.encode("utf-16-le"), protect=True).hex(), encoding="ascii")
    os.replace(temporary, target)


def load_key(provider_id: str, environ: dict[str, str] | None = None) -> tuple[str, str]:
    """(key, source): the environment first, then the saved key. ('', 'none') when there is neither."""
    environ = os.environ if environ is None else environ
    provider = get(provider_id)
    if provider.key_env and environ.get(provider.key_env, "").strip():
        return environ[provider.key_env].strip(), "environment"
    if provider_id == "chaseos-cloud":
        key = cloud_key.load()
        return (key, "saved") if key else ("", "none")
    try:
        raw = _path(provider_id).read_text(encoding="ascii").strip()
        key = cloud_key._dpapi(bytes.fromhex(raw), protect=False).decode("utf-16-le") if raw else ""
    except (OSError, ValueError, UnicodeError, cloud_key.KeyStoreUnavailable):
        key = ""
    return (key, "saved") if key else ("", "none")


def forget_key(provider_id: str) -> bool:
    if provider_id == "chaseos-cloud":
        return cloud_key.forget()
    try:
        _path(provider_id).unlink()
        return True
    except FileNotFoundError:
        return False


def list_models(base_url: str, key: str = "", *, timeout: float = 10.0) -> tuple[int, list[str]]:
    """(HTTP status, model ids) from GET {base_url}/models. Free on every provider here; 0 means no connection."""
    import urllib.error
    import urllib.request

    headers = {"User-Agent": "ChaserAgent/1"}
    if key:
        headers["Authorization"] = f"Bearer {key}"
    try:
        with urllib.request.urlopen(urllib.request.Request(f"{base_url.rstrip('/')}/models", headers=headers), timeout=timeout) as reply:  # noqa: S310
            value = json.loads(reply.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return exc.code, []
    except (urllib.error.URLError, TimeoutError, ConnectionError, OSError, ValueError):
        return 0, []
    rows = value.get("data") if isinstance(value, dict) else value
    ids = [str(row.get("id")) for row in rows or [] if isinstance(row, dict) and row.get("id")]
    return 200, sorted(set(ids))
