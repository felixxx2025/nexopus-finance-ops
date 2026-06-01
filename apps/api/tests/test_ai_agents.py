"""
Testes para os agentes de IA: github_ai_client, agent_parser,
agent_classifier e agent_generator.

Todos os testes usam mocks para não fazer chamadas reais à API GitHub.
Os testes são organizados por módulo e cobrem:
  - Caminhos felizes (happy path)
  - Tratamento de erros (malformed JSON, HTTP errors, retry)
  - Validação de schema de saída
  - Lógica de partida dobrada
"""
from __future__ import annotations

import json
import os
import tempfile
import uuid
from decimal import Decimal
from unittest.mock import MagicMock, patch, AsyncMock

import pytest

# ── Fixtures de dados ─────────────────────────────────────────────────────────

PARSED_DATA_FIXTURE = {
    "empresa": {"nome": "Empresa Teste LTDA", "cnpj": "11222333000181"},
    "periodo": {"data_inicio": "2026-01-01", "data_fim": "2026-03-31"},
    "lancamentos": [
        {
            "data": "2026-01-15",
            "descricao": "Receita de Serviços de TI",
            "valor": 50000.0,
            "tipo": "receita",
            "conta_sugerida": "Receita de Serviços",
        },
        {
            "data": "2026-01-20",
            "descricao": "Aluguel do escritório",
            "valor": 5000.0,
            "tipo": "despesa",
            "conta_sugerida": "Despesas com Aluguéis",
        },
        {
            "data": "2026-02-01",
            "descricao": "Folha de pagamento",
            "valor": 20000.0,
            "tipo": "despesa",
            "conta_sugerida": "Despesas com Pessoal",
        },
    ],
    "moeda": "BRL",
    "confianca": 0.92,
}

CLASSIFIED_DATA_FIXTURE = {
    **PARSED_DATA_FIXTURE,
    "lancamentos": [
        {
            **PARSED_DATA_FIXTURE["lancamentos"][0],
            "tipo_conta": "receita",
            "codigo_conta": "3.1.1.01.01",
            "grupo_dre": "receita_bruta",
            "natureza": "credora",
        },
        {
            **PARSED_DATA_FIXTURE["lancamentos"][1],
            "tipo_conta": "despesa",
            "codigo_conta": "6.1.2.01.01",
            "grupo_dre": "despesa_operacional",
            "natureza": "devedora",
        },
        {
            **PARSED_DATA_FIXTURE["lancamentos"][2],
            "tipo_conta": "despesa",
            "codigo_conta": "6.1.1.01.01",
            "grupo_dre": "despesa_operacional",
            "natureza": "devedora",
        },
    ],
}


# ══════════════════════════════════════════════════════════════════════════════
# github_ai_client
# ══════════════════════════════════════════════════════════════════════════════

