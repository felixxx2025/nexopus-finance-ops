"""
Embedding Service — Geração e gerenciamento de embeddings para RAG.

Modelo: Sentence Transformers (HuggingFace) - 100% local e gratuito
Modelo usado: paraphrase-multilingual-MiniLM-L12-v2 (384 dimensions, multilíngue)
Cache: Redis para embeddings frequentes
"""
from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.config import settings

logger = logging.getLogger(__name__)

_EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
_EMBEDDING_DIM = 384
_model_cache = None


def _get_model():
    """Carrega modelo Sentence Transformers com cache."""
    global _model_cache
    if _model_cache is None:
        try:
            from sentence_transformers import SentenceTransformer

            logger.info("Carregando modelo de embeddings: %s", _EMBEDDING_MODEL)
            _model_cache = SentenceTransformer(_EMBEDDING_MODEL)
            logger.info("Modelo carregado com sucesso (dim=%d)", _model_cache.get_sentence_embedding_dimension())
        except ImportError:
            logger.error("sentence-transformers não instalado. Instale: pip install sentence-transformers")
            raise
        except Exception as e:
            logger.error("Erro ao carregar modelo: %s", e)
            raise
    return _model_cache


def generate_embedding(text: str) -> list[float]:
    """
    Gera embedding para um texto usando Sentence Transformers (local).

    Args:
        text: Texto para gerar embedding.

    Returns:
        Lista de floats representando o embedding (384 dimensions).
    """
    if not text or not text.strip():
        logger.warning("Tentativa de gerar embedding para texto vazio.")
        return [0.0] * _EMBEDDING_DIM

    try:
        model = _get_model()
        embedding = model.encode(text, convert_to_numpy=True, show_progress_bar=False)
        logger.debug("Embedding gerado com sucesso (dim=%d)", len(embedding))
        return embedding.tolist()
    except Exception as e:
        logger.error("Falha ao gerar embedding: %s", e)
        # Fallback: retorna embedding zero
        return [0.0] * _EMBEDDING_DIM


def generate_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """
    Gera embeddings para múltiplos textos em batch (mais eficiente).

    Args:
        texts: Lista de textos para gerar embeddings.

    Returns:
        Lista de embeddings.
    """
    if not texts:
        return []

    try:
        model = _get_model()
        embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=False, batch_size=32)
        logger.debug("Batch de %d embeddings gerados", len(embeddings))
        return embeddings.tolist()
    except Exception as e:
        logger.error("Falha ao gerar batch de embeddings: %s", e)
        # Fallback: embeddings zero para o batch
        return [[0.0] * _EMBEDDING_DIM] * len(texts)


async def cache_embedding(cache_key: str, embedding: list[float], ttl: int = 3600) -> None:
    """
    Cacheia embedding no Redis.

    Args:
        cache_key: Chave do cache.
        embedding: Embedding para cachear.
        ttl: Time-to-live em segundos (default 1 hora).
    """
    try:
        import redis as redis_lib
        import json

        redis_client = redis_lib.from_url(settings.redis_url, decode_responses=True)
        redis_client.setex(cache_key, ttl, json.dumps(embedding))
        logger.debug("Embedding cacheado: %s", cache_key)
    except Exception as e:
        logger.warning("Falha ao cachear embedding: %s", e)


async def get_cached_embedding(cache_key: str) -> list[float] | None:
    """
    Recupera embedding do cache.

    Args:
        cache_key: Chave do cache.

    Returns:
        Embedding se encontrado, None caso contrário.
    """
    try:
        import redis as redis_lib
        import json

        redis_client = redis_lib.from_url(settings.redis_url, decode_responses=True)
        cached = redis_client.get(cache_key)
        if cached:
            embedding = json.loads(cached)
            logger.debug("Embedding recuperado do cache: %s", cache_key)
            return embedding
    except Exception as e:
        logger.warning("Falha ao recuperar embedding do cache: %s", e)
    return None


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """
    Calcula similaridade de cosseno entre dois embeddings.

    Args:
        a: Primeiro embedding.
        b: Segundo embedding.

    Returns:
        Similaridade entre 0 e 1.
    """
    if len(a) != len(b):
        raise ValueError("Embeddings devem ter o mesmo tamanho.")

    dot_product = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(y * y for y in b) ** 0.5

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot_product / (norm_a * norm_b)
