"""
Cliente HTTP compartilhado para GitHub AI (Copilot + Azure Inference).

Suporte a:
  - Chat Completions (endpoint Copilot)
  - Embeddings (endpoint Copilot / Azure Inference)

Configuração via variáveis de ambiente:
  GITHUB_TOKEN          — token PAT / gh auth token
  GITHUB_AI_TIMEOUT     — timeout em segundos (padrão: 60)
  GITHUB_AI_MAX_RETRIES — tentativas em caso de erro 429/5xx (padrão: 3)
"""
from __future__ import annotations

import json
import logging
import os
import time
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# ── Endpoints confirmados como funcionais via teste real ──────────────────────
COPILOT_CHAT_URL = "https://api.githubcopilot.com/chat/completions"
COPILOT_EMBED_URL = "https://api.githubcopilot.com/embeddings"
AZURE_CHAT_URL = "https://models.inference.ai.azure.com/chat/completions"
AZURE_EMBED_URL = "https://models.inference.ai.azure.com/embeddings"

# Modelos confirmados como 200 OK durante testes de invocação real
MODELS = {
    # Chat — Copilot endpoint
    "parser": "Meta-Llama-3.1-405B-Instruct",   # Azure Inference
    "classifier": "claude-sonnet-4.6",            # Copilot
    "generator": "gpt-5.2",                       # Copilot
    # Embeddings
    "embedding": "text-embedding-3-large",        # Azure Inference
}


def _get_token() -> str:
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        import subprocess  # noqa: PLC0415
        try:
            result = subprocess.run(
                ["gh", "auth", "token"],
                capture_output=True,
                text=True,
                timeout=5,
                check=True,
            )
            token = result.stdout.strip()
        except Exception:
            pass
    if not token:
        raise RuntimeError(
            "GITHUB_TOKEN não definido e 'gh auth token' falhou. "
            "Defina a variável de ambiente GITHUB_TOKEN."
        )
    return token


def _headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {_get_token()}",
        "Content-Type": "application/json",
    }


def _retry_request(
    method: str,
    url: str,
    payload: dict[str, Any],
    max_retries: int | None = None,
    timeout: float | None = None,
) -> dict[str, Any]:
    """
    Executa requisição HTTP com retry exponencial para 429 e 5xx.

    Returns:
        JSON de resposta como dict.

    Raises:
        RuntimeError: Após esgotar tentativas ou em erro 4xx definitivo.
    """
    max_retries = max_retries or int(os.environ.get("GITHUB_AI_MAX_RETRIES", "3"))
    timeout = timeout or float(os.environ.get("GITHUB_AI_TIMEOUT", "60"))

    last_exc: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            with httpx.Client(timeout=timeout) as client:
                resp = client.request(
                    method,
                    url,
                    headers=_headers(),
                    content=json.dumps(payload),
                )

            if resp.status_code == 200:
                return resp.json()

            if resp.status_code == 429:
                retry_after = float(resp.headers.get("retry-after", 2 ** attempt))
                logger.warning(
                    "Rate limit atingido em %s. Aguardando %.1fs (tentativa %d/%d)",
                    url, retry_after, attempt, max_retries,
                )
                time.sleep(retry_after)
                continue

            if resp.status_code >= 500:
                wait = 2 ** attempt
                logger.warning(
                    "Erro %d em %s. Tentativa %d/%d — aguardando %ds",
                    resp.status_code, url, attempt, max_retries, wait,
                )
                time.sleep(wait)
                continue

            # 4xx definitivo — não há motivo para retry
            try:
                body = resp.json()
            except Exception:
                body = resp.text
            raise RuntimeError(
                f"GitHub AI retornou HTTP {resp.status_code}: {body}"
            )

        except httpx.TimeoutException as exc:
            wait = 2 ** attempt
            logger.warning(
                "Timeout em %s (tentativa %d/%d) — aguardando %ds",
                url, attempt, max_retries, wait,
            )
            last_exc = exc
            time.sleep(wait)
        except RuntimeError:
            raise
        except Exception as exc:
            last_exc = exc
            logger.warning(
                "Erro inesperado em %s (tentativa %d/%d): %s",
                url, attempt, max_retries, exc,
            )
            time.sleep(2 ** attempt)

    raise RuntimeError(
        f"GitHub AI falhou após {max_retries} tentativas em {url}. "
        f"Último erro: {last_exc}"
    )


def chat_completion(
    messages: list[dict[str, str]],
    model: str,
    *,
    max_tokens: int = 2048,
    temperature: float = 0.1,
    endpoint: str = COPILOT_CHAT_URL,
    response_format: dict[str, str] | None = None,
    max_retries: int | None = None,
    timeout: float | None = None,
) -> str:
    """
    Invoca chat completion e retorna apenas o texto da primeira escolha.

    Args:
        messages: Lista de mensagens no formato OpenAI.
        model: ID do modelo (use constantes em MODELS).
        max_tokens: Limite de tokens na resposta.
        temperature: 0.0 = determinístico, 1.0 = criativo.
        endpoint: URL do endpoint (Copilot ou Azure).
        response_format: Ex.: {"type": "json_object"} para JSON mode.

    Returns:
        Conteúdo textual da resposta.
    """
    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    if response_format:
        payload["response_format"] = response_format

    logger.debug("chat_completion → model=%s endpoint=%s", model, endpoint)
    data = _retry_request("POST", endpoint, payload, max_retries=max_retries, timeout=timeout)

    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as exc:
        raise RuntimeError(f"Resposta inesperada da API: {data}") from exc


def embed(
    texts: list[str],
    model: str = MODELS["embedding"],
    *,
    endpoint: str = AZURE_EMBED_URL,
    input_type: str = "query",
) -> list[list[float]]:
    """
    Gera embeddings para uma lista de textos.

    Args:
        texts: Lista de strings para embedding.
        model: Modelo de embedding.
        endpoint: URL do endpoint.
        input_type: "query" ou "document" (relevante para Cohere).

    Returns:
        Lista de vetores float.
    """
    payload: dict[str, Any] = {
        "model": model,
        "input": texts,
    }
    # Cohere requer input_type; Azure OpenAI ignora silenciosamente
    if "cohere" in model.lower() or "embed" in model.lower():
        payload["input_type"] = input_type

    logger.debug("embed → model=%s texts=%d endpoint=%s", model, len(texts), endpoint)
    data = _retry_request("POST", endpoint, payload)

    try:
        sorted_data = sorted(data["data"], key=lambda x: x["index"])
        return [item["embedding"] for item in sorted_data]
    except (KeyError, TypeError) as exc:
        raise RuntimeError(f"Resposta inesperada de embedding: {data}") from exc
