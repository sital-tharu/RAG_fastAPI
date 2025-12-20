
import asyncio
import sys
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.models.models import Company, FinancialStatement, FinancialLineItem

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def main():
    settings = get_settings()
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        stmt = select(Company)
        result = await session.execute(stmt)
        companies = result.scalars().all()
        
        if not companies:
            print("No companies found in the database.")
            return

        print(f"Found {len(companies)} companies in total.")

        for company in companies:
            print(f"Found Company: {company.name} (ID: {company.id}, Ticker: {company.ticker})")
            
            # 2. Check Financial Statements
            stmt = select(FinancialStatement).where(FinancialStatement.company_id == company.id).order_by(FinancialStatement.period_date.desc())
            result = await session.execute(stmt)
            statements = result.scalars().all()
            
            print(f"Found {len(statements)} statements.")
            
            for stmt in statements:
                print(f"  Statement ID: {stmt.id}, Type: {stmt.statement_type}, Period: {stmt.period_date} ({stmt.period_type})")
                
                # 3. Check specific Line Items for the latest statement
                stmt_items = select(FinancialLineItem).where(FinancialLineItem.statement_id == stmt.id)
                result_items = await session.execute(stmt_items)
                items = result_items.scalars().all()
                
                # Check for "Operating Margin" or similar
                op_margin = [i for i in items if "margin" in i.line_item_name.lower() or "operating" in i.line_item_name.lower()]
                
                print(f"    Total Line Items: {len(items)}")
                if op_margin:
                    print("    Matching Line Items (Margin/Operating):")
                    for item in op_margin:
                        print(f"      - {item.line_item_name}: {item.line_item_value}")
                else:
                    print("    No line items matched 'margin' or 'operating'")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
