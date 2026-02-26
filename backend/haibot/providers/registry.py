# -*- coding: utf-8 -*-
"""Built-in provider definitions and registry."""

from __future__ import annotations

from typing import List, Optional

from .models import ModelInfo, ProviderDefinition

# ---------------------------------------------------------------------------
# Built-in LLM model lists
# ---------------------------------------------------------------------------

MODELSCOPE_MODELS: List[ModelInfo] = [
    ModelInfo(
        id="Qwen/Qwen3-235B-A22B-Instruct-2507",
        name="Qwen3-235B-A22B-Instruct-2507",
    ),
    ModelInfo(id="deepseek-ai/DeepSeek-V3.2", name="DeepSeek-V3.2"),
]

DASHSCOPE_MODELS: List[ModelInfo] = [
    ModelInfo(id="qwen3-max", name="Qwen3 Max"),
    ModelInfo(
        id="qwen3-235b-a22b-thinking-2507",
        name="Qwen3 235B A22B Thinking",
    ),
    ModelInfo(id="deepseek-v3.2", name="DeepSeek-V3.2"),
]

ANTHROPIC_MODELS: List[ModelInfo] = [
    ModelInfo(id="claude-opus-4-6", name="Claude Opus 4.6"),
    ModelInfo(id="claude-sonnet-4-6", name="Claude Sonnet 4.6"),
    ModelInfo(id="claude-haiku-4-5-20251001", name="Claude Haiku 4.5"),
    ModelInfo(id="claude-opus-4-5", name="Claude Opus 4.5"),
    ModelInfo(id="claude-sonnet-4-5", name="Claude Sonnet 4.5"),
]

GLM_MODELS: List[ModelInfo] = [
    ModelInfo(id="glm-4-plus", name="GLM-4 Plus"),
    ModelInfo(id="glm-4-long", name="GLM-4 Long"),
    ModelInfo(id="glm-4-flash", name="GLM-4 Flash"),
    ModelInfo(id="glm-z1-plus", name="GLM-Z1 Plus"),
    ModelInfo(id="glm-z1-flash", name="GLM-Z1 Flash"),
]

MINIMAX_MODELS: List[ModelInfo] = [
    ModelInfo(id="MiniMax-2.5", name="MiniMax 2.5"),
    ModelInfo(id="MiniMax-2.1", name="MiniMax 2.1"),
]

# ---------------------------------------------------------------------------
# Provider definitions
# ---------------------------------------------------------------------------

PROVIDER_MODELSCOPE = ProviderDefinition(
    id="modelscope",
    name="ModelScope",
    default_base_url="https://api-inference.modelscope.cn/v1",
    api_key_prefix="ms",
    models=MODELSCOPE_MODELS,
    model_type="openai",
)

PROVIDER_DASHSCOPE = ProviderDefinition(
    id="dashscope",
    name="DashScope",
    default_base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    api_key_prefix="sk",
    models=DASHSCOPE_MODELS,
    model_type="openai",
)

PROVIDER_ANTHROPIC = ProviderDefinition(
    id="anthropic",
    name="Anthropic",
    default_base_url="https://api.anthropic.com",
    api_key_prefix="sk-ant-",
    models=ANTHROPIC_MODELS,
    model_type="anthropic",
    # allow_custom_base_url lets power users point to an Anthropic-compatible
    # proxy (e.g. AWS Bedrock gateway, corporate relay).
    allow_custom_base_url=True,
)

PROVIDER_GLM = ProviderDefinition(
    id="glm",
    name="GLM (智谱AI)",
    default_base_url="https://open.bigmodel.cn/api/paas/v4",
    api_key_prefix="",
    models=GLM_MODELS,
    model_type="openai",
)

PROVIDER_MINIMAX = ProviderDefinition(
    id="minimax",
    name="MiniMax",
    default_base_url="https://api.minimaxi.com/anthropic",
    api_key_prefix="",
    models=MINIMAX_MODELS,
    model_type="anthropic",
)

PROVIDER_OPENAI = ProviderDefinition(
    id="custom_openai",
    name="Custom OpenAI",
    default_base_url="",
    api_key_prefix="",
    models=[],
    allow_custom_base_url=True,
    model_type="openai",
)

# Registry: provider_id -> ProviderDefinition
PROVIDERS: dict[str, ProviderDefinition] = {
    PROVIDER_MODELSCOPE.id: PROVIDER_MODELSCOPE,
    PROVIDER_DASHSCOPE.id: PROVIDER_DASHSCOPE,
    PROVIDER_OPENAI.id: PROVIDER_OPENAI,
    PROVIDER_GLM.id: PROVIDER_GLM,
    PROVIDER_MINIMAX.id: PROVIDER_MINIMAX,
    PROVIDER_ANTHROPIC.id: PROVIDER_ANTHROPIC,
}


def get_provider(provider_id: str) -> Optional[ProviderDefinition]:
    """Return a provider definition by id, or None if not found."""
    return PROVIDERS.get(provider_id)


def list_providers() -> List[ProviderDefinition]:
    """Return all registered provider definitions."""
    return list(PROVIDERS.values())
