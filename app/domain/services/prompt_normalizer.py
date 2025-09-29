from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate

class NormalizedQuery(BaseModel):
    search_query: str = Field(description="A pergunta otimizada e rica em palavras-chave, ideal para uma busca semântica em documentos acadêmicos.")
    generation_context: str = Field(description="O cenário específico ou a instrução criativa para a geração final. Se não houver, use uma descrição da tarefa.")

class PromptNormalizer:
    def __init__(self, api_key: str, model_name: str = "gpt-4o-mini"):
        self.llm = ChatOpenAI(
            model_name=model_name,
            api_key=api_key,
            temperature=0.0
        ).with_structured_output(NormalizedQuery)

        self.prompt_template = PromptTemplate(
            input_variables=["user_context"],
            template=(
                "Você é um especialista em reescrever queries para um sistema de Retrieval-Augmented Generation (RAG). "
                "Sua tarefa é analisar o contexto do usuário e transformá-lo em dois componentes:\n"
                "1. Uma 'search_query' clara e técnica para buscar informações em artigos acadêmicos sobre cibersegurança.\n"
                "2. Um 'generation_context' que captura o cenário específico que o usuário quer que seja criado.\n\n"
                
                "**REGRAS IMPORTANTES:**\n"
                "- A 'search_query' DEVE ser em INGLÊS para garantir a compatibilidade com os documentos de pesquisa.\n"
                "- O 'generation_context' deve permanecer no idioma original do usuário.\n\n"

                "Contexto do Usuário: '{user_context}'\n\n"
                
                "Exemplo:\n"
                "Contexto do Usuário: 'cria um email de phishing dificil pro alex do chefe dele, a sarah, sobre o projeto aurora'\n"
                "Saída JSON: {{"
                '  "search_query": "Advanced spear phishing techniques using social engineering and referencing internal projects to create urgency.",'
                '  "generation_context": "O cenário é um e-mail para o funcionário Alex, vindo de sua chefe Sarah, sobre o Projeto Aurora."'
                "}}\n\n"
                
                "Agora, processe o contexto do usuário fornecido."
            )
        )
        self.chain = self.prompt_template | self.llm

    async def normalize(self, user_context: str) -> NormalizedQuery:
        return await self.chain.ainvoke({"user_context": user_context})