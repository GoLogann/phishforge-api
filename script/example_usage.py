#!/usr/bin/env python3
"""
Script de exemplo mostrando como usar o novo sistema de avaliação RAGAS.

Este script demonstra como:
1. Gerar um email via API
2. Capturar os dados necessários
3. Executar avaliação RAGAS standalone
4. Consultar resultados
"""

import asyncio
import json
import logging
from pathlib import Path

import requests

# Configuração básica de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configurações
API_BASE_URL = "http://localhost:8000"
SCRIPT_DIR = Path(__file__).parent


async def example_complete_workflow():
    """Exemplo de workflow completo: geração + avaliação."""
    
    logger.info("=== EXEMPLO DE WORKFLOW COMPLETO ===")
    
    # 1. Gerar email via API
    logger.info("1. Gerando email via API...")
    
    generation_request = {
        "user_context": "Gere um email de phishing simulando um banco solicitando atualização de dados urgente",
        "difficulty": "medio"
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/generate",
            json=generation_request,
            timeout=60
        )
        response.raise_for_status()
        email_data = response.json()
        
        logger.info(f"Email gerado com ID: {email_data['id']}")
        logger.info(f"Assunto: {email_data['assunto']}")
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Erro ao gerar email: {e}")
        return
    
    # 2. Simular dados que seriam capturados do pipeline RAG
    # (Em uma implementação real, estes dados viriam dos logs ou seriam passados pelo endpoint)
    logger.info("2. Preparando dados para avaliação...")
    
    evaluation_data = {
        "email_id": email_data["id"],
        "user_context": generation_request["user_context"],
        "search_query": "phishing bancário atualização dados credenciais urgente",
        "generation_context": "email phishing banco falso solicitar dados pessoais urgente",
        "difficulty": generation_request["difficulty"],
        "hyde_context": "Um email de phishing bancário típico incluiria elementos como urgência para atualização de dados, solicitação de informações pessoais, links suspeitos e uso de logos bancários falsificados para enganar a vítima.",
        "fused_context": "Técnicas de phishing bancário: uso de logos oficiais falsificados, criação de senso de urgência (conta será bloqueada), solicitação de dados confidenciais via email, links para sites falsos que imitam o banco real, uso de linguagem formal para parecer legítimo, pressão temporal para ação imediata."
    }
    
    # 3. Criar arquivo temporário para avaliação
    logger.info("3. Criando arquivo de avaliação...")
    
    batch_file = SCRIPT_DIR / "temp_evaluation.json"
    batch_data = {
        "description": f"Avaliação automática do email {email_data['id']}",
        "evaluations": [evaluation_data]
    }
    
    with open(batch_file, 'w', encoding='utf-8') as f:
        json.dump(batch_data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Arquivo criado: {batch_file}")
    
    # 4. Executar avaliação (simulado - em produção executaria o script)
    logger.info("4. Para executar a avaliação, use:")
    logger.info(f"python {SCRIPT_DIR}/evaluate_ragas.py --batch-file {batch_file}")
    
    # 5. Exemplo de consulta SQL que seria executada após a avaliação
    logger.info("5. Após a avaliação, consulte os resultados com:")
    print(f"""
    -- Consultar métricas do email gerado
    SELECT 
        e.email_id,
        e.difficulty,
        e.status,
        m.metric_name,
        m.metric_value,
        m.metric_category
    FROM ragas_evaluations e
    LEFT JOIN ragas_metrics m ON e.id = m.evaluation_id
    WHERE e.email_id = '{email_data['id']}';
    
    -- Ver documentos recuperados
    SELECT 
        d.document_order,
        d.similarity_score,
        d.rerank_score,
        LEFT(d.document_text, 100) as preview
    FROM ragas_evaluations e
    JOIN evaluation_retrieved_documents d ON e.id = d.evaluation_id
    WHERE e.email_id = '{email_data['id']}'
    ORDER BY d.document_order;
    """)
    
    logger.info("=== WORKFLOW COMPLETO ===")


def example_batch_evaluation():
    """Exemplo de como criar um arquivo de avaliação em lote."""
    
    logger.info("=== EXEMPLO DE AVALIAÇÃO EM LOTE ===")
    
    # IDs de exemplo (substitua por IDs reais)
    example_emails = [
        "123e4567-e89b-12d3-a456-426614174000",
        "234e4567-e89b-12d3-a456-426614174001",
        "345e4567-e89b-12d3-a456-426614174002"
    ]
    
    batch_evaluations = []
    
    contexts = [
        {
            "user_context": "Gere um email de phishing simulando uma mensagem de um banco",
            "search_query": "phishing bancário atualização dados credenciais",
            "generation_context": "email phishing banco falso solicitar dados pessoais",
            "difficulty": "medio",
            "hyde_context": "Phishing bancário com solicitação urgente de atualização.",
            "fused_context": "Técnicas de phishing bancário: urgência, logos falsos, links suspeitos."
        },
        {
            "user_context": "Crie um phishing de e-commerce fingindo ser uma promoção",
            "search_query": "phishing e-commerce promoção falsa desconto",
            "generation_context": "email phishing loja online promoção fake",
            "difficulty": "baixo",
            "hyde_context": "Phishing de e-commerce com oferta irresistível.",
            "fused_context": "Táticas de e-commerce: descontos impossíveis, pressão temporal, links falsos."
        },
        {
            "user_context": "Desenvolva um phishing avançado simulando notificação de segurança",
            "search_query": "phishing segurança notificação breach violação",
            "generation_context": "email phishing sofisticado alerta segurança",
            "difficulty": "alto",
            "hyde_context": "Phishing avançado simulando alerta de segurança legítimo.",
            "fused_context": "Phishing de segurança: terminologia técnica, CVEs, alertas falsos."
        }
    ]
    
    for email_id, context in zip(example_emails, contexts):
        evaluation = {
            "email_id": email_id,
            **context
        }
        batch_evaluations.append(evaluation)
    
    batch_file = SCRIPT_DIR / "batch_evaluation_example.json"
    batch_data = {
        "description": "Exemplo de avaliação em lote - múltiplos tipos de phishing",
        "created_at": "2025-11-06T12:00:00Z",
        "evaluations": batch_evaluations
    }
    
    with open(batch_file, 'w', encoding='utf-8') as f:
        json.dump(batch_data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Arquivo de lote criado: {batch_file}")
    logger.info(f"Para executar: python {SCRIPT_DIR}/evaluate_ragas.py --batch-file {batch_file}")
    
    logger.info("=== AVALIAÇÃO EM LOTE ===")


def example_analysis_queries():
    """Exemplos de consultas para análise dos resultados."""
    
    logger.info("=== EXEMPLOS DE CONSULTAS DE ANÁLISE ===")
    
    queries = [
        ("Métricas por nível de dificuldade", """
        SELECT 
            e.difficulty,
            m.metric_name,
            AVG(m.metric_value) as avg_value,
            MIN(m.metric_value) as min_value,
            MAX(m.metric_value) as max_value,
            COUNT(*) as sample_count
        FROM ragas_evaluations e
        JOIN ragas_metrics m ON e.id = m.evaluation_id
        WHERE e.status = 'completed'
        GROUP BY e.difficulty, m.metric_name
        ORDER BY e.difficulty, m.metric_name;
        """),
        
        ("Performance de sessões", """
        SELECT 
            session_name,
            status,
            total_evaluations,
            successful_evaluations,
            success_rate_percent,
            duration_seconds / 60.0 as duration_minutes
        FROM session_performance_overview
        ORDER BY started_at DESC;
        """),
        
        ("Correlação entre métricas", """
        SELECT 
            e.email_id,
            e.difficulty,
            MAX(CASE WHEN m.metric_name = 'faithfulness' THEN m.metric_value END) as faithfulness,
            MAX(CASE WHEN m.metric_name = 'answer_relevancy' THEN m.metric_value END) as answer_relevancy,
            MAX(CASE WHEN m.metric_name = 'context_precision' THEN m.metric_value END) as context_precision,
            MAX(CASE WHEN m.metric_name = 'context_recall' THEN m.metric_value END) as context_recall
        FROM ragas_evaluations e
        JOIN ragas_metrics m ON e.id = m.evaluation_id
        WHERE e.status = 'completed'
        GROUP BY e.email_id, e.difficulty;
        """),
        
        ("Evolução temporal das métricas", """
        SELECT 
            DATE(e.created_at) as evaluation_date,
            m.metric_name,
            AVG(m.metric_value) as daily_avg,
            COUNT(*) as daily_count
        FROM ragas_evaluations e
        JOIN ragas_metrics m ON e.id = m.evaluation_id
        WHERE e.status = 'completed'
          AND e.created_at >= CURRENT_DATE - INTERVAL '30 days'
        GROUP BY DATE(e.created_at), m.metric_name
        ORDER BY evaluation_date DESC, m.metric_name;
        """)
    ]
    
    for title, query in queries:
        print(f"\n-- {title}")
        print(query)
    
    logger.info("=== CONSULTAS DE ANÁLISE ===")


def main():
    """Função principal com menu interativo."""
    
    print("\n=== SISTEMA DE AVALIAÇÃO RAGAS - EXEMPLOS ===")
    print("1. Workflow completo (geração + avaliação)")
    print("2. Criar arquivo de avaliação em lote")
    print("3. Mostrar consultas de análise")
    print("4. Executar todos os exemplos")
    print("0. Sair")
    
    try:
        choice = input("\nEscolha uma opção: ").strip()
        
        if choice == "1":
            asyncio.run(example_complete_workflow())
        elif choice == "2":
            example_batch_evaluation()
        elif choice == "3":
            example_analysis_queries()
        elif choice == "4":
            asyncio.run(example_complete_workflow())
            example_batch_evaluation()
            example_analysis_queries()
        elif choice == "0":
            print("Saindo...")
            return
        else:
            print("Opção inválida!")
            
    except KeyboardInterrupt:
        print("\nInterrompido pelo usuário.")
    except Exception as e:
        logger.error(f"Erro: {e}")


if __name__ == "__main__":
    main()