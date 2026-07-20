---
name: local-agent-model-defaults
description: Use when creating or modifying AI agent projects and choosing a model, API key, OpenAI-compatible base URL, LiteLLM endpoint, or related environment variables.
---

# Local Agent Model Defaults

Use these personal defaults for AI agent projects unless the user or the project explicitly specifies another provider, model, API key, or endpoint.

## Local LiteLLM Defaults

Prefer the local OpenAI-compatible LiteLLM proxy on port `4000`:

```dotenv
OPENAI_API_KEY=sk-no-key-needed
OPENAI_BASE_URL=http://localhost:4000/v1
OPENAI_MODEL=ds-deepseek-v4-flash
```

The OpenAI-compatible client uses `http://localhost:4000/v1` as its base URL and sends chat requests to `/chat/completions`. The local proxy does not require a real provider API key, so `sk-no-key-needed` is the intended placeholder.

## Decision Rules

1. Use the local LiteLLM values above when an AI agent implementation needs model configuration and no explicit alternative is requested.
2. Preserve an explicit model, provider, base URL, or secret supplied by the user or already required by the project.
3. Never invent or request a real external API key when the local LiteLLM proxy is the intended backend.
4. Keep secrets out of source control; use environment variables or the project's existing configuration mechanism.

## Example

For a new OpenAI-compatible agent configuration, use:

```python
from langchain_openai import ChatOpenAI

model = ChatOpenAI(
    model="ds-deepseek-v4-flash",
    api_key="sk-no-key-needed",
    base_url="http://localhost:4000/v1",
)
```
