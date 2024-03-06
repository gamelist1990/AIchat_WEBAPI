from sydney import SydneyClient
import asyncio

async def main():
 async with SydneyClient() as sydney:
    response = await sydney.ask("HELLO?", citations=True)
    print(response)
if __name__ == "__main__":
    asyncio.run(main())