"""
AI Control — controle centralizado de confiança, fallback e log de decisão.

Responsabilidades:
- Avaliar score de confiança de resultados dos agentes IA
- Definir ação automática: AUTO_APPROVE, NEEDS_REVIEW, REJECT
- Registrar log de decisão auditável em cada operação
- Fornecer fallback seguro quando o score for baixo

Thresholds configuráveis via env:
  AI_AUTO_APPROVE_THRESHOLD  (default: 0.80)
  AI_NEEDS_REVIEW_THRESHOLD  (default: 0.50)
"""
from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)

# ── Thresholds ────────────────────────────────────────────────────────────────

_AUTO_APPROVE_THRESHOLD = float(os.getenv("AI_AUTO_APPROVE_THRESHOLD", "0.80"))
_NEEDS_REVIEW_THRESHOLD = float(os.getenv("AI_NEEDS_REVIEW_THRESHOLD", "0.50"))


class AIDecision(str, Enum):
    AUTO_APPROVE = "auto_approve"   # confiança ≥ _AUTO_APPROVE_THRESHOLD
    NEEDS_REVIEW = "needs_review"   # _NEEDS_REVIEW_THRESHOLD ≤ confiança < _AUTO_APPROVE_THRESHOLD
    REJECT = "reject"               # confiança < _NEEDS_REVIEW_THRESHOLD


# ── Decision Log ──────────────────────────────────────────────────────────────

class AIDecisionLog:
    """Representa um evento de decisão IA — gravado em audit_logs ou arquivo."""

    def __init__(
        self,
        agent: str,
        operation: str,
        confidence: float,
        decision: AIDecision,
        doc_id: Optional[str] = None,
        company_id: Optional[str] = None,
        payload_summary: Optional[dict] = None,
        reason: Optional[str] = None,
    ) -> None:
        self.id = str(uuid.uuid4())
        self.agent = agent
        self.operation = operation
        self.confidence = confidence
        self.decision = decision
        self.doc_id = doc_id
        self.company_id = company_id
        self.payload_summary = payload_summary or {}
        self.reason = reason
        self.ts = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "ts": self.ts,
            "agent": self.agent,
            "operation": self.operation,
            "confidence": self.confidence,
            "decision": self.decision.value,
            "doc_id": self.doc_id,
            "company_id": self.company_id,
            "payload_summary": self.payload_summary,
            "reason": self.reason,
        }

    def log(self) -> None:
        """Emite o log estruturado via logger (capturado pelo Loki/Promtail)."""
        level = (
            logging.INFO if self.decision == AIDecision.AUTO_APPROVE
            else logging.WARNING if self.decision == AIDecision.NEEDS_REVIEW
            else logging.ERROR
        )
        logger.log(level, "AI_DECISION %s", json.dumps(self.to_dict(), ensure_ascii=False))


# ── Controller ────────────────────────────────────────────────────────────────