class TestGitHubAIClient:

    def test_get_token_from_env(self, monkeypatch):
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_test_token_123")
        from services.ai_engine import github_ai_client
        token = github_ai_client._get_token()
        assert token == "ghp_test_token_123"

    def test_get_token_raises_without_env_or_gh(self, monkeypatch):
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        with patch("subprocess.run", side_effect=Exception("gh not found")):
            from services.ai_engine import github_ai_client
            with pytest.raises(RuntimeError, match="GITHUB_TOKEN"):
                github_ai_client._get_token()

    def test_chat_completion_success(self, monkeypatch):
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_test")
        mock_response = {
            "choices": [{"message": {"content": "Resposta do modelo"}}]
        }
        from services.ai_engine import github_ai_client
        with patch.object(github_ai_client, "_retry_request", return_value=mock_response):
            result = github_ai_client.chat_completion(
                messages=[{"role": "user", "content": "Olá"}],
                model="gpt-5.2",
            )
        assert result == "Resposta do modelo"

    def test_chat_completion_bad_response_raises(self, monkeypatch):
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_test")
        from services.ai_engine import github_ai_client
        with patch.object(github_ai_client, "_retry_request", return_value={"invalid": True}):
            with pytest.raises(RuntimeError, match="Resposta inesperada"):
                github_ai_client.chat_completion(
                    messages=[{"role": "user", "content": "Olá"}],
                    model="gpt-5.2",
                )

    @pytest.mark.asyncio
    async def test_embed_success(self, monkeypatch):
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_test")
        mock_response = {
            "data": [
                {"index": 0, "embedding": [0.1, 0.2, 0.3]},
                {"index": 1, "embedding": [0.4, 0.5, 0.6]},
            ]
        }
        from services.ai_engine import github_ai_client
        with patch.object(github_ai_client, "_retry_request", AsyncMock(return_value=mock_response)):
            result = await github_ai_client.embed(["texto1", "texto2"])
        assert len(result) == 2
        assert result[0] == [0.1, 0.2, 0.3]
        assert result[1] == [0.4, 0.5, 0.6]

    @pytest.mark.asyncio
    async def test_embed_sorted_by_index(self, monkeypatch):
        """Garante que embeddings são retornados na ordem correta independente da API."""
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_test")
        mock_response = {
            "data": [
                {"index": 1, "embedding": [0.4, 0.5]},
                {"index": 0, "embedding": [0.1, 0.2]},
            ]
        }
        from services.ai_engine import github_ai_client
        with patch.object(github_ai_client, "_retry_request", AsyncMock(return_value=mock_response)):
            result = await github_ai_client.embed(["a", "b"])
        assert result[0] == [0.1, 0.2]
        assert result[1] == [0.4, 0.5]

    def test_retry_on_rate_limit(self, monkeypatch):
        """Verifica que 429 dispara retry com sleep."""
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_test")
        import httpx
        from services.ai_engine import github_ai_client

        call_count = 0

        def fake_request(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            mock_resp = MagicMock()
            if call_count < 3:
                mock_resp.status_code = 429
                mock_resp.headers = {"retry-after": "0"}
            else:
                mock_resp.status_code = 200
                mock_resp.json.return_value = {
                    "choices": [{"message": {"content": "ok"}}]
                }
            return mock_resp

        with patch("httpx.Client") as mock_client_cls:
            mock_client_cls.return_value.__enter__.return_value.request.side_effect = fake_request
            with patch("time.sleep"):
                result = github_ai_client.chat_completion(
                    messages=[{"role": "user", "content": "test"}],
                    model="gpt-5.2",
                    max_retries=3,
                )
        assert result == "ok"
        assert call_count == 3

    def test_raises_after_max_retries(self, monkeypatch):
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_test")
        from services.ai_engine import github_ai_client

        def fake_request(*args, **kwargs):
            mock_resp = MagicMock()
            mock_resp.status_code = 500
            return mock_resp

        with patch("httpx.Client") as mock_client_cls:
            mock_client_cls.return_value.__enter__.return_value.request.side_effect = fake_request
            with patch("time.sleep"):
                with pytest.raises(RuntimeError, match="GitHub AI falhou após"):
                    github_ai_client.chat_completion(
                        messages=[{"role": "user", "content": "test"}],
                        model="gpt-5.2",
                        max_retries=2,
                    )

    def test_raises_on_4xx(self, monkeypatch):
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_test")
        from services.ai_engine import github_ai_client

        def fake_request(*args, **kwargs):
            mock_resp = MagicMock()
            mock_resp.status_code = 403
            mock_resp.json.return_value = {"error": {"message": "sem permissão"}}
            return mock_resp

        with patch("httpx.Client") as mock_client_cls:
            mock_client_cls.return_value.__enter__.return_value.request.side_effect = fake_request
            with pytest.raises(RuntimeError, match="HTTP 403"):
                github_ai_client.chat_completion(
                    messages=[],
                    model="gpt-5.2",
                )


# ══════════════════════════════════════════════════════════════════════════════
# agent_parser
# ══════════════════════════════════════════════════════════════════════════════

class TestAgentParser:

    def test_parse_txt_file(self, tmp_path, monkeypatch):
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_test")
        txt = tmp_path / "extrato.txt"
        txt.write_text(
            "Empresa: Teste LTDA\nCNPJ: 11.222.333/0001-81\n"
            "01/01/2026 - Receita de Serviços - R$ 50.000,00\n"
            "15/01/2026 - Aluguel - R$ 5.000,00\n",
            encoding="utf-8",
        )

        from services.ai_engine import agent_parser

        mock_llm_response = json.dumps({
            "empresa": {"nome": "Teste LTDA", "cnpj": "11222333000181"},
            "periodo": {"data_inicio": "2026-01-01", "data_fim": "2026-01-31"},
            "lancamentos": [
                {"data": "2026-01-01", "descricao": "Receita", "valor": 50000, "tipo": "receita", "conta_sugerida": "Receita de Serviços"},
                {"data": "2026-01-15", "descricao": "Aluguel", "valor": 5000, "tipo": "despesa", "conta_sugerida": "Aluguéis"},
            ],
            "moeda": "BRL",
            "confianca": 0.9,
        })

        with patch.object(agent_parser, "chat_completion", return_value=mock_llm_response):
            result = agent_parser.parse_document(str(txt))

        assert result["empresa"]["cnpj"] == "11222333000181"
        assert len(result["lancamentos"]) == 2
        assert result["lancamentos"][0]["tipo"] == "receita"
        assert result["lancamentos"][1]["tipo"] == "despesa"
        assert result["moeda"] == "BRL"
        assert isinstance(result["confianca"], float)

    def test_parse_handles_markdown_fences(self, tmp_path, monkeypatch):
        """Parser deve tolerar resposta com ```json ... ``` do modelo."""
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_test")
        txt = tmp_path / "doc.txt"
        txt.write_text("Receita: R$1000", encoding="utf-8")

        from services.ai_engine import agent_parser

        mock_response_with_fences = (
            "```json\n"
            + json.dumps({
                "empresa": {"nome": "X", "cnpj": ""},
                "periodo": {"data_inicio": None, "data_fim": None},
                "lancamentos": [{"data": None, "descricao": "Receita", "valor": 1000, "tipo": "receita", "conta_sugerida": ""}],
                "moeda": "BRL",
                "confianca": 0.7,
            })
            + "\n```"
        )

        with patch.object(agent_parser, "chat_completion", return_value=mock_response_with_fences):
            result = agent_parser.parse_document(str(txt))

        assert len(result["lancamentos"]) == 1

    def test_parse_uses_fallback_on_invalid_json(self, tmp_path, monkeypatch):
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_test")
        txt = tmp_path / "doc.txt"
        txt.write_text("dados", encoding="utf-8")

        from services.ai_engine import agent_parser

        with patch.object(agent_parser, "chat_completion", return_value="texto inválido sem json"):
            result = agent_parser.parse_document(str(txt))
            # Deve usar fallback em vez de levantar exceção
            assert "_ai_control" in result
            assert result["_ai_control"]["decision"] == "reject"

    def test_parse_raises_on_unsupported_extension(self, tmp_path, monkeypatch):
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_test")
        f = tmp_path / "planilha.xlsx"
        f.write_bytes(b"fake")

        from services.ai_engine import agent_parser
        with pytest.raises(NotImplementedError, match="Excel"):
            agent_parser.parse_document(str(f))

    def test_validate_structure_normalizes_missing_fields(self):
        from services.ai_engine import agent_parser

        raw = {}
        result = agent_parser._validate_structure(raw)

        assert result["empresa"] == {"nome": "", "cnpj": ""}
        assert result["periodo"] == {"data_inicio": None, "data_fim": None}
        assert result["lancamentos"] == []
        assert result["moeda"] == "BRL"
        assert result["confianca"] == 0.0

    def test_validate_structure_clamps_tipo(self):
        from services.ai_engine import agent_parser

        raw = {
            "empresa": {"nome": "X", "cnpj": ""},
            "periodo": {},
            "lancamentos": [
                {"data": None, "descricao": "item", "valor": 100, "tipo": "INVALIDO", "conta_sugerida": ""},
            ],
        }
        result = agent_parser._validate_structure(raw)
        assert result["lancamentos"][0]["tipo"] == "neutro"

    def test_truncate_long_text(self):
        from services.ai_engine import agent_parser

        long_text = "a" * 20_000
        truncated = agent_parser._truncate(long_text)
        assert len(truncated) <= agent_parser._MAX_TEXT_CHARS + 50
        assert "TRUNCADO" in truncated

    def test_parse_normalizes_negative_valor(self, tmp_path, monkeypatch):
        """Valores negativos devem ser convertidos para positivos."""
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_test")
        txt = tmp_path / "doc.txt"
        txt.write_text("dados", encoding="utf-8")

        from services.ai_engine import agent_parser

        mock_response = json.dumps({
            "empresa": {"nome": "X", "cnpj": ""},
            "periodo": {},
            "lancamentos": [
                {"data": None, "descricao": "Despesa", "valor": -1500.0, "tipo": "despesa", "conta_sugerida": ""},
            ],
            "moeda": "BRL",
            "confianca": 0.8,
        })

        with patch.object(agent_parser, "chat_completion", return_value=mock_response):
            result = agent_parser.parse_document(str(txt))

        assert result["lancamentos"][0]["valor"] == 1500.0


# ══════════════════════════════════════════════════════════════════════════════
# agent_classifier
# ══════════════════════════════════════════════════════════════════════════════

class TestAgentClassifier:

    def test_classify_accounts_happy_path(self, monkeypatch):
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_test")
        from services.ai_engine import agent_classifier

        classified_response = json.dumps({
            "lancamentos": [
                {
                    **PARSED_DATA_FIXTURE["lancamentos"][0],
                    "tipo_conta": "receita",
                    "codigo_conta": "3.1.1",
                    "grupo_dre": "receita_bruta",
                    "natureza": "credora",
                },
            ]
        })

        data = {**PARSED_DATA_FIXTURE, "lancamentos": [PARSED_DATA_FIXTURE["lancamentos"][0]]}
        with patch.object(agent_classifier, "chat_completion", return_value=classified_response):
            result = agent_classifier.classify_accounts(data)

        assert len(result["lancamentos"]) == 1
        assert result["lancamentos"][0]["tipo_conta"] == "receita"
        assert result["lancamentos"][0]["grupo_dre"] == "receita_bruta"
        assert result["lancamentos"][0]["natureza"] == "credora"

    def test_classify_preserves_original_on_bad_json(self, monkeypatch):
        """Se o LLM retornar JSON inválido, deve retornar os originais."""
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_test")
        from services.ai_engine import agent_classifier

        original_entries = [PARSED_DATA_FIXTURE["lancamentos"][0]]
        data = {**PARSED_DATA_FIXTURE, "lancamentos": original_entries}

        with patch.object(agent_classifier, "chat_completion", return_value="não é json"):
            result = agent_classifier.classify_accounts(data)

        assert result["lancamentos"] == original_entries

    def test_classify_empty_lancamentos(self, monkeypatch):
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_test")
        from services.ai_engine import agent_classifier

        data = {**PARSED_DATA_FIXTURE, "lancamentos": []}
        result = agent_classifier.classify_accounts(data)
        assert result["lancamentos"] == []

    def test_classify_batches_large_input(self, monkeypatch):
        """Com mais de _BATCH_SIZE lançamentos, deve fazer múltiplas chamadas."""
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_test")
        from services.ai_engine import agent_classifier

        # 25 lançamentos (batch_size = 20 → 2 chamadas)
        entries = [
            {"data": "2026-01-01", "descricao": f"Item {i}", "valor": float(i * 100),
             "tipo": "despesa", "conta_sugerida": "Diversas"}
            for i in range(25)
        ]
        data = {**PARSED_DATA_FIXTURE, "lancamentos": entries}

        call_count = 0

        def mock_chat(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            # Retorna os mesmos entries passados com tipo_conta adicionado
            msgs = kwargs.get("messages") or args[0]
            user_content = msgs[-1]["content"]
            batch = json.loads(user_content.split("\n\n", 1)[1])["lancamentos"]
            classified = [
                {**e, "tipo_conta": "despesa", "codigo_conta": "6.x", "grupo_dre": "despesa_operacional", "natureza": "devedora"}
                for e in batch
            ]
            return json.dumps({"lancamentos": classified})

        with patch.object(agent_classifier, "chat_completion", side_effect=mock_chat):
            result = agent_classifier.classify_accounts(data)

        assert call_count == 2  # ceil(25/20) = 2
        assert len(result["lancamentos"]) == 25

    def test_classify_preserves_original_fields(self, monkeypatch):
        """Campos originais do parser devem sobreviver à classificação."""
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_test")
        from services.ai_engine import agent_classifier

        entry = PARSED_DATA_FIXTURE["lancamentos"][0].copy()
        data = {**PARSED_DATA_FIXTURE, "lancamentos": [entry]}

        classified_response = json.dumps({
            "lancamentos": [{
                **entry,
                "tipo_conta": "receita",
                "codigo_conta": "3.1",
                "grupo_dre": "receita_bruta",
                "natureza": "credora",
            }]
        })

        with patch.object(agent_classifier, "chat_completion", return_value=classified_response):
            result = agent_classifier.classify_accounts(data)

        l = result["lancamentos"][0]
        assert l["descricao"] == entry["descricao"]
        assert l["valor"] == entry["valor"]
        assert l["tipo"] == entry["tipo"]


# ══════════════════════════════════════════════════════════════════════════════
# agent_generator
# ══════════════════════════════════════════════════════════════════════════════

class TestAgentGenerator:

    def test_generate_entries_creates_double_entry(self, monkeypatch):
        """Para cada lançamento, deve existir exatamente 1 débito e 1 crédito de igual valor."""
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_test")
        from services.ai_engine import agent_generator

        narrativa_mock = "A empresa apresentou resultado positivo no período."

        with patch.object(agent_generator, "chat_completion", return_value=narrativa_mock):
            entries = agent_generator.generate_entries(CLASSIFIED_DATA_FIXTURE)

        assert len(entries) == 3

        for entry in entries:
            items = entry["items"]
            assert len(items) == 2, "Cada lançamento deve ter exatamente 2 items"

            debits = [i for i in items if i["type"] == "debit"]
            credits = [i for i in items if i["type"] == "credit"]
            assert len(debits) == 1, "Deve haver exatamente 1 débito por lançamento"
            assert len(credits) == 1, "Deve haver exatamente 1 crédito por lançamento"
            assert debits[0]["amount"] == credits[0]["amount"], "Débito deve igualar crédito"

    def test_receita_has_credit_principal(self, monkeypatch):
        """Conta de receita (credora): lado principal = credit."""
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_test")
        from services.ai_engine import agent_generator

        data = {
            **CLASSIFIED_DATA_FIXTURE,
            "lancamentos": [CLASSIFIED_DATA_FIXTURE["lancamentos"][0]],  # receita
        }

        with patch.object(agent_generator, "chat_completion", return_value="narrativa"):
            entries = agent_generator.generate_entries(data)

        items = entries[0]["items"]
        conta_principal = items[0]
        assert conta_principal["type"] == "credit"
        assert conta_principal["account"] == "Receita de Serviços"

    def test_despesa_has_debit_principal(self, monkeypatch):
        """Conta de despesa (devedora): lado principal = debit."""
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_test")
        from services.ai_engine import agent_generator

        data = {
            **CLASSIFIED_DATA_FIXTURE,
            "lancamentos": [CLASSIFIED_DATA_FIXTURE["lancamentos"][1]],  # despesa
        }

        with patch.object(agent_generator, "chat_completion", return_value="narrativa"):
            entries = agent_generator.generate_entries(data)

        items = entries[0]["items"]
        conta_principal = items[0]
        assert conta_principal["type"] == "debit"

    def test_generate_entries_empty_input(self, monkeypatch):
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_test")
        from services.ai_engine import agent_generator

        result = agent_generator.generate_entries({**CLASSIFIED_DATA_FIXTURE, "lancamentos": []})
        assert result == []

    def test_narrativa_attached_to_first_entry(self, monkeypatch):
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_test")
        from services.ai_engine import agent_generator

        narrativa = "Resultado financeiro positivo no 1T2026."
        with patch.object(agent_generator, "chat_completion", return_value=narrativa):
            entries = agent_generator.generate_entries(CLASSIFIED_DATA_FIXTURE)

        assert entries[0]["narrativa"] == narrativa
        assert "kpis" in entries[0]

    def test_narrativa_fallback_on_llm_error(self, monkeypatch):
        """Se o LLM falhar, deve retornar narrativa de fallback — não exceção."""
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_test")
        from services.ai_engine import agent_generator

        with patch.object(agent_generator, "chat_completion", side_effect=RuntimeError("API down")):
            entries = agent_generator.generate_entries(CLASSIFIED_DATA_FIXTURE)

        assert len(entries) == 3
        assert "narrativa" in entries[0]
        assert len(entries[0]["narrativa"]) > 10  # narrativa de fallback não é vazia

    def test_generate_ids_are_valid_uuids(self, monkeypatch):
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_test")
        from services.ai_engine import agent_generator

        with patch.object(agent_generator, "chat_completion", return_value="narrativa"):
            entries = agent_generator.generate_entries(CLASSIFIED_DATA_FIXTURE)

        for entry in entries:
            uuid.UUID(entry["journal_entry"]["id"])  # lança ValueError se inválido
            for item in entry["items"]:
                uuid.UUID(item["id"])
                uuid.UUID(item["entry_id"])

    def test_determine_dc_devedoras(self):
        from services.ai_engine.agent_generator import _determine_dc

        assert _determine_dc("ativo") == ("debit", "credit")
        assert _determine_dc("despesa") == ("debit", "credit")
        assert _determine_dc("ATIVO") == ("debit", "credit")

    def test_determine_dc_credoras(self):
        from services.ai_engine.agent_generator import _determine_dc

        assert _determine_dc("receita") == ("credit", "debit")
        assert _determine_dc("passivo") == ("credit", "debit")
        assert _determine_dc("pl") == ("credit", "debit")

    def test_valor_zero_does_not_raise(self, monkeypatch):
        """Lançamentos com valor 0 devem ser processados sem erro."""
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_test")
        from services.ai_engine import agent_generator

        data = {
            **CLASSIFIED_DATA_FIXTURE,
            "lancamentos": [{
                "data": "2026-01-01",
                "descricao": "Ajuste",
                "valor": 0,
                "tipo": "neutro",
                "conta_sugerida": "Ajustes",
                "tipo_conta": "despesa",
                "codigo_conta": "",
                "grupo_dre": "nao_aplicavel",
                "natureza": "devedora",
            }],
        }

        with patch.object(agent_generator, "chat_completion", return_value="narrativa"):
            entries = agent_generator.generate_entries(data)

        assert entries[0]["items"][0]["amount"] == 0.0
        assert entries[0]["items"][1]["amount"] == 0.0

    def test_kpis_calculation(self, monkeypatch):
        """KPIs devem refletir receita - despesa corretamente."""
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_test")
        from services.ai_engine import agent_generator

        with patch.object(agent_generator, "chat_completion", return_value="narrativa"):
            entries = agent_generator.generate_entries(CLASSIFIED_DATA_FIXTURE)

        kpis = entries[0]["kpis"]
        assert kpis["receita_total"] == 50000.0
        assert kpis["despesa_total"] == 25000.0  # 5000 + 20000
        assert kpis["resultado"] == 25000.0       # lucro


# ══════════════════════════════════════════════════════════════════════════════
# Integração leve: pipeline completo (parser → classifier → generator)
# ══════════════════════════════════════════════════════════════════════════════

class TestPipelineIntegration:

    def test_full_pipeline_produces_valid_entries(self, tmp_path, monkeypatch):
        """Simula o pipeline completo sem chamadas reais à API."""
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_test")

        txt = tmp_path / "extrato.txt"
        txt.write_text(
            "Empresa: NEXOPUS LTDA\nCNPJ: 12345678000195\n"
            "Receita de serviços: R$ 100.000,00\nDespesas operacionais: R$ 40.000,00",
            encoding="utf-8",
        )

        parser_response = json.dumps({
            "empresa": {"nome": "NEXOPUS LTDA", "cnpj": "12345678000195"},
            "periodo": {"data_inicio": "2026-01-01", "data_fim": "2026-03-31"},
            "lancamentos": [
                {"data": "2026-01-01", "descricao": "Receita", "valor": 100000.0, "tipo": "receita", "conta_sugerida": "Receita de Serviços"},
                {"data": "2026-01-31", "descricao": "Despesa", "valor": 40000.0, "tipo": "despesa", "conta_sugerida": "Despesas Operacionais"},
            ],
            "moeda": "BRL",
            "confianca": 0.95,
        })

        classifier_response = json.dumps({
            "lancamentos": [
                {"data": "2026-01-01", "descricao": "Receita", "valor": 100000.0, "tipo": "receita",
                 "conta_sugerida": "Receita de Serviços", "tipo_conta": "receita",
                 "codigo_conta": "3.1.1", "grupo_dre": "receita_bruta", "natureza": "credora"},
                {"data": "2026-01-31", "descricao": "Despesa", "valor": 40000.0, "tipo": "despesa",
                 "conta_sugerida": "Despesas Operacionais", "tipo_conta": "despesa",
                 "codigo_conta": "6.1.1", "grupo_dre": "despesa_operacional", "natureza": "devedora"},
            ]
        })

        narrativa = "NEXOPUS apresentou lucro de R$ 60.000,00 no período."

        from services.ai_engine import agent_classifier, agent_generator, agent_parser

        with patch.object(agent_parser, "chat_completion", return_value=parser_response):
            parsed = agent_parser.parse_document(str(txt))

        with patch.object(agent_classifier, "chat_completion", return_value=classifier_response):
            classified = agent_classifier.classify_accounts(parsed)

        with patch.object(agent_generator, "chat_completion", return_value=narrativa):
            entries = agent_generator.generate_entries(classified)

        # Validações do pipeline completo
        assert len(entries) == 2
        assert entries[0]["narrativa"] == narrativa
        assert entries[0]["kpis"]["receita_total"] == 100000.0
        assert entries[0]["kpis"]["despesa_total"] == 40000.0
        assert entries[0]["kpis"]["resultado"] == 60000.0

        # Valida partida dobrada em todos os lançamentos
        from services.compliance.rules import validate_double_entry
        for entry in entries:
            assert validate_double_entry(entry["items"]) is True
