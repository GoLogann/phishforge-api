-- V20251106120000__ragas_evaluation_tables.sql
-- Migration para tabelas de avaliação RAGAS

-- Tabela principal para armazenar sessions de avaliação
CREATE TABLE evaluation_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_name VARCHAR(255),
    description TEXT,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed')),
    started_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMPTZ,
    total_evaluations INTEGER DEFAULT 0,
    successful_evaluations INTEGER DEFAULT 0,
    failed_evaluations INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE evaluation_sessions IS 'Sessões de avaliação que agrupam múltiplas avaliações RAGAS.';
COMMENT ON COLUMN evaluation_sessions.session_name IS 'Nome identificador da sessão de avaliação.';
COMMENT ON COLUMN evaluation_sessions.status IS 'Status da sessão (pending, running, completed, failed).';
COMMENT ON COLUMN evaluation_sessions.total_evaluations IS 'Total de avaliações planejadas para a sessão.';
COMMENT ON COLUMN evaluation_sessions.successful_evaluations IS 'Número de avaliações concluídas com sucesso.';
COMMENT ON COLUMN evaluation_sessions.failed_evaluations IS 'Número de avaliações que falharam.';

-- Tabela principal para avaliações RAGAS
CREATE TABLE ragas_evaluations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES evaluation_sessions(id) ON DELETE CASCADE,
    email_id UUID NOT NULL REFERENCES phishing_emails(id) ON DELETE CASCADE,
    user_context TEXT NOT NULL,
    search_query TEXT NOT NULL,
    generation_context TEXT NOT NULL,
    difficulty VARCHAR(20) NOT NULL,
    hyde_context TEXT,
    fused_context TEXT,
    expanded_answer_pt TEXT,
    full_answer_pt TEXT,
    expanded_answer_en TEXT,
    full_answer_en TEXT,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed')),
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE ragas_evaluations IS 'Dados de entrada e saída para avaliações RAGAS de emails de phishing.';
COMMENT ON COLUMN ragas_evaluations.session_id IS 'ID da sessão de avaliação (opcional para avaliações individuais).';
COMMENT ON COLUMN ragas_evaluations.email_id IS 'ID do email de phishing que foi avaliado.';
COMMENT ON COLUMN ragas_evaluations.user_context IS 'Contexto original fornecido pelo usuário.';
COMMENT ON COLUMN ragas_evaluations.search_query IS 'Query de busca normalizada.';
COMMENT ON COLUMN ragas_evaluations.generation_context IS 'Contexto de geração normalizado.';
COMMENT ON COLUMN ragas_evaluations.difficulty IS 'Nível de dificuldade solicitado.';
COMMENT ON COLUMN ragas_evaluations.hyde_context IS 'Contexto hipotético gerado pelo HyDE.';
COMMENT ON COLUMN ragas_evaluations.fused_context IS 'Contexto final fusionado dos documentos relevantes.';
COMMENT ON COLUMN ragas_evaluations.expanded_answer_pt IS 'Resposta expandida em português.';
COMMENT ON COLUMN ragas_evaluations.full_answer_pt IS 'Resposta completa em português.';
COMMENT ON COLUMN ragas_evaluations.expanded_answer_en IS 'Resposta expandida traduzida para inglês.';
COMMENT ON COLUMN ragas_evaluations.full_answer_en IS 'Resposta completa traduzida para inglês.';
COMMENT ON COLUMN ragas_evaluations.status IS 'Status da avaliação.';
COMMENT ON COLUMN ragas_evaluations.error_message IS 'Mensagem de erro caso a avaliação falhe.';

-- Tabela para documentos recuperados durante a avaliação
CREATE TABLE evaluation_retrieved_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    evaluation_id UUID NOT NULL REFERENCES ragas_evaluations(id) ON DELETE CASCADE,
    document_order INTEGER NOT NULL,
    document_id VARCHAR(255),
    document_text TEXT NOT NULL,
    parent_content TEXT,
    similarity_score DECIMAL(10, 8),
    rerank_score DECIMAL(10, 8),
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE evaluation_retrieved_documents IS 'Documentos recuperados durante o processo de avaliação.';
COMMENT ON COLUMN evaluation_retrieved_documents.evaluation_id IS 'ID da avaliação à qual o documento pertence.';
COMMENT ON COLUMN evaluation_retrieved_documents.document_order IS 'Ordem do documento na lista de resultados.';
COMMENT ON COLUMN evaluation_retrieved_documents.document_id IS 'ID único do documento no vector store.';
COMMENT ON COLUMN evaluation_retrieved_documents.document_text IS 'Texto do documento recuperado.';
COMMENT ON COLUMN evaluation_retrieved_documents.parent_content IS 'Conteúdo pai do documento (se disponível).';
COMMENT ON COLUMN evaluation_retrieved_documents.similarity_score IS 'Score de similaridade inicial.';
COMMENT ON COLUMN evaluation_retrieved_documents.rerank_score IS 'Score após re-ranking.';
COMMENT ON COLUMN evaluation_retrieved_documents.metadata IS 'Metadados adicionais do documento.';

-- Tabela para métricas RAGAS
CREATE TABLE ragas_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    evaluation_id UUID NOT NULL REFERENCES ragas_evaluations(id) ON DELETE CASCADE,
    metric_name VARCHAR(50) NOT NULL,
    metric_value DECIMAL(10, 8),
    metric_category VARCHAR(30),
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE ragas_metrics IS 'Métricas individuais calculadas pelo RAGAS.';
COMMENT ON COLUMN ragas_metrics.evaluation_id IS 'ID da avaliação que gerou a métrica.';
COMMENT ON COLUMN ragas_metrics.metric_name IS 'Nome da métrica RAGAS (faithfulness, answer_relevancy, etc).';
COMMENT ON COLUMN ragas_metrics.metric_value IS 'Valor numérico da métrica.';
COMMENT ON COLUMN ragas_metrics.metric_category IS 'Categoria da métrica (retrieval, generation, etc).';
COMMENT ON COLUMN ragas_metrics.metadata IS 'Metadados adicionais sobre o cálculo da métrica.';