class AIController:
    """
    Controla o fluxo de decisão de resultados de agentes IA.

    Uso:
        ctrl = AIController(agent="parser", operation="parse_document")
        result = ctrl.evaluate(
            confidence=0.75,
            result=structured_data,
            doc_id=doc_id,
        )
        if result.decision == AIDecision.REJECT:
            raise ValueError("IA com confiança muito baixa, documento não processado.")
    """

    def __init__(
        self,
        agent: str,
        operation: str,
        auto_approve_threshold: float = _AUTO_APPROVE_THRESHOLD,
        needs_review_threshold: float = _NEEDS_REVIEW_THRESHOLD,
    ) -> None:
        self.agent = agent
        self.operation = operation
        self.auto_approve_threshold = auto_approve_threshold
        self.needs_review_threshold = needs_review_threshold

    def evaluate(
        self,
        confidence: float,
        result: Any,
        doc_id: Optional[str] = None,
        company_id: Optional[str] = None,
        payload_summary: Optional[dict] = None,
    ) -> "AIEvalResult":
        """
        Avalia o resultado do agente e retorna um AIEvalResult com a decisão.

        Args:
            confidence: Score 0.0–1.0 retornado pelo agente.
            result: Dados gerados pelo agente (para passagem direta se aprovado).
            doc_id: UUID do documento associado (para log).
            company_id: UUID da empresa (para log).
            payload_summary: Resumo do payload para log (não envie dados sensíveis).

        Returns:
            AIEvalResult com decision, result e log.
        """
        if confidence >= self.auto_approve_threshold:
            decision = AIDecision.AUTO_APPROVE
            reason = f"Confiança {confidence:.2f} ≥ limiar auto-aprovação {self.auto_approve_threshold}"
        elif confidence >= self.needs_review_threshold:
            decision = AIDecision.NEEDS_REVIEW
            reason = (
                f"Confiança {confidence:.2f} entre {self.needs_review_threshold} e "
                f"{self.auto_approve_threshold} — revisão humana necessária"
            )
        else:
            decision = AIDecision.REJECT
            reason = (
                f"Confiança {confidence:.2f} < limiar mínimo {self.needs_review_threshold} — "
                "resultado descartado"
            )

        log = AIDecisionLog(
            agent=self.agent,
            operation=self.operation,
            confidence=confidence,
            decision=decision,
            doc_id=doc_id,
            company_id=company_id,
            payload_summary=payload_summary or {},
            reason=reason,
        )
        log.log()

        return AIEvalResult(decision=decision, result=result, log=log, reason=reason)

    def with_fallback(
        self,
        confidence: float,
        ai_result: Any,
        fallback_result: Any,
        doc_id: Optional[str] = None,
        company_id: Optional[str] = None,
    ) -> "AIEvalResult":
        """
        Avalia e retorna fallback quando a decisão for REJECT.

        Útil para garantir que o sistema sempre retorne um resultado utilizável,
        mesmo que seja o fallback (ex: resultado vazio estruturado).
        """
        eval_result = self.evaluate(
            confidence=confidence,
            result=ai_result,
            doc_id=doc_id,
            company_id=company_id,
        )
        if eval_result.decision == AIDecision.REJECT:
            logger.warning(
                "AI fallback ativado | agent=%s | confiança=%.2f | doc_id=%s",
                self.agent, confidence, doc_id,
            )
            eval_result.result = fallback_result
            eval_result.used_fallback = True
        return eval_result


class AIEvalResult:
    """Resultado da avaliação do AIController."""

    def __init__(
        self,
        decision: AIDecision,
        result: Any,
        log: AIDecisionLog,
        reason: str = "",
    ) -> None:
        self.decision = decision
        self.result = result
        self.log = log
        self.reason = reason
        self.used_fallback = False

    @property
    def requires_human_review(self) -> bool:
        return self.decision in (AIDecision.NEEDS_REVIEW, AIDecision.REJECT)

    @property
    def is_approved(self) -> bool:
        return self.decision == AIDecision.AUTO_APPROVE

    def to_dict(self) -> dict:
        return {
            "decision": self.decision.value,
            "confidence": self.log.confidence,
            "reason": self.reason,
            "used_fallback": self.used_fallback,
            "requires_human_review": self.requires_human_review,
            "log_id": self.log.id,
        }


# ── Fallbacks padrão ─────────────────────────────────────────────────────────

FALLBACK_PARSE_RESULT: dict = {
    "empresa": {"nome": "", "cnpj": ""},
    "periodo": {"data_inicio": None, "data_fim": None},
    "lancamentos": [],
    "moeda": "BRL",
    "confianca": 0.0,
    "_fallback": True,
}

FALLBACK_FORECAST_RESULT: dict = {
    "cenarios": {
        "base": {"receita_projetada": 0, "despesa_projetada": 0, "resultado_liquido": 0}
    },
    "tendencia_receita": "indisponivel",
    "tendencia_despesa": "indisponivel",
    "recomendacoes": ["Dados insuficientes para projeção confiável."],
    "confianca": 0.0,
    "_fallback": True,
}

FALLBACK_AUDIT_RESULT: dict = {
    "score_risco": 100,
    "nivel_risco": "indisponivel",
    "anomalias": [],
    "compliance": {"equacao_patrimonial": False, "partida_dobrada": False},
    "acoes_recomendadas": ["Auditoria automática indisponível — revisão manual necessária."],
    "resumo_executivo": "Não foi possível executar a auditoria automática.",
    "lancamentos_auditados": 0,
    "confianca": 0.0,
    "_fallback": True,
}
