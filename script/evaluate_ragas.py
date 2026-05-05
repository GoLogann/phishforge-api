#!/usr/bin/env python3
"""
Script standalone para execução de avaliações RAGAS.

Este script pode ser executado independentemente da API para processar
avaliações de emails de phishing usando o framework RAGAS.

Uso:
    python evaluate_ragas.py --help
    python evaluate_ragas.py --email-id UUID --user-context "contexto"
    python evaluate_ragas.py --session-id UUID
    python evaluate_ragas.py --batch-file evaluations.json
"""

import argparse
import asyncio
import json
import logging
import sys
import traceback
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Dict, Optional
from uuid import UUID

import asyncpg
from ragas.embeddings import BaseRagasEmbeddings
from ragas.llms import BaseRagasLLM

# Adiciona o diretório raiz ao path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.config import settings
from app.domain.models.evaluation import (CreateRagasEvaluationRequest,
                                          RagasEvaluation, RagasMetric)
from app.domain.services.evaluation import run_and_log_ragas_evaluation
from app.domain.services.response_generator import ResponseGenerator
from app.infra.database.connection import get_db_pool
from app.infra.database.repositories.evaluation_repository import \
    EvaluationRepository

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ragas_evaluation.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class RagasEvaluationService:
    """Serviço para executar avaliações RAGAS standalone."""
    
    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
        self.evaluation_repo = EvaluationRepository(db_pool)
        
        # TODO: Inicializar componentes RAGAS conforme configuração
        # Estes precisarão ser injetados ou configurados conforme o container atual
        self.eval_llm: Optional[BaseRagasLLM] = None
        self.eval_embeddings: Optional[BaseRagasEmbeddings] = None
        self.response_generator: Optional[ResponseGenerator] = None
    
    async def initialize_components(self):
        """Inicializa componentes necessários para avaliação."""
        logger.info("Inicializando componentes RAGAS...")
        
        try:
            # Inicializa response_generator
            self.response_generator = ResponseGenerator(
                api_key=settings.OPENAI_API_KEY,
                model_name=settings.MODEL_NAME_LLM
            )
            
            # Inicializa componentes RAGAS
            from langchain_openai import ChatOpenAI, OpenAIEmbeddings
            from ragas.embeddings import LangchainEmbeddingsWrapper
            from ragas.llms import LangchainLLMWrapper
            
            chat_model = ChatOpenAI(
                model="gpt-4o-mini",
                api_key=settings.OPENAI_API_KEY
            )
            
            embeddings_model = OpenAIEmbeddings(
                model="text-embedding-3-large",
                api_key=settings.OPENAI_API_KEY
            )
            
            self.eval_llm = LangchainLLMWrapper(langchain_llm=chat_model)
            self.eval_embeddings = LangchainEmbeddingsWrapper(embeddings=embeddings_model)
            
            logger.info("Componentes RAGAS inicializados com sucesso")
            
        except Exception as e:
            logger.error(f"Erro ao inicializar componentes RAGAS: {e}")
            raise

    async def _get_email_by_id(self, email_id: UUID):
        """Busca um email por ID diretamente do banco."""
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT id, receptor, remetente, assunto, conteudo, explicacao, 
                       nivel, categoria, links, created_at, updated_at
                FROM phishing_emails 
                WHERE id = $1
            """, email_id)
            
            if row:
                # Converte a row em um objeto simples com os atributos necessários
                class EmailData:
                    def __init__(self, row_data):
                        self.id = row_data['id']
                        self.receptor = row_data['receptor']
                        self.remetente = row_data['remetente']
                        self.assunto = row_data['assunto']
                        self.conteudo = row_data['conteudo']
                        self.explicacao = row_data['explicacao']
                        self.nivel = row_data['nivel']
                        self.categoria = row_data['categoria']
                        self.links = row_data['links']
                        self.created_at = row_data['created_at']
                        self.updated_at = row_data['updated_at']
                
                return EmailData(row)
            return None
    
    async def process_single_evaluation(self, request: CreateRagasEvaluationRequest) -> UUID:
        """Processa uma única avaliação RAGAS."""
        logger.info(f"Iniciando avaliação para email {request.email_id}")
        
        # 1. Cria registro de avaliação no banco
        evaluation = RagasEvaluation(
            session_id=request.session_id,
            email_id=request.email_id,
            user_context=request.user_context,
            search_query=request.search_query,
            generation_context=request.generation_context,
            difficulty=request.difficulty,
            hyde_context=request.hyde_context,
            fused_context=request.fused_context,
            status="running"
        )
        
        evaluation_id = await self.evaluation_repo.create_evaluation(evaluation)
        logger.info(f"Criado registro de avaliação {evaluation_id}")
        
        try:
            # 2. Busca o email gerado diretamente do banco
            email = await self._get_email_by_id(request.email_id)
            if not email:
                raise ValueError(f"Email {request.email_id} não encontrado")
            
            # 3. Preparação de respostas para RAGAS (em português primeiro)
            expanded_email_response_pt = (
                f"Email de Phishing - Nível {request.difficulty}\n\n"
                f"**Remetente:** {email.remetente}\n"
                f"**Assunto:** {email.assunto}\n\n"
                f"**Corpo do Email:**\n{email.conteudo}\n\n"
                f"**Técnicas Implementadas:**\n"
                f"{email.explicacao[:300]}..."
            )
            
            full_response_with_explanation_pt = (
                f"Assunto: {email.assunto}\n"
                f"Remetente: {email.remetente}\n\n"
                f"Corpo do E-mail:\n{email.conteudo}\n\n"
                f"---\n"
                f"Análise das Táticas (Explicação Completa):\n{email.explicacao}"
            )
            
            # 4. Salva as respostas em português
            await self.evaluation_repo.update_evaluation_translations(
                evaluation_id,
                expanded_email_response_pt,
                full_response_with_explanation_pt,
                "",  # expanded_en - será preenchido após tradução
                ""   # full_en - será preenchido após tradução
            )
            
            # 5. Tradução para inglês (necessário para RAGAS)
            if not self.response_generator:
                raise ValueError("ResponseGenerator não inicializado")
            
            logger.info("Iniciando tradução para inglês...")
            expanded_en = await self.response_generator.translate_to_english_with_enrichment(
                expanded_email_response_pt, 
                request.difficulty
            )
            full_en = await self.response_generator.translate_to_english_with_enrichment(
                full_response_with_explanation_pt,
                request.difficulty
            )
            
            if not expanded_en or not full_en:
                raise ValueError("Falha na tradução para inglês")
            
            # 6. Atualiza com traduções
            await self.evaluation_repo.update_evaluation_translations(
                evaluation_id,
                expanded_email_response_pt,
                full_response_with_explanation_pt,
                expanded_en,
                full_en
            )
            
            # 7. Verificar se há contexto para avaliação
            if not request.fused_context or not request.fused_context.strip():
                logger.warning("Contexto vazio - pulando avaliação RAGAS")
                await self.evaluation_repo.update_evaluation_status(
                    evaluation_id, "completed", "Contexto vazio - avaliação pulada"
                )
                return evaluation_id
            
            # 8. Executa avaliação RAGAS
            logger.info("Executando avaliação RAGAS...")
            metrics_result = await run_and_log_ragas_evaluation(
                search_question=request.search_query,
                generation_question=request.user_context,
                expanded_answer=expanded_en,
                full_answer=full_en,
                contexts=[request.fused_context],
                eval_llm=self.eval_llm,
                eval_embeddings=self.eval_embeddings,
            )
            
            # 9. Salva métricas no banco
            if metrics_result and isinstance(metrics_result, dict):
                metrics_to_save = []
                for metric_name, metric_value in metrics_result.items():
                    if isinstance(metric_value, (int, float)):
                        metric = RagasMetric(
                            evaluation_id=evaluation_id,
                            metric_name=metric_name,
                            metric_value=Decimal(str(metric_value)),
                            metric_category=self._get_metric_category(metric_name)
                        )
                        metrics_to_save.append(metric)
                
                if metrics_to_save:
                    await self.evaluation_repo.create_metrics_batch(metrics_to_save)
                    logger.info(f"Salvou {len(metrics_to_save)} métricas para avaliação {evaluation_id}")
            
            # 10. Marca como concluída
            await self.evaluation_repo.update_evaluation_status(evaluation_id, "completed")
            logger.info(f"Avaliação {evaluation_id} concluída com sucesso")
            
            return evaluation_id
            
        except Exception as e:
            logger.error(f"Erro na avaliação {evaluation_id}: {str(e)}")
            logger.error(f"Stack trace: {traceback.format_exc()}")
            
            await self.evaluation_repo.update_evaluation_status(
                evaluation_id, "failed", str(e)
            )
            raise
    
    async def process_session_evaluations(self, session_id: UUID) -> Dict[str, int]:
        """Processa todas as avaliações pendentes de uma sessão."""
        logger.info(f"Processando avaliações da sessão {session_id}")
        
        # Busca avaliações pendentes da sessão
        evaluations = await self.evaluation_repo.list_evaluations_by_session(session_id)
        pending_evaluations = [e for e in evaluations if e.status == "pending"]
        
        if not pending_evaluations:
            logger.info(f"Nenhuma avaliação pendente encontrada para sessão {session_id}")
            return {"total": 0, "successful": 0, "failed": 0}
        
        # Atualiza status da sessão
        await self.evaluation_repo.update_session_status(session_id, "running")
        
        successful = 0
        failed = 0
        
        for evaluation in pending_evaluations:
            try:
                request = CreateRagasEvaluationRequest(
                    session_id=evaluation.session_id,
                    email_id=evaluation.email_id,
                    user_context=evaluation.user_context,
                    search_query=evaluation.search_query,
                    generation_context=evaluation.generation_context,
                    difficulty=evaluation.difficulty,
                    hyde_context=evaluation.hyde_context,
                    fused_context=evaluation.fused_context
                )
                
                await self.process_single_evaluation(request)
                successful += 1
                
            except Exception as e:
                logger.error(f"Erro ao processar avaliação {evaluation.id}: {str(e)}")
                failed += 1
        
        # Atualiza contadores e status final da sessão
        total = len(pending_evaluations)
        await self.evaluation_repo.update_session_counters(session_id, total, successful, failed)
        
        final_status = "completed" if failed == 0 else "failed"
        await self.evaluation_repo.update_session_status(
            session_id, final_status, datetime.now() if final_status == "completed" else None
        )
        
        logger.info(f"Sessão {session_id} finalizada: {successful} sucessos, {failed} falhas")
        
        return {"total": total, "successful": successful, "failed": failed}
    
    async def process_batch_file(self, file_path: Path) -> Dict[str, int]:
        """Processa avaliações a partir de um arquivo JSON."""
        logger.info(f"Processando arquivo em lote: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                batch_data = json.load(f)
        except Exception as e:
            logger.error(f"Erro ao ler arquivo {file_path}: {str(e)}")
            raise
        
        evaluations = batch_data.get('evaluations', [])
        if not evaluations:
            logger.warning("Nenhuma avaliação encontrada no arquivo")
            return {"total": 0, "successful": 0, "failed": 0}
        
        successful = 0
        failed = 0
        
        for eval_data in evaluations:
            try:
                request = CreateRagasEvaluationRequest(**eval_data)
                await self.process_single_evaluation(request)
                successful += 1
                
            except Exception as e:
                logger.error(f"Erro ao processar avaliação do arquivo: {str(e)}")
                failed += 1
        
        total = len(evaluations)
        logger.info(f"Processamento em lote finalizado: {successful} sucessos, {failed} falhas")
        
        return {"total": total, "successful": successful, "failed": failed}
    
    def _get_metric_category(self, metric_name: str) -> str:
        """Determina a categoria de uma métrica."""
        retrieval_metrics = ['context_precision', 'context_recall']
        generation_metrics = ['faithfulness', 'answer_relevancy']
        
        if metric_name in retrieval_metrics:
            return 'retrieval'
        elif metric_name in generation_metrics:
            return 'generation'
        else:
            return 'other'


async def main():
    """Função principal do script."""
    parser = argparse.ArgumentParser(description='Script de avaliação RAGAS standalone')
    parser.add_argument('--email-id', type=str, help='ID do email para avaliação individual')
    parser.add_argument('--user-context', type=str, help='Contexto do usuário')
    parser.add_argument('--search-query', type=str, help='Query de busca')
    parser.add_argument('--generation-context', type=str, help='Contexto de geração')
    parser.add_argument('--difficulty', type=str, default='medio', help='Nível de dificuldade')
    parser.add_argument('--hyde-context', type=str, help='Contexto HyDE')
    parser.add_argument('--fused-context', type=str, help='Contexto fusionado')
    parser.add_argument('--session-id', type=str, help='ID da sessão para processar todas as avaliações')
    parser.add_argument('--batch-file', type=str, help='Arquivo JSON com avaliações em lote')
    parser.add_argument('--log-level', type=str, default='INFO', 
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='Nível de log')
    
    args = parser.parse_args()
    
    # Configura nível de log
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    # Validação de argumentos
    if not any([args.email_id, args.session_id, args.batch_file]):
        logger.error("É necessário fornecer --email-id, --session-id ou --batch-file")
        sys.exit(1)
    
    if args.email_id and not all([args.user_context, args.search_query, args.generation_context]):
        logger.error("Para avaliação individual, é necessário fornecer user-context, search-query e generation-context")
        sys.exit(1)
    
    try:
        # Inicializa conexão com banco
        db_pool = await get_db_pool()
        service = RagasEvaluationService(db_pool)
        await service.initialize_components()
        
        if args.email_id:
            # Avaliação individual
            request = CreateRagasEvaluationRequest(
                email_id=UUID(args.email_id),
                user_context=args.user_context,
                search_query=args.search_query,
                generation_context=args.generation_context,
                difficulty=args.difficulty,
                hyde_context=args.hyde_context,
                fused_context=args.fused_context
            )
            
            evaluation_id = await service.process_single_evaluation(request)
            logger.info(f"Avaliação individual concluída: {evaluation_id}")
            
        elif args.session_id:
            # Processar sessão
            session_id = UUID(args.session_id)
            result = await service.process_session_evaluations(session_id)
            logger.info(f"Sessão processada: {result}")
            
        elif args.batch_file:
            # Processar arquivo em lote
            file_path = Path(args.batch_file)
            if not file_path.exists():
                logger.error(f"Arquivo não encontrado: {file_path}")
                sys.exit(1)
            
            result = await service.process_batch_file(file_path)
            logger.info(f"Lote processado: {result}")
        
        await db_pool.close()
        logger.info("Script finalizado com sucesso")
        
    except Exception as e:
        logger.error(f"Erro fatal: {str(e)}")
        logger.error(f"Stack trace: {traceback.format_exc()}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())