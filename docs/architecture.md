graph TB
    subgraph "Frontend - React"
        UI[Interface de Usuário React]
    end
    
    subgraph "PhishForge API - Arquitetura RAG"
        subgraph "API Layer"
            Router[API Router]
            Endpoints[Endpoints v1]
        end
        
        subgraph "Core Services - Pipeline RAG"
            DocProc[Document Processor<br/>Processador de Documentos]
            Embed[Embedding Service<br/>Gerador de Embeddings<br/>OpenAI/Sentence Transformers]
            Ret[Retriever<br/>Recuperador de Documentos]
            Rerank[Reranker<br/>Reordenação de Resultados]
            Gen[Response Generator<br/>Gerador de Respostas]
            PromptNorm[Prompt Normalizer<br/>Normalização de Prompts]
        end
        
        subgraph "Domain Layer"
            PhishService[Phishing Service]
            EvalService[Evaluation Service]
            Models[Domain Models]
        end
        
        subgraph "Infrastructure Layer"
            Qdrant[(Qdrant<br/>Vector Store)]
            Postgres[(PostgreSQL<br/>Database)]
            Repos[Repositories<br/>Analytics, Evaluation, Phishing]
        end
    end
    
    %% Fluxo Principal
    UI -->|HTTP Request| Router
    Router --> Endpoints
    Endpoints --> PhishService
    
    %% Pipeline RAG
    PhishService --> DocProc
    DocProc --> Embed
    Embed --> Qdrant
    PhishService --> Ret
    Ret --> Qdrant
    Ret --> Rerank
    Rerank --> Gen
    PromptNorm --> Gen
    
    %% Persistência
    PhishService --> Repos
    EvalService --> Repos
    Repos --> Postgres
    
    %% Response
    Gen -->|Phishing Example| PhishService
    PhishService -->|JSON Response| Endpoints
    Endpoints -->|HTTP Response| UI
    
    %% Estilos
    classDef frontend fill:#61dafb,stroke:#333,stroke-width:2px,color:#000
    classDef api fill:#00d084,stroke:#333,stroke-width:2px
    classDef service fill:#ff6b6b,stroke:#333,stroke-width:2px
    classDef infra fill:#4ecdc4,stroke:#333,stroke-width:2px
    classDef storage fill:#ffe66d,stroke:#333,stroke-width:2px
    
    class UI frontend
    class Router,Endpoints api
    class DocProc,Embed,Ret,Rerank,Gen,PromptNorm,PhishService,EvalService service
    class Repos infra
    class Qdrant,Postgres storage

## Pipeline de Processamento de Documentos

```mermaid
flowchart TB
    subgraph "1. Extração de Conteúdo"
        PDF[("📄 Documento PDF<br/>Corpus de Segurança")]
        Extract[Extração Automática<br/>de Conteúdo]
        Meta[Preservação de<br/>Metadados de Página]
    end
    
    subgraph "2. Segmentação Semântica - Chunking"
        Chunk[Fragmentação do Texto]
        Config["⚙️ Configuração<br/>• 1024 tokens por fragmento<br/>• 256 tokens de sobreposição"]
        Overlap[Sobreposição Semântica<br/>Continuidade entre Segmentos]
    end
    
    subgraph "3. Enriquecimento de Metadados"
        Enrich[Enriquecimento<br/>dos Fragmentos]
        MetaFields["📋 Metadados Descritivos<br/>• Fonte do documento<br/>• Número da página<br/>• Identificador único UUID"]
    end
    
    subgraph "4. Estruturação JSON"
        JSON["🔧 Estrutura do Fragmento"]
        ChildText["child_text<br/>Fragmento indexado"]
        ParentText["parent_text<br/>Contexto completo da página"]
        Metadata["metadata<br/>Informações bibliográficas"]
    end
    
    subgraph "5. Geração de Embeddings"
        EmbedService[Embedding Service<br/>OpenAI ou Sentence Transformers]
        Vectors["🔢 Vetores de<br/>Embedding"]
    end
    
    subgraph "6. Armazenamento Vetorial"
        Qdrant[("🗄️ Qdrant<br/>Vector Database")]
        Search[Busca Semântica<br/>Eficiente]
    end
    
    %% Fluxo Principal
    PDF --> Extract
    Extract --> Meta
    Meta --> Chunk
    Config -.-> Chunk
    Chunk --> Overlap
    Overlap --> Enrich
    MetaFields -.-> Enrich
    Enrich --> JSON
    JSON --> ChildText
    JSON --> ParentText
    JSON --> Metadata
    ChildText --> EmbedService
    ParentText --> EmbedService
    Metadata --> EmbedService
    EmbedService --> Vectors
    Vectors --> Qdrant
    Qdrant --> Search
    
    %% Estilos
    classDef input fill:#a8e6cf,stroke:#333,stroke-width:2px
    classDef process fill:#88d8b0,stroke:#333,stroke-width:2px
    classDef config fill:#ffeaa7,stroke:#333,stroke-width:2px
    classDef structure fill:#74b9ff,stroke:#333,stroke-width:2px
    classDef embedding fill:#fd79a8,stroke:#333,stroke-width:2px
    classDef storage fill:#fdcb6e,stroke:#333,stroke-width:2px
    
    class PDF input
    class Extract,Meta,Chunk,Overlap,Enrich process
    class Config,MetaFields config
    class JSON,ChildText,ParentText,Metadata structure
    class EmbedService,Vectors embedding
    class Qdrant,Search storage
```

