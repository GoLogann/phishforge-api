# app/domain/services/user_answer_evaluator.py

import logging

from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field


class UserAnswerScore(BaseModel):
    """Modelo estruturado para a resposta da avaliação"""
    score: int = Field(
        ge=0, 
        le=5, 
        description="Nota de 0 a 5 para a justificativa do usuário"
    )
    feedback: str = Field(
        description="Feedback detalhado explicando a nota atribuída"
    )
    strengths: list[str] = Field(
        default_factory=list,
        description="Pontos fortes identificados na justificativa"
    )
    improvements: list[str] = Field(
        default_factory=list,
        description="Pontos que podem ser melhorados na justificativa"
    )


class UserAnswerEvaluator:
    """
    Serviço para avaliar justificativas de usuários sobre identificação de phishing.
    
    Este serviço recebe um exemplo de phishing e a justificativa do usuário
    sobre por que ele acredita que o exemplo é phishing, retornando uma
    nota de 0 a 5 com feedback detalhado.
    """
    
    def __init__(self, api_key: str, model_name: str = "gpt-4o-mini"):
        self.llm = ChatOpenAI(
            model_name=model_name,
            api_key=api_key,
            temperature=0.3
        ).with_structured_output(UserAnswerScore)
        
        self.logger = logging.getLogger(__name__)

    async def evaluate(
        self,
        phishing_example: str,
        user_justification: str
    ) -> UserAnswerScore:
        """
        Avalia a justificativa do usuário sobre identificação de phishing.
        
        Args:
            phishing_example: O exemplo de phishing que foi apresentado ao usuário
            user_justification: A justificativa do usuário explicando por que é phishing
            
        Returns:
            UserAnswerScore com nota de 0 a 5 e feedback detalhado
        """
        prompt = self._build_prompt(phishing_example, user_justification)
        
        try:
            result = await self.llm.ainvoke(prompt)
            self.logger.info(f"Avaliação concluída: nota {result.score}/5")
            return result
        except Exception as e:
            self.logger.error(f"Erro ao avaliar justificativa: {str(e)}")
            raise

    def _build_prompt(self, phishing_example: str, user_justification: str) -> str:
        """Constrói o prompt para avaliação da justificativa"""
        return f"""## TAREFA
Você é um especialista em cibersegurança e educação. Sua tarefa é avaliar a justificativa de um usuário sobre por que um determinado exemplo é um email de phishing.

## EXEMPLO DE PHISHING APRESENTADO
{phishing_example}

## JUSTIFICATIVA DO USUÁRIO
{user_justification}

## CRITÉRIOS DE AVALIAÇÃO (0-5)

**Nota 0 - Incorreto:**
- Justificativa completamente errada ou sem relação com phishing
- Não identifica nenhum indicador válido

**Nota 1 - Muito Fraco:**
- Menciona apenas um ponto superficial
- Não demonstra compreensão das técnicas de phishing

**Nota 2 - Fraco:**
- Identifica poucos indicadores de forma vaga
- Argumentação pouco desenvolvida

**Nota 3 - Satisfatório:**
- Identifica alguns indicadores corretos
- Argumentação básica mas razoável
- Demonstra compreensão parcial das táticas de phishing

**Nota 4 - Bom:**
- Identifica múltiplos indicadores corretamente
- Boa articulação dos argumentos
- Demonstra boa compreensão das técnicas de engenharia social

**Nota 5 - Excelente:**
- Identifica a maioria ou todos os indicadores presentes
- Argumentação clara, completa e bem estruturada
- Demonstra profundo conhecimento sobre táticas de phishing
- Menciona gatilhos psicológicos e técnicas específicas

## INDICADORES QUE DEVEM SER CONSIDERADOS
Avalie se o usuário identificou corretamente elementos como:
- Remetente suspeito ou falsificado
- Tom de urgência ou pressão
- Links suspeitos ou disfarçados
- Solicitação de informações sensíveis
- Erros gramaticais ou de formatação
- Inconsistências na identidade visual
- Gatilhos psicológicos (medo, ganância, curiosidade, autoridade)
- Técnicas de engenharia social
- Contexto implausível ou genérico

## INSTRUÇÕES
1. Analise cuidadosamente o exemplo de phishing
2. Compare com a justificativa do usuário
3. Atribua uma nota de 0 a 5
4. Forneça feedback construtivo
5. Liste pontos fortes e áreas de melhoria

Seja justo e educativo na avaliação."""
