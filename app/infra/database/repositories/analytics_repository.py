import json
from typing import Optional, Dict, Any
from uuid import UUID

from app.infra.database.connection import DatabaseConnection


class AnalyticsRepository:
    def __init__(self, db: DatabaseConnection):
        self.db = db

    async def create_analytics(
        self,
        email_id: UUID,
        word_count: int,
        suspicious_keywords_count: int,
        analysis_metadata: Dict[str, Any]
    ) -> UUID:
        """Cria análise para um email de phishing"""
        async with self.db.get_connection() as conn:
            query = """
                INSERT INTO phishing_analytics 
                (email_id, word_count, suspicious_keywords_count, analysis_metadata)
                VALUES ($1, $2, $3, $4)
                RETURNING id
            """
            return await conn.fetchval(
                query,
                email_id,
                word_count,
                suspicious_keywords_count,
                json.dumps(analysis_metadata)
            )

    async def get_analytics_by_email_id(self, email_id: UUID) -> Optional[Dict]:
        """Busca análise de um email específico"""
        async with self.db.get_connection() as conn:
            query = """
                SELECT id, email_id, word_count, suspicious_keywords_count, 
                       analysis_metadata, created_at
                FROM phishing_analytics 
                WHERE email_id = $1
            """
            row = await conn.fetchrow(query, email_id)
            if not row:
                return None
            return {
                "id": row["id"],
                "email_id": row["email_id"],
                "word_count": row["word_count"],
                "suspicious_keywords_count": row["suspicious_keywords_count"],
                "analysis_metadata": json.loads(row["analysis_metadata"]) if row["analysis_metadata"] else {},
                "created_at": row["created_at"],
            }

    async def get_aggregated_analytics(self) -> Dict:
        """Retorna analytics agregados do sistema"""
        async with self.db.get_connection() as conn:
            query = """
                SELECT 
                    AVG(word_count) as avg_word_count,
                    AVG(suspicious_keywords_count) as avg_suspicious_keywords,
                    MIN(word_count) as min_word_count,
                    MAX(word_count) as max_word_count,
                    COUNT(*) as total_analyzed
                FROM phishing_analytics
            """
            row = await conn.fetchrow(query)
            return {
                "avg_word_count": float(row["avg_word_count"]) if row["avg_word_count"] else 0,
                "avg_suspicious_keywords": float(row["avg_suspicious_keywords"]) if row["avg_suspicious_keywords"] else 0,
                "min_word_count": row["min_word_count"] or 0,
                "max_word_count": row["max_word_count"] or 0,
                "total_analyzed": row["total_analyzed"] or 0,
            }
