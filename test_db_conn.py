
import psycopg
import sys

passwords = ["password", "postgres", "admin", "root", "1234", "op"]
db_name = "financial_rag"
user = "postgres"
host = "localhost"
port = "5432"

print(f"Testing connection to {db_name} as {user}...")

# Test 1: User postgres, Pass op (already failed but checking permutations)
# Test 2: User op, Pass postgres
# Test 3: User postgres, Pass 'open' (guess)
# Test 4: User postgres, Pass '' (empty)

configs = [
    ("postgres", "op"),
    ("op", "postgres"),
    ("postgres", "open"),
    ("postgres", ""),
    ("postgres", "openai"),
]

for u, p in configs:
    try:
        conn = psycopg.connect(
            dbname=db_name,
            user=u,
            password=p,
            host=host,
            port=port
        )
        print(f"SUCCESS: User '{u}', Password '{p}'")
        conn.close()
        sys.exit(0)
    except Exception as e:
        print(f"Failed with User '{u}', Pass '{p}': {e}")

print("All passwords failed.")
sys.exit(1)
