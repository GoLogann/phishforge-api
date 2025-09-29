# app/domain/services/response_generator.py

import logging
from langchain_core.prompts import PromptTemplate
from app.domain.models.phishing_email import PhishingEmail
from langchain_openai import ChatOpenAI

class ResponseGenerator:
    def __init__(self, api_key: str, model_name: str = "gpt-4o-mini"):
        self.llm = ChatOpenAI(
            model_name=model_name,
            api_key=api_key,
            temperature=0.7 # Reduzido para maior consistência
        ).with_structured_output(PhishingEmail)

        self.text_llm = ChatOpenAI(
            model_name=model_name,
            api_key=api_key,
            temperature=0.2
        )

        self.prompt_template = PromptTemplate(
                    input_variables=["context", "difficulty", "relevant_docs"],
                    template=(
                        "Você é um especialista em cibersegurança especializado na criação de emails de phishing educacionais baseados em pesquisas acadêmicas.\n\n"
                        
                        "## CARACTERÍSTICAS DOS NÍVEIS DE DIFICULDADE\n\n"
                        
                        "**FÁCIL:**\n"
                        "- Remetente claramente suspeito ou genérico (ex: noreply@empresa123.com)\n"
                        "- Assunto com erros ortográficos ou gramaticais evidentes\n"
                        "- Urgência exagerada e óbvia ('URGENTE!!!', 'AÇÃO IMEDIATA')\n"
                        "- Links visivelmente suspeitos ou encurtados\n"
                        "- Formatação inconsistente ou amadora\n"
                        "- Ausência de personalização (tratamento genérico)\n"
                        "- Ameaças diretas e explícitas\n"
                        "- Solicitação óbvia de informações sensíveis\n\n"
                        
                        "**MÉDIO:**\n"
                        "- Remetente parcialmente convincente mas com pequenas inconsistências\n"
                        "- Assunto plausível mas com alguns indicadores de suspeita\n"
                        "- Urgência moderada com justificativa aparente\n"
                        "- Links que parecem legítimos à primeira vista\n"
                        "- Formatação mais profissional, similar a comunicações empresariais\n"
                        "- Personalização básica (nome do destinatário)\n"
                        "- Mistura de informações verdadeiras com falsas\n"
                        "- Uso de logos e identidade visual parcialmente convincentes\n"
                        "- Solicitação indireta de ação (download, clique, verificação)\n\n"
                        
                        "**DIFÍCIL:**\n"
                        "- Remetente altamente convincente, indistinguível de comunicações legítimas\n"
                        "- Assunto contextualmente perfeito e relevante\n"
                        "- Urgência sutil e bem justificada (contexto empresarial realista)\n"
                        "- Links com domínios similares aos originais (typosquatting sutil)\n"
                        "- Formatação profissional idêntica às comunicações oficiais\n"
                        "- Personalização avançada (cargo, projetos específicos, colegas)\n"
                        "- Informações específicas e verificáveis sobre a empresa/pessoa\n"
                        "- Identidade visual perfeita (logos, assinaturas, layout)\n"
                        "- Contexto temporal relevante (eventos atuais, datas importantes)\n"
                        "- Engenharia social sofisticada (psicologia, autoridade, reciprocidade)\n\n"
                        
                        "## ANÁLISE DO CONHECIMENTO TÉCNICO\n"
                        "Analise cuidadosamente as táticas, métodos e gatilhos psicológicos descritos nos documentos de pesquisa:\n\n"
                        "**CONHECIMENTO ACADÊMICO:**\n"
                        "{relevant_docs}\n\n"
                        
                        "## ESPECIFICAÇÕES DO CENÁRIO\n"
                        "**Nível de Dificuldade:** {difficulty}\n"
                        "**Cenário Específico:** {context}\n\n"
                        
                        "## PROCESSO DE RACIOCÍNIO (CHAIN-OF-THOUGHT)\n"
                        "Antes de gerar o email, siga este processo de raciocínio passo a passo:\n\n"
                        
                        "**PASSO 1 - ANÁLISE DO CONTEXTO:**\n"
                        "Pense: Qual é o cenário solicitado? Qual organização/situação está sendo simulada? Quem seria o alvo típico?\n"
                        "Identifique os elementos-chave que tornam este cenário plausível.\n\n"
                        
                        "**PASSO 2 - MAPEAMENTO DE TÁTICAS:**\n"
                        "Pense: Quais técnicas de phishing do conhecimento acadêmico são mais aplicáveis a este cenário?\n"
                        "Liste mentalmente: gatilhos psicológicos relevantes, vetores de ataque apropriados, técnicas de persuasão aplicáveis.\n\n"
                        
                        "**PASSO 3 - ADEQUAÇÃO AO NÍVEL:**\n"
                        "Pense: Como o nível '{difficulty}' deve influenciar cada componente do email?\n"
                        "- Remetente: Como deve parecer no nível {difficulty}?\n"
                        "- Assunto: Que grau de sofisticação é esperado?\n"
                        "- Corpo: Quão convincente e personalizado deve ser?\n"
                        "- Links/URLs: Que nível de camuflagem é necessário?\n"
                        "- Call-to-action: Quão direto ou sutil deve ser?\n\n"
                        
                        "**PASSO 4 - SÍNTESE DOS ELEMENTOS:**\n"
                        "Pense: Como combinar o cenário + táticas acadêmicas + nível de dificuldade em um email coerente?\n"
                        "Considere: consistência entre todos os elementos, realismo do contexto, efetividade psicológica.\n\n"
                        
                        "**PASSO 5 - VALIDAÇÃO DE COMPLETUDE:**\n"
                        "Pense: O email cobre todos os aspectos solicitados?\n"
                        "- ✓ Remetente definido?\n"
                        "- ✓ Assunto apropriado?\n"
                        "- ✓ Corpo completo e convincente?\n"
                        "- ✓ Call-to-action claro?\n"
                        "- ✓ Técnicas acadêmicas implementadas?\n"
                        "- ✓ Nível de dificuldade respeitado?\n\n"
                        
                        "## INSTRUÇÕES DE SÍNTESE\n"
                        "Após completar o processo de raciocínio acima, crie um email de phishing que:\n\n"
                        
                        "1. **APLIQUE O RACIOCÍNIO:** Use as conclusões dos 5 passos para informar cada decisão\n"
                        "2. **IMPLEMENTE O NÍVEL:** Garanta que cada elemento reflita precisamente as características do nível '{difficulty}'\n"
                        "3. **INTEGRE CONCEITOS TÉCNICOS:** Incorpore naturalmente as táticas identificadas no conhecimento acadêmico\n"
                        "4. **MANTENHA COMPLETUDE:** Inclua todos os componentes solicitados no cenário\n"
                        "5. **ASSEGURE CONSISTÊNCIA:** Todos os elementos devem trabalhar juntos de forma coerente\n"
                        "6. **MAXIMIZE REALISMO:** Use detalhes plausíveis e específicos ao contexto\n\n"
                        
                        "## FORMATO DE RESPOSTA\n"
                        "Gere APENAS o objeto JSON no formato PhishingEmail, sem incluir o raciocínio intermediário.\n"
                        "O email deve ser o resultado final da aplicação do processo Chain-of-Thought.\n\n"
                        
                        "IMPORTANTE: Embora você não mostre explicitamente os passos de raciocínio, sua resposta deve demonstrar que você seguiu este processo sistemático, resultando em um email que implementa:\n"
                        "- As características específicas do nível '{difficulty}'\n"
                        "- As táticas acadêmicas identificadas no conhecimento técnico\n"
                        "- O cenário solicitado de forma completa e precisa\n"
                        "- Um raciocínio coerente e bem fundamentado em cada elemento"
                    )
                )
        
        self.hyde_prompt_template = PromptTemplate(
            input_variables=["query"],
            template=(
                "Como especialista em cibersegurança, gere uma resposta técnica e específica para a consulta do usuário. "
                "Esta resposta deve incluir terminologia precisa, conceitos técnicos e detalhes específicos que um documento acadêmico sobre o tópico conteria.\n\n"
                
                "**Consulta:** {query}\n\n"
                
                "**Resposta técnica (inclua métodos específicos, terminologia acadêmica e conceitos detalhados):**\n"
            )
        )
        
        self.chain = self.prompt_template | self.llm
        self.hyde_chain = self.hyde_prompt_template | self.text_llm

    async def generate_response(self, difficulty: str, context: str, relevant_docs):
        """
        Gera um email de phishing baseado no contexto, dificuldade e documentos relevantes.
        
        Args:
            difficulty: Nível de dificuldade ('fácil', 'médio', 'difícil')
            context: Contexto específico do cenário
            relevant_docs: Documentos acadêmicos relevantes
        """
        try:
            # Normaliza o nível de dificuldade para garantir consistência
            difficulty_normalized = difficulty.lower().strip()
            if difficulty_normalized not in ['fácil', 'médio', 'difícil', 'facil', 'medio', 'dificil']:
                difficulty_normalized = 'médio'  # Default para médio se não reconhecido
            
            return await self.chain.ainvoke({
                "context": context,
                "difficulty": difficulty_normalized,
                "relevant_docs": relevant_docs
            })
        except Exception as e:
            logging.error(f"Error generating response: {e}")
            raise e 

    async def generate_hypothetical_answer(self, query: str) -> str:
        """
        Gera uma resposta hipotética para melhorar a busca semântica (HyDE).
        
        Args:
            query: Consulta do usuário
            
        Returns:
            str: Resposta hipotética rica em contexto técnico
        """
        try:
            response = await self.hyde_chain.ainvoke({"query": query})
            return response.content.strip().strip('"')
        except Exception as e:
            logging.error(f"Error generating hypothetical answer: {e}")
            return query


    async def fuse_and_summarize_context(self, generation_context: str, contexts: list[str]) -> str:
        """
        Funde múltiplos contextos em um resumo coeso e relevante.
        
        Args:
            generation_context: Contexto da tarefa de geração
            contexts: Lista de contextos a serem fundidos
            
        Returns:
            str: Contexto fundido e resumido
        """
        if not contexts:
            return "Conhecimento técnico específico não disponível."

        full_context_text = "\n\n---\n\n".join(contexts)

        prompt = PromptTemplate(
            input_variables=["generation_context", "full_context_text"],
            template=(
                "Analise os documentos acadêmicos e extraia informações técnicas específicas para executar a tarefa solicitada.\n\n"
                
                "**TAREFA CRIATIVA:**\n"
                "{generation_context}\n\n"
                
                "**DOCUMENTOS ACADÊMICOS:**\n"
                "{full_context_text}\n\n"
                
                "**INSTRUÇÕES DE EXTRAÇÃO:**\n"
                "1. Identifique táticas, técnicas e métodos específicos relevantes para a tarefa\n"
                "2. Extraia gatilhos psicológicos e estratégias mencionadas\n"
                "3. Inclua exemplos práticos e terminologia técnica\n"
                "4. Mantenha apenas informações DIRETAMENTE úteis para a criação do email\n"
                "5. Organize em formato claro e acionável\n"
                "6. Relacione as técnicas com níveis de sofisticação (fácil, médio, difícil)\n\n"
                
                "**CONHECIMENTO TÉCNICO FOCADO (em português brasileiro):**"
            )
        )
        
        fusion_chain = prompt | self.text_llm
        
        try:
            response = await fusion_chain.ainvoke({
                "generation_context": generation_context,
                "full_context_text": full_context_text
            })
            return response.content.strip()
        except Exception as e:
            logging.error(f"Error fusing context: {e}")
            return full_context_text


    async def translate_to_english_with_enrichment(self, text: str, difficulty: str) -> str:
        """
        Traduz e enriquece o texto com terminologia técnica explícita.
        """
        if not text or len(text.split()) < 5:
            return text

        prompt = PromptTemplate(
            input_variables=["text_to_translate", "difficulty"],
            template=(
                "Translate the following phishing email from Portuguese to English. "
                "Additionally, ENRICH the translation by explicitly mentioning the social engineering techniques used.\n\n"
                
                "**Instructions:**\n"
                "1. Translate all content accurately\n"
                "2. After the 'Implemented Techniques' section, ADD a paragraph explicitly stating:\n"
                "   - Which social engineering tactics are used (e.g., authority, urgency, personalization)\n"
                "   - How the email demonstrates sophisticated phishing techniques\n"
                "   - The {difficulty}-level characteristics present in the email\n\n"
                
                "**Text to translate:**\n"
                "{text_to_translate}\n\n"
                
                "**Enriched English translation:**"
            )
        )
        
        translation_chain = prompt | self.text_llm
        
        try:
            response = await translation_chain.ainvoke({
                "text_to_translate": text,
                "difficulty": difficulty
            })
            return response.content.strip()
        except Exception as e:
            logging.error(f"Error translating to English: {e}")
            return text