"""
Agent Creative Local - Capacidade criativa sem dependência de APIs externas.

Usa templates e lógica local para gerar:
- Relatórios financeiros
- Insights
- Narrativas
- Recomendações
"""
from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


async def generate_financial_report_local(
    db: AsyncSession,
    data: dict[str, Any],
    report_type: str = "executive_summary",
) -> dict[str, Any]:
    """
    Gera um relatório financeiro usando templates locais.
    
    Args:
        db: Sessão do banco de dados.
        data: Dados financeiros.
        report_type: Tipo de relatório.
    
    Returns:
        Relatório gerado.
    """
    try:
        # Extrair dados
        dre = data.get("dre", {})
        balanco = data.get("balanco", {})
        
        # Template base
        report = f"""
# Relatório Financeiro - {report_type.replace('_', ' ').title()}
**Data:** {date.today().strftime('%d/%m/%Y')}

## Resumo Executivo
"""
        
        # Adicionar DRE se disponível
        if dre:
            receita = dre.get("receita_liquida", 0)
            lucro = dre.get("lucro_liquido", 0)
            margem = (lucro / receita * 100) if receita > 0 else 0
            
            report += f"""
### Demonstração do Resultado
- **Receita Líquida:** R$ {receita:,.2f}
- **Lucro Líquido:** R$ {lucro:,.2f}
- **Margem de Lucro:** {margem:.2f}%
"""
        
        # Adicionar Balanço se disponível
        if balanco:
            ativo = balanco.get("ativo_total", 0)
            passivo = balanco.get("passivo_total", 0)
            pl = balanco.get("patrimonio_liquido", 0)
            
            report += f"""
### Balanço Patrimonial
- **Ativo Total:** R$ {ativo:,.2f}
- **Passivo Total:** R$ {passivo:,.2f}
- **Patrimônio Líquido:** R$ {pl:,.2f}
"""
        
        # Adicionar análise
        report += """
## Análise de Desempenho
Este relatório foi gerado automaticamente pelo sistema Nexopus Finance Ops.
Para uma análise mais detalhada, consulte os relatórios completos ou solicite uma análise personalizada.

## Recomendações
- Revisar contas a receber para melhorar fluxo de caixa
- Analisar estrutura de custos para otimização
- Monitorar indicadores de rentabilidade mensalmente
"""
        
        return {
            "success": True,
            "report_type": report_type,
            "content": report,
            "generated_at": date.today().isoformat(),
            "method": "local_template",
        }
    except Exception as e:
        logger.error("Failed to generate financial report locally: %s", e)
        return {
            "success": False,
            "error": str(e),
        }


async def generate_insights_local(
    db: AsyncSession,
    data: dict[str, Any],
    focus_area: str = "general",
) -> dict[str, Any]:
    """
    Gera insights usando lógica local.
    
    Args:
        db: Sessão do banco de dados.
        data: Dados financeiros.
        focus_area: Área de foco.
    
    Returns:
        Insights gerados.
    """
    try:
        insights = []
        
        dre = data.get("dre", {})
        balanco = data.get("balanco", {})
        
        # Insight 1: Lucratividade
        if dre:
            receita = dre.get("receita_liquida", 0)
            lucro = dre.get("lucro_liquido", 0)
            margem = (lucro / receita * 100) if receita > 0 else 0
            
            if margem > 20:
                insights.append({
                    "observation": f"Margem de lucro de {margem:.1f}% está acima da média do setor",
                    "cause": "Eficiência operacional e controle de custos",
                    "impact": "Alta rentabilidade e capacidade de reinvestimento",
                    "recommendation": "Manter práticas atuais e considerar expansão",
                })
            elif margem > 10:
                insights.append({
                    "observation": f"Margem de lucro de {margem:.1f}% está na média",
                    "cause": "Operação estável com espaço para otimização",
                    "impact": "Rentabilidade moderada",
                    "recommendation": "Identificar oportunidades de redução de custos",
                })
            else:
                insights.append({
                    "observation": f"Margem de lucro de {margem:.1f}% está abaixo da média",
                    "cause": "Custos elevados ou precificação inadequada",
                    "impact": "Baixa rentabilidade e risco financeiro",
                    "recommendation": "Revisar estrutura de custos e estratégia de preços",
                })
        
        # Insight 2: Liquidez
        if balanco:
            ativo_circulante = balanco.get("ativo_circulante", 0)
            passivo_circulante = balanco.get("passivo_circulante", 0)
            liquidez = ativo_circulante / passivo_circulante if passivo_circulante > 0 else 0
            
            if liquidez > 1.5:
                insights.append({
                    "observation": f"Índice de liquidez de {liquidez:.2f} indica boa saúde financeira",
                    "cause": "Ativos circulantes suficientes para cobrir obrigações",
                    "impact": "Baixo risco de insolvência",
                    "recommendation": "Manter nível atual de liquidez",
                })
            elif liquidez > 1.0:
                insights.append({
                    "observation": f"Índice de liquidez de {liquidez:.2f} está adequado",
                    "cause": "Equilíbrio entre ativos e passivos circulantes",
                    "impact": "Risco moderado",
                    "recommendation": "Monitorar tendência de liquidez",
                })
            else:
                insights.append({
                    "observation": f"Índice de liquidez de {liquidez:.2f} indica risco",
                    "cause": "Passivos circulantes superam ativos circulantes",
                    "impact": "Alto risco de insolvência",
                    "recommendation": "Renegociar dívidas ou aumentar capital de giro",
                })
        
        return {
            "success": True,
            "focus_area": focus_area,
            "insights": insights,
            "generated_at": date.today().isoformat(),
            "method": "local_logic",
        }
    except Exception as e:
        logger.error("Failed to generate insights locally: %s", e)
        return {
            "success": False,
            "error": str(e),
        }


