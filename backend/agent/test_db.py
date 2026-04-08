import asyncio
import sys
from psycopg import AsyncConnection

async def test():
    # Get this URL from Supabase Dashboard → "Session pooler" option
    session_pooler_url = "postgresql://postgres.ukyrttzhkdmoienbvawh:Mani%40975464@aws-1-ap-northeast-1.pooler.supabase.com:5432/postgres"

    try:
        conn = await AsyncConnection.connect(session_pooler_url, autocommit=True)
        result = await conn.execute("SELECT 1 AS ping")
        row = await result.fetchone()
        print("✅ Session Pooler Connected!")
        print(row)
        await conn.close()
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

asyncio.run(test())