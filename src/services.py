import os
import time
import aiofiles
import asyncio
import aiohttp
from typing import Optional, Any
from socket import AF_INET
from fastapi import UploadFile
from config import MESSAGES_FILEPATH, STATIC_DIR

class SingletonAioHttp:
    sem: Optional[asyncio.Semaphore] = None
    client: Optional[aiohttp.ClientSession] = None

    @classmethod
    def get_client(cls) -> aiohttp.ClientSession:
        if cls.client is None:
            timeout = aiohttp.ClientTimeout(total = 2)
            connector = aiohttp.TCPConnector(family = AF_INET,
                limit_per_host = 100)
            cls.client = aiohttp.ClientSession(timeout = timeout,
                connector = connector)
        return cls.client

    @classmethod
    async def close_client(cls) -> None:
        if cls.client:
            await cls.client.close()
            cls.client = None

    @classmethod
    async def query_url(cls, url: str) -> Any:
        client = cls.get_client()
        try:
            async with client.get(url) as response:
                if response.status != 200:
                    return {
                        'error': str(await response.text())
                    }
                result = await response.json()
        except Exception as e:
            return {'error': e}
        return result

def write_message(message: str = ''):
    time.sleep(5)
    with open(MESSAGES_FILEPATH, mode = 'a+') as f:
        f.write(f"new message: {message}\n")

async def save_static_file(file: UploadFile):
    async with aiofiles.open(os.path.join(STATIC_DIR,
            file.filename), 'wb') as out_file:
            while True:
                content = await file.read(1024)
                if not content:
                    break
                await out_file.write(content)
