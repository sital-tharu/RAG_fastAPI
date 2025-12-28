from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from app.models.models import Company, FinancialStatement, FinancialLineItem
import re
import logging

logger = logging.getLogger(__name__)


class SQLRetriever:
    def __init__(self, db: AsyncSession):
        self.db = db
        
        # Financial terminology mappings for better keyword matching
        self.financial_term_mappings = {
            # Revenue synonyms
            "revenue": ["revenue", "sales", "turnover", "income", "earnings"],
            "profit": ["profit", "income", "earnings", "pbt", "pat"],
            "margin": ["margin"],
            "assets": ["assets", "asset"],
            "liabilities": ["liabilities", "liability", "debt"],
            "equity": ["equity", "stockholders", "shareholders"],
            "capex": ["capital expenditure", "capex", "capital spending"],
            "cash": ["cash", "cash flow"],
            "ebitda": ["ebitda", "operating income", "operating profit"],
            "roe": ["return on equity", "roe"],
            "roa": ["return on assets", "roa"],
            "ratio": ["ratio", "current ratio", "debt"],
        }
    
    def extract_financial_keywords(self, query_text: str) -> List[str]:
        """
        Extract relevant financial keywords from query text.
        Maps common financial terms to their database equivalents.
        
        Args:
            query_text: Natural language query
            
        Returns:
            List of keywords to search for in database
        """
        query_lower = query_text.lower()
        keywords = []
        
        # Check for mapped financial terms
        for term, synonyms in self.financial_term_mappings.items():
            if term in query_lower:
                keywords.extend(synonyms)
        
        # Also extract simple keywords (longer than 3 chars, not common words)
        stop_words = {"what", "when", "where", "which", "who", "how", "the", "is", 
                     "are", "was", "were", "for", "and", "or", "but", "from", "with"}
        
        words = re.findall(r'\b\w+\b', query_lower)
        for word in words:
            if len(word) > 3 and word not in stop_words and word not in keywords:
                keywords.append(word)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_keywords = []
        for kw in keywords:
            if kw not in seen:
                seen.add(kw)
                unique_keywords.append(kw)
        
        logger.debug(f"Extracted keywords from '{query_text}': {unique_keywords}")
        return unique_keywords

    async def retrieve_financial_data(self, ticker: str, query_text: str, limit: int = 200) -> List[Dict]:
        """
        Retrieve financial data from PostgreSQL based on ticker and query context.
        Uses improved keyword extraction with financial term mappings.
        
        Args:
            ticker: Company ticker symbol
            query_text: Natural language query
            limit: Maximum number of results
            
        Returns:
            List of matching financial line items
        """
        
        # 1. Get Company ID
        company_stmt = select(Company).where(Company.ticker == ticker)
        result = await self.db.execute(company_stmt)
        company = result.scalar_one_or_none()
        
        if not company:
            logger.warning(f"Company not found: {ticker}")
            return []

        # 2. Extract keywords using improved method
        keywords = self.extract_financial_keywords(query_text)
        
        if not keywords:
            logger.warning(f"No keywords extracted from query: {query_text}")
            return []

        # 3. Extract Year from query (e.g., "2022", "FY24", "FY 2023")
        target_year = None
        
        # Match "FY22", "FY 22", "FY2022", "FY 2022"
        fy_match = re.search(r'fy\s*(\d{2,4})', query_text, re.IGNORECASE)
        if fy_match:
            year_str = fy_match.group(1)
            target_year = int("20" + year_str) if len(year_str) == 2 else int(year_str)
        
        # Match full year "2022", "2023"
        if not target_year:
            full_year_match = re.search(r'\b(20\d{2})\b', query_text)
            if full_year_match:
                target_year = int(full_year_match.group(1))
        
        if target_year:
            logger.debug(f"Extracted fiscal year from query: {target_year}")

        # 4. Build dynamic OR clause for line items
        conditions = [FinancialLineItem.line_item_name.ilike(f"%{kw}%") for kw in keywords]
        
        # 5. Base query
        base_query = (
            select(
                FinancialLineItem.line_item_name,
                FinancialLineItem.line_item_value,
                FinancialStatement.period_type,
                FinancialStatement.fiscal_year,
                FinancialStatement.fiscal_quarter,
                FinancialStatement.statement_type,
                FinancialStatement.period_date
            )
            .join(FinancialStatement, FinancialLineItem.statement_id == FinancialStatement.id)
            .where(
                and_(
                    FinancialStatement.company_id == company.id,
                    or_(*conditions)
                )
            )
        )

        # 6. Apply Year Filter if detected
        if target_year:
            base_query = base_query.where(FinancialStatement.fiscal_year == target_year)
        
        # 7. Order by most recent first, limit results
        stmt = base_query.order_by(FinancialStatement.period_date.desc()).limit(limit)
        
        results = await self.db.execute(stmt)
        
        # 8. Format results
        data = []
        for row in results:
            data.append({
                "source": "sql",
                "line_item": row.line_item_name,
                "value": float(row.line_item_value),
                "period": f"FY{row.fiscal_year} (Annual)" if row.period_type == "annual" else (
                    f"FY{row.fiscal_year} Q{row.fiscal_quarter}" if row.fiscal_quarter else f"FY{row.fiscal_year}"
                ),
                "statement": row.statement_type
            })
        
        logger.info(f"Retrieved {len(data)} financial records for {ticker}")
        return data
