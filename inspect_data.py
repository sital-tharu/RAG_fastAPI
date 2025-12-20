
import asyncio
import sys
# Set policy for Windows
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from sqlalchemy import select, and_
from app.core.database import AsyncSessionLocal
from app.models.models import FinancialStatement, Company, FinancialLineItem

async def main():
    async with AsyncSessionLocal() as session:
        print("\n=== Line Item Check (RELIANCE.NS 2022) ===")
        
        # Find 2022 Annual Statement ID first
        stmt = select(FinancialStatement).join(Company).where(
            and_(
                Company.ticker == "RELIANCE.NS",
                FinancialStatement.fiscal_year == 2022,
                FinancialStatement.period_type == "annual",
                FinancialStatement.statement_type == "income_statement"
            )
        )
        result = await session.execute(stmt)
        statement = result.scalar_one_or_none()
        
        if not statement:
            print("No Annual Income Statement for 2022 found!")
            return
            
        print(f"Statement ID: {statement.id} | Date: {statement.period_date} | Fiscal Year: {statement.fiscal_year}")
        
        # Get line items matching "Revenue"
        li_stmt = select(FinancialLineItem).where(
            and_(
                FinancialLineItem.statement_id == statement.id,
                FinancialLineItem.line_item_name.ilike("%Revenue%")
            )
        )
        li_result = await session.execute(li_stmt)
        items = li_result.scalars().all()
        
        if not items:
            print("No 'Revenue' items found!")
        
        for item in items:
            print(f"- {item.line_item_name}: {item.line_item_value}")

if __name__ == "__main__":
    asyncio.run(main())
