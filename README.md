# PhishForge

PhishForge é uma ferramenta educacional que gera exemplos de e-mails de phishing utilizando Inteligência Artificial. O objetivo é conscientizar e treinar usuários sobre técnicas de phishing, ajudando na prevenção contra ataques cibernéticos.

## Tecnologias Utilizadas

- **LangChain** - Para a geração de e-mails de phishing com IA.
- **Qdrant** - Base vetorial utilizada para armazenamento e busca semântica.
- **FastAPI** - Framework para exposição da API.
- **Poetry** - Gerenciador de dependências do projeto.
- **Docker Compose** - Para gestão do container do Qdrant.

## Instalação e Configuração

1. Clone este repositório:

   ```bash
   git clone https://github.com/GoLogann/phishforge.git
   cd phishforge
   ```

2. Instale as dependências utilizando Poetry:

   ```bash
   poetry install
   ```

3. Inicie o container do Qdrant com Docker Compose:

   ```bash
   docker-compose up -d
   ```

4. Certifique-se de ter um token da API da OpenAI para usar o GPT:
   
   Defina-o no arquivo `core/config.py` dentro da classe `Settings`:

   ```python
   from pydantic_settings import BaseSettings

   class Settings(BaseSettings):
       MODEL_NAME_EMBEDDING: str = "all-MiniLM-L6-v2"
       MODEL_NAME_LLM: str = "gpt-4o"
       QDRANT_URL: str = "http://localhost:6333"
       OPENAI_API_KEY: str = "sua-chave-aqui"
       CHUNK_SIZE: int = 1000
       CHUNK_OVERLAP: int = 200
       TOP_K_DOCUMENTS: int = 4

   settings = Settings()
   ```

6. Execute a API com FastAPI:

   ```bash
   poetry run uvicorn app.main:app --reload
   ```

## Uso

A API disponibiliza endpoints para gerar e-mails de phishing educacionais. Para testar, acesse:

- **Swagger UI**: `http://localhost:8000/docs`
- **Redoc**: `http://localhost:8000/redoc`
