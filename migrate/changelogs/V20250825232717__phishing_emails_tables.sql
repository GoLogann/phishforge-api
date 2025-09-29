-- V20250825232717__phishing_emails_tables.sql
-- Migration corrigida com a função update_updated_at_column

-- Primeiro, criamos a função para atualizar updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
   NEW.updated_at = CURRENT_TIMESTAMP;
   RETURN NEW;
END;
$$ LANGUAGE 'plpgsql';

-- Tabela principal de emails de phishing
CREATE TABLE phishing_emails (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    receptor VARCHAR(255) NOT NULL,
    remetente VARCHAR(255) NOT NULL,
    assunto TEXT NOT NULL,
    conteudo TEXT NOT NULL,
    explicacao TEXT NOT NULL,
    nivel VARCHAR(20) NOT NULL CHECK (nivel IN ('baixo', 'medio', 'alto', 'critico')),
    categoria VARCHAR(50) NOT NULL,
    links JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE phishing_emails IS 'Tabela que armazena exemplos de emails de phishing gerados para treinamento e análise.';
COMMENT ON COLUMN phishing_emails.receptor IS 'Email do destinatário do phishing.';
COMMENT ON COLUMN phishing_emails.remetente IS 'Email do remetente (falso) do phishing.';
COMMENT ON COLUMN phishing_emails.assunto IS 'Linha de assunto do email de phishing.';
COMMENT ON COLUMN phishing_emails.conteudo IS 'Corpo completo do email de phishing.';
COMMENT ON COLUMN phishing_emails.explicacao IS 'Explicação sobre as técnicas de phishing utilizadas no exemplo.';
COMMENT ON COLUMN phishing_emails.nivel IS 'Nível de sofisticação do phishing (baixo, medio, alto, critico).';
COMMENT ON COLUMN phishing_emails.categoria IS 'Categoria do phishing (banking, social_media, ecommerce, etc).';
COMMENT ON COLUMN phishing_emails.links IS 'Array JSON com os links maliciosos presentes no email.';

-- Tabela de análises dos emails
CREATE TABLE phishing_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email_id UUID NOT NULL REFERENCES phishing_emails(id) ON DELETE CASCADE,
    word_count INTEGER,
    suspicious_keywords_count INTEGER,
    analysis_metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE phishing_analytics IS 'Tabela que armazena análises e métricas dos emails de phishing.';
COMMENT ON COLUMN phishing_analytics.word_count IS 'Número total de palavras no conteúdo do email.';
COMMENT ON COLUMN phishing_analytics.suspicious_keywords_count IS 'Número de palavras suspeitas identificadas.';
COMMENT ON COLUMN phishing_analytics.analysis_metadata IS 'Metadados adicionais da análise em formato JSON.';

-- Tabela de datasets para treinamento
CREATE TABLE training_datasets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    version VARCHAR(20) DEFAULT '1.0',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE training_datasets IS 'Tabela que armazena conjuntos de dados organizados para treinamento de modelos.';
COMMENT ON COLUMN training_datasets.name IS 'Nome único do dataset de treinamento.';
COMMENT ON COLUMN training_datasets.description IS 'Descrição detalhada do propósito e conteúdo do dataset.';
COMMENT ON COLUMN training_datasets.version IS 'Versão do dataset para controle de mudanças.';
COMMENT ON COLUMN training_datasets.is_active IS 'Indica se o dataset está ativo para uso.';

-- Tabela de relacionamento entre datasets e emails
CREATE TABLE dataset_emails (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dataset_id UUID NOT NULL REFERENCES training_datasets(id) ON DELETE CASCADE,
    email_id UUID NOT NULL REFERENCES phishing_emails(id) ON DELETE CASCADE,
    split_type VARCHAR(20) DEFAULT 'train' CHECK (split_type IN ('train', 'validation', 'test')),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (dataset_id, email_id)
);

COMMENT ON TABLE dataset_emails IS 'Tabela de relacionamento entre datasets e emails de phishing.';
COMMENT ON COLUMN dataset_emails.split_type IS 'Tipo de divisão do dado no dataset (train, validation, test).';

-- Índices para performance
CREATE INDEX idx_phishing_emails_categoria ON phishing_emails USING btree (categoria);
CREATE INDEX idx_phishing_emails_nivel ON phishing_emails USING btree (nivel);
CREATE INDEX idx_phishing_emails_created_at ON phishing_emails USING btree (created_at);
CREATE INDEX idx_phishing_analytics_email ON phishing_analytics USING btree (email_id);
CREATE INDEX idx_training_datasets_name ON training_datasets USING btree (name);
CREATE INDEX idx_dataset_emails_dataset ON dataset_emails USING btree (dataset_id);
CREATE INDEX idx_dataset_emails_split ON dataset_emails USING btree (split_type);

-- Índices GIN para busca em campos JSON e texto
CREATE INDEX idx_phishing_emails_links ON phishing_emails USING gin (links);
CREATE INDEX idx_phishing_analytics_metadata ON phishing_analytics USING gin (analysis_metadata);
CREATE INDEX idx_phishing_emails_content_search ON phishing_emails USING gin (to_tsvector('portuguese', conteudo));
CREATE INDEX idx_phishing_emails_subject_search ON phishing_emails USING gin (to_tsvector('portuguese', assunto));

-- Triggers para atualizar updated_at automaticamente
CREATE TRIGGER set_timestamp_phishing_emails
BEFORE UPDATE ON phishing_emails
FOR EACH ROW
EXECUTE PROCEDURE update_updated_at_column();

CREATE TRIGGER set_timestamp_training_datasets
BEFORE UPDATE ON training_datasets
FOR EACH ROW
EXECUTE PROCEDURE update_updated_at_column();