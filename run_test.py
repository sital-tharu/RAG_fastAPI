import sys
import asyncio
import uvicorn
import traceback

async def start_server():
    config = uvicorn.Config("app.main:app", host="127.0.0.1", port=8003, reload=False)
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    if sys.platform == "win32":
        print("Setting Selector policy...")
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    try:
        asyncio.run(start_server())
    except Exception:
        traceback.print_exc()
