from __future__ import annotations
from typing import List, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
import logging

from app.ingestion.data_fetchers import YahooFinanceFetcher
from app.ingestion.data_normalizer import DataNormalizer, StandardizedFinancials, LineItem
from app.ingestion.ratio_calculator import RatioCalculator
from app.ingestion.data_validator import DataValidator
from datetime import datetime
from app.models.models import Company, FinancialStatement, FinancialLineItem
from app.core.vector_store import vector_store

logger = logging.getLogger(__name__)

class IngestionService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.fetcher = YahooFinanceFetcher()
        self.normalizer = DataNormalizer()
        self.ratio_calculator = RatioCalculator()
        self.validator = DataValidator()

    async def ingest_company(self, ticker: str):
        """Full ingestion pipeline for a company"""
        
        # 1. Fetch Data
        raw_data = await self.fetcher.fetch_financials(ticker)
        info = raw_data.get("info", {})
        
        # 2. Normalize Data
        financials_list = self.normalizer.normalize(raw_data)
        
        if not financials_list:
            return {"status": "error", "message": "No financial data found"}
        
        # 2.5. Validate Data Quality (non-blocking)
        try:
            validation_result = self.validator.validate_company_data(ticker, financials_list)
            logger.info(f"Validation for {ticker}: {validation_result['valid_statements']}/{validation_result['total_statements']} valid")
            if validation_result.get('warnings'):
                logger.warning(f"Data quality warnings for {ticker}: {validation_result['warnings']}")
        except Exception as e:
            logger.error(f"Validation error (non-blocking): {e}")
            validation_result = None

        # 3. Store in PostgreSQL
        company = await self._ingest_company_metadata(ticker, info)
        
        chunks_to_embed = []
        metadatas_to_embed = []
        calculated_ratios_count = 0

        # Group statements by period for ratio calculation
        statements_by_period = {}
        for fin in financials_list:
            key = (fin.fiscal_year, fin.period_type, fin.period_date)
            if key not in statements_by_period:
                statements_by_period[key] = []
            statements_by_period[key].append(fin)
        
        for fin in financials_list:
            # Store Statement
            statement = await self._ingest_statement(company.id, fin)
            
            # Store Line Items (original data)
            await self._ingest_line_items(statement.id, fin.line_items)
            
            # 3.5. Calculate and store financial ratios (if we have enough data for this period)
            try:
                period_key = (fin.fiscal_year, fin.period_type, fin.period_date)
                period_statements = statements_by_period.get(period_key, [])
                
                if len(period_statements) >= 2:  # Need at least 2 statement types for ratios
                    calculated_ratios = self.ratio_calculator.calculate_ratios(period_statements)
                    
                    if calculated_ratios:
                        # Store ratios as additional line items
                        await self._ingest_line_items(statement.id, calculated_ratios)
                        calculated_ratios_count += len(calculated_ratios)
                        logger.info(f"Calculated {len(calculated_ratios)} ratios for {fin.statement_type} {fin.period_date}")
            except Exception as e:
                logger.error(f"Error calculating ratios (non-blocking): {e}")
            
            # 4. Prepare Vector Chunks
            # Create a chunk for each line item containing context
            for item in fin.line_items:
                # Text: "Company: TCS\nPeriod: 2023-03-31\n... Value: ..."
                text = (
                    f"Company: {company.name} ({ticker})\n"
                    f"Period: {fin.period_date.strftime('%Y-%m-%d')} ({fin.period_type})\n"
                    f"Statement: {fin.statement_type}\n"
                    f"Line Item: {item.name}\n"
                    f"Value: {item.value:,.2f}"
                )
                
                metadata = {
                    "company_id": company.id,
                    "ticker": ticker,
                    "statement_type": fin.statement_type,
                    "period_type": fin.period_type,
                    "period_date": fin.period_date.isoformat(),
                    "line_item": item.name,
                    "numeric_value": float(item.value)
                }
                
                chunks_to_embed.append(text)
                metadatas_to_embed.append(metadata)

        # 5. Store in Vector DB
        if chunks_to_embed:
            await vector_store.add_texts(chunks_to_embed, metadatas_to_embed)

        return {
            "status": "success", 
            "company": company.name, 
            "statements": len(financials_list),
            "chunks": len(chunks_to_embed),
            "calculated_ratios": calculated_ratios_count,
            "validation": validation_result
        }

    async def _ingest_company_metadata(self, ticker: str, info: Dict) -> Company:
        stmt = insert(Company).values(
            ticker=ticker,
            name=info.get("longName", ticker),
            sector=info.get("sector"),
            industry=info.get("industry")
        ).on_conflict_do_update(
            index_elements=['ticker'],
            set_={
                "name": info.get("longName", ticker),
                "sector": info.get("sector"),
                "industry": info.get("industry"),
                "updated_at":  datetime.utcnow()
            }
        ).returning(Company)
        
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def _ingest_statement(self, company_id: int, fin: StandardizedFinancials) -> FinancialStatement:
        # Check existence first or use simple upsert logic
        # For statement, uniqueness is (company_id, statement_type, period_type, period_date)
        
        stmt = insert(FinancialStatement).values(
            company_id=company_id,
            statement_type=fin.statement_type,
            period_type=fin.period_type,
            period_date=fin.period_date,
            fiscal_year=fin.fiscal_year,
            fiscal_quarter=fin.fiscal_quarter,
            source="yfinance",
            raw_data=fin.raw_data
        ).on_conflict_do_update(
            constraint='uq_company_statement_period',
            set_={"updated_at": datetime.utcnow()}
        ).returning(FinancialStatement)
        
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def _ingest_line_items(self, statement_id: int, items: List[LineItem]):
        if not items:
            return
            
        # Bulk insert/upsert line items
        values = [
            {
                "statement_id": statement_id,
                "line_item_name": item.name,
                "line_item_value": item.value,
                "currency": "INR" # Defaulting to INR for now, ideally fetch from info
            }
            for item in items
        ]
        
        stmt = insert(FinancialLineItem).values(values)
        stmt = stmt.on_conflict_do_update(
            constraint='uq_statement_line_item',
            set_={"line_item_value": stmt.excluded.line_item_value}
        )
        
        await self.db.execute(stmt)

