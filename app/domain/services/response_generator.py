import logging
import re

from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

from app.core.config import settings


class ResponseGenerator:
    def __init__(self):
        self.llm = ChatOpenAI(
            model_name=settings.MODEL_NAME_LLM,
            temperature=0,
            api_key=settings.OPENAI_API_KEY
        )

        self.prompt_template = PromptTemplate(
            input_variables=["context", "difficulty"],
            template=(
                "Você é um assistente de IA especializado em gerar exemplos de e-mails de phishing para fins educacionais. "
                "Sua tarefa é criar exemplos realistas, de e-mails de phishing com base no contexto fornecido. "
                "Cada exemplo deve seguir a estrutura de um e-mail de phishing.\n\n"
                "Contexto: {context}\n\n"
                "Diculdade: {difficulty}\n\n"
                "Gere um exemplo de e-mail de phishing com base no contexto e na pergunta. "
                "Forneça a resposta no seguinte formato JSON:\n"
                
                "{{\n"
                "  \"receptor\": \"email@example.com\",\n"
                "  \"remetente\": \"fake_sender@example.com\",\n"
                "  \"assunto\": \"Urgente: Verifique sua conta\",\n"
                "  \"conteudo\": \"Caro usuário, por favor, verifique sua conta clicando no link abaixo...\",\n"
                "  \"links\": [\"http://malicious-link.com\"]\n"
                "}}\n\n"
            )
        )

        self.chain = self.prompt_template | self.llm

    async def generate_response(self, difficulty: str, context: str):
        try:
            response = self.chain.invoke(
                {
                    "context": context,
                    "difficulty": difficulty,
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