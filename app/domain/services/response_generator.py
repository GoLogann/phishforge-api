import logging
import re

from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

from app.core.config import settings


class ResponseGenerator:
    def __init__(self):
        self.llm = ChatOpenAI(
            model_name=settings.MODEL_NAME_LLM,
            temperature=0.6,
            api_key=settings.OPENAI_API_KEY
        )

        self.prompt_template = PromptTemplate(
            input_variables=["context", "difficulty"],
            template=(
                "Você é um assistente de IA especializado em gerar exemplos de e-mails de phishing para fins educacionais. "
                "Sua tarefa é criar exemplos realistas, de e-mails de phishing com base no contexto fornecido. "
                "Cada exemplo deve seguir a estrutura de um e-mail de phishing. Sempre crie nomes reais para o remetente "
                "e o receptor. É crie exemplos muito realistas. Seja criativo no conteudo do e-mail.\n\n"
                "Contexto: {context}\n\n"
                "Documentos Relavantes para incrementar sua resposta: {relevant_docs}\n\n"
                "Diculdade: {difficulty}\n\n"
                "Gere um exemplo de e-mail de phishing com base no contexto e na pergunta. "
                "Forneça a resposta no seguinte formato JSON:\n"
                
                "{{\n"
                "  \"receptor\": \"\",\n"
                "  \"remetente\": \"\",\n"
                "  \"assunto\": \"\",\n"
                "  \"conteudo\": \"\",\n"
                "  \"links\": [\"\"]\n"
                "}}\n\n"
            )
        )

        self.chain = self.prompt_template | self.llm

    async def generate_response(self, difficulty: str, context: str, relevant_docs):
        try:
            response = self.chain.invoke(
                {
                    "context": context,
                    "difficulty": difficulty,
                    "relevant_docs": relevant_docs
                }
            )

            clean_response = re.sub(r'```json\n|\n```', '', response.content)

            if clean_response:
                return clean_response
            else:
                raise ValueError("Received response is empty after cleaning markdown.")
        except Exception as e:
            logging.error(f"Error generating response: {e}")
            return {"error": "Failed to generate phishing email"}