import logging

from ragas.dataset_schema import SingleTurnSample
from ragas.embeddings import BaseRagasEmbeddings
from ragas.llms import BaseRagasLLM
from ragas.metrics import (
    ContextRelevance,
    Faithfulness,
    ResponseRelevancy,
)

logging.basicConfig(level=logging.INFO)
evaluation_logger = logging.getLogger("ragas_evaluation")


async def run_ragas_evaluation(
    search_question: str,
    generation_question: str,
    expanded_answer: str,
    full_answer: str,
    contexts: list[str],
    eval_llm: BaseRagasLLM,
    eval_embeddings: BaseRagasEmbeddings,
) -> dict:
    """
    Executa avaliação RAGAS - TUDO EM INGLÊS.
    Usa apenas métricas reference-free (sem necessidade de ground truth).

    Métricas:
    - Context Relevance: Avalia se os contextos recuperados são relevantes para a pergunta
    - Faithfulness: Avalia se a resposta é fiel/suportada pelos contextos
    - Response Relevancy: Avalia se a resposta é relevante para a pergunta do usuário
      (NÃO precisa de contexto, apenas user_input e response)
    """
    try:
        # Sample para Context Relevance e Faithfulness (precisam de contexto)
        context_sample = SingleTurnSample(
            user_input=search_question,
            retrieved_contexts=contexts,
            response=full_answer,
        )

        # Sample para Response Relevancy (NÃO precisa de contexto)
        # Usa a query tratada do usuário e a resposta gerada
        relevancy_sample = SingleTurnSample(
            user_input=generation_question, response=expanded_answer
        )

        context_scorer = ContextRelevance(llm=eval_llm)
        relevancy_scorer = ResponseRelevancy(llm=eval_llm, embeddings=eval_embeddings)
        faithfulness_scorer = Faithfulness(llm=eval_llm)

        context_score = await context_scorer.single_turn_ascore(context_sample)
        faithfulness_score = await faithfulness_scorer.single_turn_ascore(
            context_sample
        )
        relevancy_score = await relevancy_scorer.single_turn_ascore(relevancy_sample)

        evaluation_logger.info(f"\n{'=' * 60}")
        evaluation_logger.info("RAGAS EVALUATION (ALL IN ENGLISH)")
        evaluation_logger.info(f"{'=' * 60}")
        evaluation_logger.info(f"Context Relevance:    {context_score}")
        evaluation_logger.info(f"Faithfulness:         {faithfulness_score}")
        evaluation_logger.info(f"Response Relevancy:   {relevancy_score}")
        evaluation_logger.info(f"{'=' * 60}\n")

        return {
            "context_relevance": context_score,
            "faithfulness": faithfulness_score,
            "response_relevancy": relevancy_score,
        }

    except Exception as e:
        evaluation_logger.error(f"Erro RAGAS: {str(e)}", exc_info=True)
        return {
            "context_relevance": None,
            "faithfulness": None,
            "response_relevancy": None,
            "error": str(e),
        }


async def run_and_log_ragas_evaluation(
    search_question: str,
    generation_question: str,
    expanded_answer: str,
    full_answer: str,
    contexts: list[str],
    eval_llm: BaseRagasLLM,
    eval_embeddings: BaseRagasEmbeddings,
):
    """
    Wrapper que executa a avaliação RAGAS e exibe resultados formatados.
    """
    ragas_result = await run_ragas_evaluation(
        search_question=search_question,
        generation_question=generation_question,
        expanded_answer=expanded_answer,
        full_answer=full_answer,
        contexts=contexts,
        eval_llm=eval_llm,
        eval_embeddings=eval_embeddings,
    )

    print("\n" + "=" * 70)
    print("📊 RAGAS EVALUATION RESULTS")
    print("=" * 70)
    print(f"Search Question: {search_question[:100]}...")
    print(f"Generation Question: {generation_question[:100]}...")
    print("-" * 70)

    if ragas_result.get("error"):
        print(f"❌ ERROR: {ragas_result['error']}")
    else:
        context_rel = ragas_result.get("context_relevance")
        faithfulness_score = ragas_result.get("faithfulness")
        response_rel = ragas_result.get("response_relevancy")

        print(
            f"Context Relevance:    {context_rel:.4f}"
            if context_rel is not None
            else "Context Relevance:    N/A"
        )
        print(
            f"Faithfulness:         {faithfulness_score:.4f}"
            if faithfulness_score is not None
            else "Faithfulness:         N/A"
        )
        print(
            f"Response Relevancy:   {response_rel:.4f}"
            if response_rel is not None
            else "Response Relevancy:   N/A"
        )

        if context_rel is not None:
            if context_rel >= 0.8:
                print("✅ Context Relevance: EXCELENTE - Contexto altamente relevante")
            elif context_rel >= 0.6:
                print("⚠️  Context Relevance: BOM - Contexto parcialmente relevante")
            else:
                print("❌ Context Relevance: BAIXO - Contexto pouco relevante")

        if faithfulness_score is not None:
            if faithfulness_score >= 0.8:
                print("✅ Faithfulness: EXCELENTE - A resposta é fiel ao contexto")
            elif faithfulness_score >= 0.6:
                print(
                    "⚠️  Faithfulness: BOM - A resposta contém algumas informações não suportadas"
                )
            else:
                print(
                    "❌ Faithfulness: BAIXO - A resposta parece estar alucinando/inventando fatos"
                )

        if response_rel is not None:
            if response_rel >= 0.8:
                print("✅ Response Relevancy: EXCELENTE - Resposta altamente alinhada")
            elif response_rel >= 0.6:
                print(
                    "⚠️  Response Relevancy: BOM - Resposta adequada com espaço para melhoria"
                )
            else:
                print("❌ Response Relevancy: BAIXO - Resposta precisa de ajustes")

    print("=" * 70 + "\n")
