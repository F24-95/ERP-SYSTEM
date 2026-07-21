import sqlite3
import os

# Check SQLite database
db_path = os.path.join(os.path.dirname(__file__), "school_erp.db")
print(f"SQLite DB path: {db_path}")
print(f"SQLite DB exists: {os.path.exists(db_path)}")

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [t[0] for t in cursor.fetchall()]
    print(f"SQLite tables: {tables}")
    if "users" in tables:
        cursor = conn.execute("SELECT count(*) FROM users")
        cnt = cursor.fetchone()[0]
        print(f"Users in SQLite: {cnt}")
        cursor = conn.execute("SELECT email, role FROM users")
        for row in cursor.fetchall():
            print(f"  - {row[0]} ({row[1]})")
    conn.close()

# Now check PostgreSQL via asyncpg
import asyncio
import asyncpg
from dotenv import load_dotenv

load_dotenv()


async def check_pg():
    url = os.getenv("DATABASE_URL")
    print(f"\nDATABASE_URL from .env: {url}")
    try:
        conn = await asyncpg.connect(url)
        rows = await conn.fetch("SELECT email, role FROM users")
        print(f"Users in PostgreSQL: {len(rows)}")
        for r in rows:
            print(f"  - {r['email']} ({r['role']})")
        await conn.close()
    except Exception as e:
        print(f"PostgreSQL error: {e}")


asyncio.run(check_pg())
