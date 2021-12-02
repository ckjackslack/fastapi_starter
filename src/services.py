import os
import time
import aiofiles
from fastapi import UploadFile
from config import MESSAGES_FILEPATH, STATIC_DIR

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
