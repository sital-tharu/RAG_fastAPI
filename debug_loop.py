import sys
import asyncio

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def main():
    loop = asyncio.get_running_loop()
    print(f"Loop: {type(loop)}")

if __name__ == "__main__":
    asyncio.run(main())