-- Tabela para resultados agregados por sessão
CREATE TABLE evaluation_session_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES evaluation_sessions(id) ON DELETE CASCADE,
    metric_name VARCHAR(50) NOT NULL,
    avg_value DECIMAL(10, 8),
    min_value DECIMAL(10, 8),
    max_value DECIMAL(10, 8),
    std_deviation DECIMAL(10, 8),
    median_value DECIMAL(10, 8),
    total_samples INTEGER,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (session_id, metric_name)
);

COMMENT ON TABLE evaluation_session_results IS 'Resultados agregados de métricas por sessão de avaliação.';
COMMENT ON COLUMN evaluation_session_results.session_id IS 'ID da sessão de avaliação.';
COMMENT ON COLUMN evaluation_session_results.metric_name IS 'Nome da métrica agregada.';
COMMENT ON COLUMN evaluation_session_results.avg_value IS 'Valor médio da métrica na sessão.';
COMMENT ON COLUMN evaluation_session_results.min_value IS 'Valor mínimo da métrica na sessão.';
COMMENT ON COLUMN evaluation_session_results.max_value IS 'Valor máximo da métrica na sessão.';
COMMENT ON COLUMN evaluation_session_results.std_deviation IS 'Desvio padrão da métrica na sessão.';
COMMENT ON COLUMN evaluation_session_results.median_value IS 'Mediana da métrica na sessão.';
COMMENT ON COLUMN evaluation_session_results.total_samples IS 'Número de amostras usadas no cálculo.';

-- Índices para performance
CREATE INDEX idx_evaluation_sessions_status ON evaluation_sessions USING btree (status);
CREATE INDEX idx_evaluation_sessions_started_at ON evaluation_sessions USING btree (started_at);
CREATE INDEX idx_ragas_evaluations_session ON ragas_evaluations USING btree (session_id);
CREATE INDEX idx_ragas_evaluations_email ON ragas_evaluations USING btree (email_id);
CREATE INDEX idx_ragas_evaluations_status ON ragas_evaluations USING btree (status);
CREATE INDEX idx_ragas_evaluations_difficulty ON ragas_evaluations USING btree (difficulty);
CREATE INDEX idx_ragas_evaluations_created_at ON ragas_evaluations USING btree (created_at);
CREATE INDEX idx_evaluation_retrieved_docs_eval ON evaluation_retrieved_documents USING btree (evaluation_id);
CREATE INDEX idx_evaluation_retrieved_docs_order ON evaluation_retrieved_documents USING btree (evaluation_id, document_order);
CREATE INDEX idx_ragas_metrics_evaluation ON ragas_metrics USING btree (evaluation_id);
CREATE INDEX idx_ragas_metrics_name ON ragas_metrics USING btree (metric_name);
CREATE INDEX idx_ragas_metrics_category ON ragas_metrics USING btree (metric_category);
CREATE INDEX idx_evaluation_session_results_session ON evaluation_session_results USING btree (session_id);
CREATE INDEX idx_evaluation_session_results_metric ON evaluation_session_results USING btree (metric_name);

-- Índices GIN para busca em campos JSON e texto
CREATE INDEX idx_evaluation_retrieved_docs_metadata ON evaluation_retrieved_documents USING gin (metadata);
CREATE INDEX idx_ragas_metrics_metadata ON ragas_metrics USING gin (metadata);
CREATE INDEX idx_ragas_evaluations_search_query ON ragas_evaluations USING gin (to_tsvector('portuguese', search_query));
CREATE INDEX idx_ragas_evaluations_user_context ON ragas_evaluations USING gin (to_tsvector('portuguese', user_context));

-- Triggers para atualizar updated_at automaticamente
CREATE TRIGGER set_timestamp_evaluation_sessions
BEFORE UPDATE ON evaluation_sessions
FOR EACH ROW
EXECUTE PROCEDURE update_updated_at_column();

CREATE TRIGGER set_timestamp_ragas_evaluations
BEFORE UPDATE ON ragas_evaluations
FOR EACH ROW
EXECUTE PROCEDURE update_updated_at_column();

-- Views úteis para análise
CREATE VIEW evaluation_metrics_summary AS
SELECT 
    e.id as evaluation_id,
    e.email_id,
    e.difficulty,
    e.status,
    e.created_at,
    rm.metric_name,
    rm.metric_value,
    rm.metric_category
FROM ragas_evaluations e
LEFT JOIN ragas_metrics rm ON e.id = rm.evaluation_id
WHERE e.status = 'completed';

COMMENT ON VIEW evaluation_metrics_summary IS 'View consolidada com avaliações e suas respectivas métricas.';

CREATE VIEW session_performance_overview AS
SELECT 
    es.id as session_id,
    es.session_name,
    es.status,
    es.started_at,
    es.completed_at,
    es.total_evaluations,
    es.successful_evaluations,
    es.failed_evaluations,
    CASE 
        WHEN es.total_evaluations > 0 
        THEN ROUND((es.successful_evaluations::decimal / es.total_evaluations) * 100, 2)
        ELSE 0 
    END as success_rate_percent,
    EXTRACT(EPOCH FROM (es.completed_at - es.started_at)) as duration_seconds
FROM evaluation_sessions es;

COMMENT ON VIEW session_performance_overview IS 'View com métricas de performance das sessões de avaliação.';