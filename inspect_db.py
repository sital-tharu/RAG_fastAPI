
import psycopg
import os
from dotenv import load_dotenv

load_dotenv()

db_url = os.getenv("DATABASE_URL").replace("+psycopg", "")
print(f"Connecting to DB with {db_url.split('@')[1] if '@' in db_url else '...'}")

try:
    conn = psycopg.connect(db_url)
    cur = conn.cursor()
    
    # Check if company exists
    cur.execute("SELECT id, ticker, name FROM companies WHERE ticker = 'INFY.NS'")
    company = cur.fetchone()
    
    if not company:
        print("❌ Company 'INFY.NS' NOT found in 'companies' table!")
    else:
        print(f"✅ Found Company: {company}")
        comp_id = company[0]
        
        # Count matches
        cur.execute(f"""
            SELECT COUNT(*)
            FROM financial_statements fs
            JOIN financial_line_items fli ON fs.id = fli.statement_id
            WHERE fs.company_id = {comp_id} AND fli.line_item_name ILIKE '%Revenue%'
        """)
        count = cur.fetchone()[0]
        print(f"✅ Total items matching '%Revenue%': {count}")
        
        # Check if Total Revenue would be cut off by limit 100 (sorted alphabetically)
        cur.execute(f"""
            SELECT fli.line_item_name
            FROM financial_statements fs
            JOIN financial_line_items fli ON fs.id = fli.statement_id
            WHERE fs.company_id = {comp_id} AND fli.line_item_name ILIKE '%Revenue%'
            ORDER BY fs.fiscal_year DESC, fli.line_item_name
            LIMIT 150
        """)
        rows = cur.fetchall()
        print(f"✅ First 150 matches (limit is 100 in code):")
        for i, row in enumerate(rows):
            if "Total Revenue" in row[0]:
                print(f"   [{i}] {row[0]} <--- FOUND HERE")
            else:
                pass # print(f"   [{i}] {row[0]}")

    conn.close()

except Exception as e:
    print(f"Database error: {e}")
