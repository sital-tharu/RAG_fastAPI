import sys
import asyncio
import traceback

# Set policy immediately for Windows compatibility with Psycopg
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import uvicorn

async def main():
    # Configure Uvicorn
    config = uvicorn.Config("app.main:app", host="127.0.0.1", port=8000, reload=False)
    server = uvicorn.Server(config)
    
    print("\n" + "="*50)
    print("🚀 Server is running! Access it here:")
    print("👉 http://localhost:8000")
    print("="*50 + "\n")

    # Run the server in the current asyncio loop (SelectorEventLoop)
    await server.serve()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception:
        traceback.print_exc()
