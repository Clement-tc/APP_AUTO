import requests
import time
import numpy as np
import asyncio
import aiohttp
import random

URL = "http://localhost:56190/"  # à adapter si besoin

# Requête asynchrone individuelle
async def send_request(session, idx, delay):
    await asyncio.sleep(delay)
    try:
        async with session.get(URL) as response:
            status = response.status
            print(f"✅ Req {idx}: Status {status} après {delay:.2f}s")
    except Exception as e:
        print(f"❌ Req {idx}: erreur {e}")

# Générateur de tâches avec des délais aléatoires
async def main(n_requests=20, min_delay=0.1, max_delay=5.0):
    delays = np.random.uniform(min_delay, max_delay, size=n_requests)
    async with aiohttp.ClientSession() as session:
        tasks = [
            send_request(session, idx, delay)
            for idx, delay in enumerate(delays)
        ]
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main(n_requests=10_000, min_delay=1, max_delay=160.5))
