import asyncio
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.models import Company, FinancialStatement

async def check_data():
    async with AsyncSessionLocal() as session:
        # Check Company
        result = await session.execute(select(Company).where(Company.ticker == "TCS.NS"))
        company = result.scalar_one_or_none()
        
        if not company:
            print("❌ Company TCS.NS NOT FOUND in database.")
            return

        print(f"✅ Found Company: {company.name} ({company.ticker})")
        
        # Check Statements for 2022 and 2023
        result = await session.execute(
            select(FinancialStatement)
            .where(FinancialStatement.company_id == company.id)
            .where(FinancialStatement.fiscal_year.in_([2022, 2023]))
            .order_by(FinancialStatement.fiscal_year)
        )
        statements = result.scalars().all()

        with open("db_status.txt", "w", encoding="utf-8") as f:
            if not statements:
                f.write("❌ No Financial Statements found for 2022/2023.\n")
                return

            f.write(f"✅ Found {len(statements)} statements for 2022/2023:\n")
            for stmt in statements:
                f.write(f"   - FY{stmt.fiscal_year} {stmt.statement_type} ({stmt.period_type})\n")
        print("Done writing to db_status.txt")

if __name__ == "__main__":
    import sys
    # fix for windows loop
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(check_data())