## Sistema de Recuperação e Re-ranking

```mermaid
flowchart TB
    subgraph "1. Query do Usuário"
        Query["🔍 Query Original"]
        HyDE["HyDE Transformation<br/>Hypothetical Document Embedding"]
        QueryEmbed["Embedding da Query<br/>Transformada"]
    end
    
    subgraph "2. Busca por Similaridade"
        Qdrant[("🗄️ Qdrant<br/>Vector Database")]
        CosSim["Distância Cosseno<br/>Similaridade Semântica"]
        Candidates["📄 20 Documentos<br/>Candidatos"]
    end
    
    subgraph "3. Re-ranking - Cross-Encoder"
        CrossEncoder["🔄 Cross-Encoder<br/>ms-marco-MiniLM-L-6-v2"]
        JointAnalysis["Análise Conjunta<br/>Query + Documento"]
        Scoring["Pontuação de<br/>Relevância Refinada"]
    end
    
    subgraph "4. Small-to-Big Retrieval"
        Top3["🏆 Top 3 Documentos<br/>Maior Score"]
        ParentExtract["Extração de<br/>parent_content"]
        SemanticIntegrity["Preservação da<br/>Integridade Semântica"]
    end
    
    subgraph "5. Preparação do Contexto"
        Fusion["🔗 Fusão de<br/>Contextos"]
        Summarization["📝 Sumarização<br/>Otimizada"]
        ContextWindow["Otimização da<br/>Janela de Contexto"]
    end
    
    subgraph "6. Geração Final"
        LLM["🤖 LLM<br/>Modelo de Linguagem"]
        Response["📧 Resposta<br/>Gerada"]
    end
    
    %% Fluxo Principal
    Query --> HyDE
    HyDE --> QueryEmbed
    QueryEmbed --> CosSim
    Qdrant --> CosSim
    CosSim --> Candidates
    
    %% Re-ranking
    Candidates --> CrossEncoder
    Query -.-> JointAnalysis
    CrossEncoder --> JointAnalysis
    JointAnalysis --> Scoring
    
    %% Small-to-Big
    Scoring --> Top3
    Top3 --> ParentExtract
    ParentExtract --> SemanticIntegrity
    
    %% Preparação
    SemanticIntegrity --> Fusion
    Fusion --> Summarization
    Summarization --> ContextWindow
    
    %% Geração
    ContextWindow --> LLM
    Query -.-> LLM
    LLM --> Response
    
    %% Estilos
    classDef query fill:#e8daef,stroke:#333,stroke-width:2px
    classDef search fill:#aed6f1,stroke:#333,stroke-width:2px
    classDef rerank fill:#f9e79f,stroke:#333,stroke-width:2px
    classDef retrieval fill:#a9dfbf,stroke:#333,stroke-width:2px
    classDef context fill:#f5b7b1,stroke:#333,stroke-width:2px
    classDef generation fill:#d5dbdb,stroke:#333,stroke-width:2px
    classDef storage fill:#fdcb6e,stroke:#333,stroke-width:2px
    
    class Query,HyDE,QueryEmbed query
    class CosSim,Candidates search
    class CrossEncoder,JointAnalysis,Scoring rerank
    class Top3,ParentExtract,SemanticIntegrity retrieval
    class Fusion,Summarization,ContextWindow context
    class LLM,Response generation
    class Qdrant storage
```

## Corpus de Documentos - Base de Conhecimento

| # | Arquivo | Título/Descrição | Tipo |
|---|---------|------------------|------|
| 1 | 1705.09819v1.pdf | Artigo Científico arXiv (1705.09819) | Artigo Acadêmico |
| 2 | Counterintelligence_Tips_Spearphishing.pdf | Counterintelligence Tips: Spearphishing | Guia Técnico |
| 3 | Gamification_Techniques_for_Raising_Cyber_Security.pdf | Gamification Techniques for Raising Cyber Security Awareness | Artigo Acadêmico |
| 4 | Integrating-self-efficacy-into-a-gamified-approach.pdf | Integrating Self-Efficacy into a Gamified Approach | Artigo Acadêmico |
| 5 | L-G-0000568657-0002356793.pdf | Documento Técnico (L-G-0000568657) | Documento Técnico |
| 6 | Phishing-Attacks-Guide.pdf | Phishing Attacks Guide | Guia Técnico |
| 7 | Phishing.pdf | Phishing - Documento Geral | Material Educativo |
| 8 | Ratcliff IT - Top 10 types of phishing scams eBook.pdf | Top 10 Types of Phishing Scams eBook | eBook |
| 9 | Teaching_Phishing-Security_Which_Way_is_Best.pdf | Teaching Phishing Security: Which Way is Best? | Artigo Acadêmico |
| 10 | VWCardoso.pdf | Trabalho Acadêmico - VW Cardoso | Trabalho Acadêmico |
| 11 | apwg_trends_report_q1_2025.pdf | APWG Phishing Trends Report Q1 2025 | Relatório Estatístico |
| 12 | chi2019_whathack.pdf | CHI 2019 - What Hack | Artigo Acadêmico |
| 13 | eg-guide-on-phishing.pdf | EG Guide on Phishing | Guia Técnico |
| 14 | phishing-awareness-ppt.pdf | Phishing Awareness Presentation | Apresentação |
