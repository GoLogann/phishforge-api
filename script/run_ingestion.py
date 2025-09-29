import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient

# Importe os componentes da sua aplicação
from app.domain.services.document_processor import DocumentProcessor
from app.domain.services.openai.embedding_client import OpenAIEmbeddingClient
from app.infra.qdrant.store import QdrantVectorStore

load_dotenv()

# Caminho absoluto para a pasta de artigos, para que o script funcione de qualquer lugar
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
ARTICLES_DIR = os.path.join(PROJECT_ROOT, "data", "articles")

# Constantes de configuração
COLLECTION_NAME = "phishing_articles"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")


# --- Injeção de Dependência Manual ---
qdrant_client = QdrantClient(url=QDRANT_URL)
embedding_client = OpenAIEmbeddingClient(api_key=OPENAI_API_KEY)
vector_store = QdrantVectorStore(client=qdrant_client, embedding_client=embedding_client)
processor = DocumentProcessor(chunk_size=800, chunk_overlap=150)

def delete_articles_collection():
    """Deleta a coleção para garantir uma re-indexação limpa."""
    print(f"🗑️  Tentando deletar a coleção '{COLLECTION_NAME}'...")
    try:
        vector_store.client.delete_collection(collection_name=COLLECTION_NAME)
        print(f"✅ Coleção '{COLLECTION_NAME}' deletada com sucesso.")
    except Exception as e:
        print(f"ℹ️  Não foi possível deletar a coleção (pode não existir ainda): {e}")

def index_articles():
    """
    Orquestra a indexação de todos os documentos suportados na pasta de artigos.
    """
    supported_extensions = [".pdf", ".md", ".txt"]
    try:
        all_files = [f for f in os.listdir(ARTICLES_DIR) if any(f.endswith(ext) for ext in supported_extensions)]
    except FileNotFoundError:
        print(f"❌ Erro: O diretório '{ARTICLES_DIR}' não foi encontrado.")
        return

    if not all_files:
        print(f"⚠️  Nenhum arquivo suportado encontrado em '{ARTICLES_DIR}'.")
        return

    print(f"🚀 Iniciando a indexação de {len(all_files)} documento(s)...")

    for file_name in all_files:
        file_path = os.path.join(ARTICLES_DIR, file_name)
        print(f"\n📄 Processando: {file_name}")

        try:
            # A lógica foi centralizada no DocumentProcessor
            chunks_data = processor.process_file(file_path)

            if not chunks_data:
                print(f"⚠️  Nenhum chunk gerado para {file_name}. Pulando.")
                continue
            
            vector_store.save(COLLECTION_NAME, chunks_data)
            print(f"✅ Indexado com sucesso: {len(chunks_data)} chunks de '{file_name}'")
        except Exception as e:
            print(f"❌ Erro ao processar o arquivo {file_name}: {e}")

    print(f"\n🎉 Processo de indexação concluído!")

def validate_indexing(sample_size: int = 5):
    """
    Busca amostras no Qdrant para validar a estrutura da indexação.
    """
    print("\n\n🔬 Iniciando a validação da indexação...")
    try:
        collection_info = vector_store.client.get_collection(collection_name=COLLECTION_NAME)
        total_points = collection_info.points_count

        if total_points == 0:
            print("⚠️  A coleção está vazia. Nenhuma validação a ser feita.")
            return

        print(f"ℹ️  Coleção '{COLLECTION_NAME}' contém {total_points} vetores.")
        
        sample_points, _ = vector_store.client.scroll(
            collection_name=COLLECTION_NAME,
            limit=min(sample_size, total_points),
            with_payload=True,
            with_vectors=False
        )

        success_count = 0
        for i, point in enumerate(sample_points):
            print(f"\n--- Amostra {i+1} (ID: {point.id}) ---")
            payload = point.payload
            is_valid = True

            if "text" not in payload or "parent_content" not in payload:
                print("❌ FALHA: Faltam os campos 'text' ou 'parent_content'.")
                is_valid = False
            
            elif payload.get("text") not in payload.get("parent_content", ""):
                print("❌ FALHA: O chunk 'filho' (text) não faz parte do 'pai' (parent_content).")
                is_valid = False

            elif "source" not in payload or "page" not in payload:
                print("❌ FALHA: Faltam os metadados 'source' ou 'page'.")
                is_valid = False
            
            if is_valid:
                success_count += 1
                print(f"✅ SUCESSO: Estrutura 'Small-to-Big' está correta.")
                print(f"   - Fonte: {payload['source']}, Página: {payload['page']}")
                print(f"   - Tamanho do Filho: {len(payload['text'])} chars | Tamanho do Pai: {len(payload['parent_content'])} chars")
            else:
                print("   - Payload com problema:", payload)

        print("\n-------------------------------------------")
        if success_count == len(sample_points):
            print(f"🎉 Validação concluída com sucesso! Todas as {success_count} amostras estão corretas.")
        else:
            print(f"🚨 Validação concluída com erros. {success_count} de {len(sample_points)} amostras estão corretas.")

    except Exception as e:
        print(f"❌ Erro durante a validação: {e}")
        
if __name__ == "__main__":
    delete_articles_collection()
    index_articles()
    validate_indexing()