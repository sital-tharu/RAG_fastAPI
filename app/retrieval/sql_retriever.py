from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from app.models.models import Company, FinancialStatement, FinancialLineItem

class SQLRetriever:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def retrieve_financial_data(self, ticker: str, query_text: str, limit: int = 20) -> List[Dict]:
        """
        Retrieve financial data from PostgreSQL based on ticker and query context.
        Note: accurately mapping NL query to specific line items is hard without LLM.
        Here we fetch commonly requested metrics if keywords match, or just recent data.
        
        For this MVP, we will try to fuzzy match line items from the query words.
        """
        
        # 1. Get Company ID
        company_stmt = select(Company).where(Company.ticker == ticker)
        result = await self.db.execute(company_stmt)
        company = result.scalar_one_or_none()
        
        if not company:
            return []

        # 2. Extract potential line item keywords from query
        # This is a naive implementation. In production, use LLM to extract "Revenue" from "How much did they earn?"
        # But per requirements "LLM Usage: Google AI Studio", we could use LLM here too. 
        # For now, let's just search for key terms in the database that match words in the query.
        
        keywords = [word for word in query_text.split() if len(word) > 3]
        
        if not keywords:
            return []

        # Build dynamic OR clause for line items
        conditions = [FinancialLineItem.line_item_name.ilike(f"%{kw}%") for kw in keywords]
        
        stmt = (
            select(
                FinancialLineItem.line_item_name,
                FinancialLineItem.line_item_value,
                FinancialStatement.period_type,
                FinancialStatement.fiscal_year,
                FinancialStatement.fiscal_quarter,
                FinancialStatement.statement_type
            )
            .join(FinancialStatement, FinancialLineItem.statement_id == FinancialStatement.id)
            .where(
                and_(
                    FinancialStatement.company_id == company.id,
                    or_(*conditions)
                )
            )
            .order_by(FinancialStatement.period_date.desc())
            .limit(limit)
        )
        
        results = await self.db.execute(stmt)
        
        data = []
        for row in results:
            data.append({
                "source": "sql",
                "line_item": row.line_item_name,
                "value": float(row.line_item_value),
                "period": f"FY{row.fiscal_year} Q{row.fiscal_quarter}" if row.fiscal_quarter else f"FY{row.fiscal_year}",
                "statement": row.statement_type
            })
            
        return data
