import os
import re
import traceback
import unicodedata

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, UnstructuredWordDocumentLoader

from app.core.config import settings


class DocumentProcessor:
    def __init__(self, chunk_size=settings.CHUNK_SIZE, chunk_overlap=settings.CHUNK_OVERLAP):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def process_document_data(self, document_data):
        """
        Processa o texto de um documento (PDF ou DOCX) e divide em chunks.

        :param document_data: Texto do documento
        :return: Lista de chunks
        """
        chunks = []
        try:
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size, chunk_overlap=self.chunk_overlap
            )

            chunks = splitter.split_text(document_data)

        except Exception as e:
            print(f"Erro ao processar documento: {e}")
            print(traceback.format_exc())

        return chunks

    def preprocess_file_rag(self, file_path):
        ext = os.path.splitext(file_path)[1].lower()
        try:
            if ext == '.pdf':
                loader = PyPDFLoader(file_path)
            elif ext == '.docx':
                loader = UnstructuredWordDocumentLoader(file_path)
            else:
                raise ValueError(f"Formato de arquivo {ext} não suportado.")

            documents = loader.load()
            text = " ".join(doc.page_content for doc in documents)

            text = self.preprocess_text(text)
            return text

        except Exception as e:
            print(f"Erro ao processar o arquivo {file_path}: {str(e)}")
            raise

    @staticmethod
    def preprocess_text(text):
        text = text.lower()
        text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')
        text = re.sub(r'[^\w\s.,!?]', ' ', text)
        text = " ".join(text.split())

        return text

