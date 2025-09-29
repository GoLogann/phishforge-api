from fastapi import APIRouter, Body, HTTPException, Depends, Query, BackgroundTasks 
from dependency_injector.wiring import inject, Provide
from app.core.container import Container
from typing import Optional
from uuid import UUID

from ragas.llms import BaseRagasLLM
from ragas.embeddings import BaseRagasEmbeddings

from app.domain.services.evaluation import run_and_log_ragas_evaluation, run_ragas_evaluation
from app.domain.services.prompt_normalizer import PromptNormalizer
from app.domain.services.reranker import ReRanker
from app.domain.services.response_generator import ResponseGenerator
from app.domain.services.phishing_service import PhishingEmailService
from app.domain.services.retriever import DocumentRetriever
from app.dto.estatistica import EmailStatistics
from app.dto.query import QueryRequest

app = APIRouter()
    
@app.post("/api/v1/generate")
@inject
async def generate(
    request: QueryRequest,
    background_tasks: BackgroundTasks,
    response_generator: ResponseGenerator = Depends(Provide[Container.response_generator]),
    normalizer: PromptNormalizer = Depends(Provide[Container.prompt_normalizer]),
    retriever: DocumentRetriever = Depends(Provide[Container.retriever]),
    phishing_service: PhishingEmailService = Depends(Provide[Container.phishing_service]),
    reranker: ReRanker = Depends(Provide[Container.reranker]),
    eval_llm: BaseRagasLLM = Depends(Provide[Container.evaluation_llm]),
    eval_embeddings: BaseRagasEmbeddings = Depends(Provide[Container.evaluation_embeddings]),
):
    """
    Gera um exemplo de phishing com um pipeline RAG avançado e dispara a avaliação.
    """
    print(f"\n--- RECEIVED USER CONTEXT ---\n{request.user_context}\n")

    # 1. Normaliza o input do usuário
    normalized_data = await normalizer.normalize(request.user_context)
    search_query = normalized_data.search_query
    generation_context = normalized_data.generation_context
    print(f"--- NORMALIZED SEARCH QUERY (for retrieval) ---\n{search_query}\n")
    print(f"--- NORMALIZED GENERATION CONTEXT (for generator) ---\n{generation_context}\n")

    # 2. HyDE (Query Transformation)
    try:
        hyde_context = await response_generator.generate_hypothetical_answer(search_query)
    except Exception:
        hyde_context = search_query

    # 3. Retrieve (Busca Inicial)
    try:
        candidate_docs = retriever.vector_store.query(
            collection_name="phishing_articles",
            query_text=hyde_context,
            top_k=20
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving documents: {str(e)}")

    # 4. Re-rank (Refinamento da Busca)
    reranked_docs = reranker.rerank(search_query, candidate_docs)

    # 5. Extração e Fusão do Contexto
    if reranked_docs:
        top_docs_payloads = [doc.payload for doc in reranked_docs[:3]]
        final_contexts = [payload['parent_content'] for payload in top_docs_payloads if 'parent_content' in payload]
    else:
        final_contexts = []
    
    fused_context = await response_generator.fuse_and_summarize_context(
        generation_context=generation_context,
        contexts=final_contexts
    )

    # 6. Geração Final
    try:
        phishing_example = await response_generator.generate_response(
            difficulty=request.difficulty,
            context=generation_context,
            relevant_docs=fused_context
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating response: {str(e)}")

    # 7. Persistência
    email_id = await phishing_service.create_email(phishing_example)
    result = phishing_example.dict()
    result['id'] = str(email_id)

    # 8. Preparação de respostas para RAGAS (em português primeiro)
    expanded_email_response_pt = (
        f"Email de Phishing - Nível {request.difficulty}\n\n"
        f"**Remetente:** {phishing_example.remetente}\n"
        f"**Assunto:** {phishing_example.assunto}\n\n"
        f"**Corpo do Email:**\n{phishing_example.conteudo}\n\n"
        f"**Técnicas Implementadas:**\n"
        f"{phishing_example.explicacao[:300]}..."
    )
    
    full_response_with_explanation_pt = (
        f"Assunto: {phishing_example.assunto}\n"
        f"Remetente: {phishing_example.remetente}\n\n"
        f"Corpo do E-mail:\n{phishing_example.conteudo}\n\n"
        f"---\n"
        f"Análise das Táticas (Explicação Completa):\n{phishing_example.explicacao}"
    )

    # 9. Tradução para inglês (para RAGAS)
    async def translate_for_ragas():
        try:
            # Verificar se os contextos não estão vazios
            if not fused_context or not fused_context.strip():
                print("⚠️  Contexto vazio - pulando avaliação RAGAS")
                return
                
            # Use o método enriquecido
            expanded_en = await response_generator.translate_to_english_with_enrichment(
                expanded_email_response_pt, 
                request.difficulty
            )
            full_en = await response_generator.translate_to_english_with_enrichment(
                full_response_with_explanation_pt,
                request.difficulty
            )
            
            # Verificar se as traduções foram bem-sucedidas
            if not expanded_en or not full_en:
                print("⚠️  Falha na tradução - pulando avaliação RAGAS")
                return
                
            await run_and_log_ragas_evaluation(
                search_question=search_query,
                generation_question=request.user_context,
                expanded_answer=expanded_en,
                full_answer=full_en,
                contexts=[fused_context],
                eval_llm=eval_llm,
                eval_embeddings=eval_embeddings,
            )
        except Exception as e:
            print(f"Erro na tradução/avaliação RAGAS: {e}")
            import traceback
            print(f"Stack trace: {traceback.format_exc()}")

    # Dispara tradução e avaliação em background
    background_tasks.add_task(translate_for_ragas)

    return result


@app.post("/api/v1/generate/batch")
@inject
async def generate_batch(
    context: str = Body(..., embed=True),
    difficulties: list[str] = Body(..., embed=True),
    total: int = Body(default=10, embed=True),
    response_generator: ResponseGenerator = Depends(Provide[Container.response_generator]),
    retriever: DocumentRetriever = Depends(Provide[Container.retriever]),
    phishing_service: PhishingEmailService = Depends(Provide[Container.phishing_service]),
):
    if not difficulties:
        raise HTTPException(status_code=400, detail="A lista de dificuldades não pode estar vazia")
    if total <= 0:
        raise HTTPException(status_code=400, detail="O total deve ser maior que 0")
    if total > 10:
        raise HTTPException(status_code=400, detail="O total máximo permitido é 10")

    try:
        relevant_docs = retriever.vector_store.query(
            collection_name="phishing_articles",
            query_text=context,
            top_k=80
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao recuperar documentos: {str(e)}")

    docs_texts = [doc.text for doc in relevant_docs[:3]] if relevant_docs else []
    docs_text = "\n\n".join(docs_texts) if docs_texts else "Sem documentos relevantes."

    base, extra = divmod(total, len(difficulties))
    distribution = {d: base for d in difficulties}
    for i in range(extra):
        distribution[difficulties[i]] += 1

    results = []
    for difficulty, count in distribution.items():
        for _ in range(count):
            try:
                phishing_example = await response_generator.generate_response(
                    difficulty=difficulty,
                    context=context,
                    relevant_docs=docs_text
                )
                email_id = await phishing_service.create_email(phishing_example)
                result = phishing_example.dict()
                result['id'] = str(email_id)
                results.append(result)
            except Exception as e:
                results.append({"error": f"Falha ao gerar exemplo {difficulty}: {str(e)}"})

    return {
        "total_requested": total,
        "total_generated": len(results),
        "distribution": distribution,
        "examples": results
    }


@app.get("/api/v1/emails/statistics", response_model=EmailStatistics)
@inject
async def get_statistics(
    phishing_service: PhishingEmailService = Depends(Provide[Container.phishing_service]),
):
    try:
        raw_stats = await phishing_service.repository.get_stats()
        return EmailStatistics(**raw_stats)
    except Exception as e:
        return EmailStatistics()


@app.get("/api/v1/emails/statistics/debug")
@inject
async def debug_statistics(
    phishing_service: PhishingEmailService = Depends(Provide[Container.phishing_service]),
):
    try:
        raw_stats = await phishing_service.repository.get_stats()
        return {
            "raw_stats": raw_stats,
            "raw_stats_type": str(type(raw_stats)),
            "by_difficulty_type": str(type(raw_stats.get("by_difficulty"))),
            "by_category_type": str(type(raw_stats.get("by_category"))),
            "total_type": str(type(raw_stats.get("total"))),
            "recent_count_type": str(type(raw_stats.get("recent_count")))
        }
    except Exception as e:
        return {
            "error": str(e),
            "error_type": str(type(e).__name__)
        }


@app.get("/api/v1/emails")
@inject
async def list_emails(
    categoria: Optional[str] = None,
    nivel: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
    phishing_service: PhishingEmailService = Depends(Provide[Container.phishing_service]),
):
    try:
        if search:
            emails = await phishing_service.search_emails(search, limit)
        elif categoria:
            emails = await phishing_service.get_emails_by_categoria(categoria, limit)
        elif nivel:
            emails = await phishing_service.get_emails_by_nivel(nivel, limit)
        else:
            emails = await phishing_service.get_all_emails(limit, offset)

        return {"emails": [email.dict() for email in emails], "count": len(emails)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving emails: {str(e)}")


@app.get("/api/v1/emails/{email_id}")
@inject
async def get_email(
    email_id: UUID,
    phishing_service: PhishingEmailService = Depends(Provide[Container.phishing_service]),
):
    email = await phishing_service.get_email_by_id(email_id)
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    return email.dict()


@app.delete("/api/v1/emails/{email_id}")
@inject
async def delete_email(
    email_id: UUID,
    phishing_service: PhishingEmailService = Depends(Provide[Container.phishing_service]),
):
    try:
        success = await phishing_service.delete_email(email_id)
        if not success:
            raise HTTPException(status_code=404, detail="Email not found")
        return {"message": "Email deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting email: {str(e)}")
