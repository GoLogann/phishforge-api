-- Alinha o vocabulário do campo `nivel` ao usado pela aplicação (facil/medio/dificil).
-- O schema original aceitava (baixo/medio/alto/critico), o que conflitava com o vocabulário
-- enviado pela API e pelo prompt do gerador, causando fallback silencioso para 'medio'.

ALTER TABLE phishing_emails DROP CONSTRAINT phishing_emails_nivel_check;

UPDATE phishing_emails
SET nivel = CASE
    WHEN nivel = 'baixo' THEN 'facil'
    WHEN nivel = 'alto' THEN 'dificil'
    WHEN nivel = 'critico' THEN 'dificil'
    WHEN nivel IN ('facil', 'medio', 'dificil') THEN nivel
    ELSE 'medio'
END;

ALTER TABLE phishing_emails
    ADD CONSTRAINT phishing_emails_nivel_check
    CHECK (nivel IN ('facil', 'medio', 'dificil'));

COMMENT ON COLUMN phishing_emails.nivel IS 'Nível de sofisticação do phishing (facil, medio, dificil).';