async def generate_narrative_local(
    db: AsyncSession,
    data: dict[str, Any],
    audience: str = "executives",
) -> dict[str, Any]:
    """
    Gera narrativa usando templates locais.
    
    Args:
        db: Sessão do banco de dados.
        data: Dados financeiros.
        audience: Público-alvo.
    
    Returns:
        Narrativa gerada.
    """
    try:
        dre = data.get("dre", {})
        balanco = data.get("balanco", {})
        
        # Narrativa base
        narrative = f"""
# Narrativa Financeira
**Público:** {audience}
**Data:** {date.today().strftime('%d/%m/%Y')}

## Contexto
A empresa apresentou desempenho financeiro no período analisado, com indicadores que refletem a situação atual do negócio.
"""
        
        # Adicionar DRE
        if dre:
            receita = dre.get("receita_liquida", 0)
            lucro = dre.get("lucro_liquido", 0)
            
            if lucro > 0:
                narrative += f"""
## Desempenho Operacional
A empresa gerou receita de R$ {receita:,.2f}, resultando em lucro líquido de R$ {lucro:,.2f}. Este resultado positivo demonstra a capacidade do negócio de gerar valor e sustentar suas operações.
"""
            else:
                narrative += f"""
## Desempenho Operacional
A empresa apresentou prejuízo de R$ {abs(lucro):,.2f} sobre receita de R$ {receita:,.2f}. Este cenário requer atenção imediata para reverter a tendência negativa.
"""
        
        # Adicionar Balanço
        if balanco:
            ativo = balanco.get("ativo_total", 0)
            pl = balanco.get("patrimonio_liquido", 0)
            
            narrative += f"""
## Estrutura Patrimonial
O ativo total da empresa é de R$ {ativo:,.2f}, com patrimônio líquido de R$ {pl:,.2f}. Esta estrutura indica a capacidade de investimento e solidez financeira da organização.
"""
        
        # Conclusão
        narrative += """
## Conclusão
Os dados apresentados refletem a situação financeira atual da empresa. Recomenda-se análise contínua dos indicadores para tomada de decisões estratégicas.
"""
        
        return {
            "success": True,
            "audience": audience,
            "narrative": narrative,
            "generated_at": date.today().isoformat(),
            "method": "local_template",
        }
    except Exception as e:
        logger.error("Failed to generate narrative locally: %s", e)
        return {
            "success": False,
            "error": str(e),
        }


async def generate_recommendations_local(
    db: AsyncSession,
    data: dict[str, Any],
    priority: str = "high_impact",
) -> dict[str, Any]:
    """
    Gera recomendações usando lógica local.
    
    Args:
        db: Sessão do banco de dados.
        data: Dados financeiros.
        priority: Prioridade.
    
    Returns:
        Recomendações geradas.
    """
    try:
        recommendations = []
        
        dre = data.get("dre", {})
        balanco = data.get("balanco", {})
        
        # Recomendação 1: Gestão de Caixa
        recommendations.append({
            "title": "Implementar gestão de caixa eficiente",
            "description": "Estabelecer previsão de fluxo de caixa semanal e manter reserva de emergência equivalente a 3 meses de despesas operacionais.",
            "benefit": "Redução de risco de insolvência e melhor planejamento financeiro",
            "effort": "Médio",
            "timeline": "1-2 meses",
            "risk": "Baixo",
        })
        
        # Recomendação 2: Análise de Custos
        if dre:
            custo = dre.get("custo_produtos_vendidos", 0)
            receita = dre.get("receita_liquida", 0)
            margem_custo = (custo / receita * 100) if receita > 0 else 0
            
            if margem_custo > 70:
                recommendations.append({
                    "title": "Otimizar estrutura de custos",
                    "description": f"Custos representam {margem_custo:.1f}% da receita. Revisar fornecedores, negociar melhores condições e identificar ineficiências operacionais.",
                    "benefit": "Aumento de margem e competitividade",
                    "effort": "Alto",
                    "timeline": "3-6 meses",
                    "risk": "Médio",
                })
        
        # Recomendação 3: Diversificação
        recommendations.append({
            "title": "Diversificar fontes de receita",
            "description": "Explorar novos mercados, produtos ou serviços para reduzir dependência de uma única fonte de receita.",
            "benefit": "Redução de risco e aumento de potencial de crescimento",
            "effort": "Alto",
            "timeline": "6-12 meses",
            "risk": "Médio",
        })
        
        return {
            "success": True,
            "priority": priority,
            "recommendations": recommendations,
            "generated_at": date.today().isoformat(),
            "method": "local_logic",
        }
    except Exception as e:
        logger.error("Failed to generate recommendations locally: %s", e)
        return {
            "success": False,
            "error": str(e),
        }
